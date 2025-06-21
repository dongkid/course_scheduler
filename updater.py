import requests
import re
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Tuple, Optional, Dict, Any, Callable

from constants import VERSION, PROJECT_URL, GITHUB_DOMAIN, VERSION_PATTERN
from logger import logger

import time
import socket

class Updater:
    """处理应用程序更新的类，包括检查、下载和安装。"""

    def __init__(self, parent_window: tk.Tk):
        """
        初始化Updater。
        :param parent_window: 父Tkinter窗口，用于显示对话框。
        """
        self.parent_window = parent_window
        self.progress_window: Optional[tk.Toplevel] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.progress_label: Optional[tk.Label] = None
        self.speed_label: Optional[tk.Label] = None
        self._update_lock = threading.Lock()
        self._current_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _is_newer(self, remote_version: str, local_version: str) -> bool:
        """比较版本号，返回远程版本是否更新。"""
        def parse_version(ver: str) -> tuple:
            match = re.match(VERSION_PATTERN, ver)
            if not match:
                return (0, 0, 0, 'z')  # 无效版本视为最低
            major, minor, patch = map(int, match.groups()[:3])
            pre = match.group(4) or ''
            return (major, minor, patch, pre)

        rv = parse_version(remote_version)
        lv = parse_version(local_version)

        # 比较主版本号、次版本号、修订号
        if rv[:3] > lv[:3]:
            return True
        if rv[:3] < lv[:3]:
            return False

        # 比较预览标识：无预览标识（正式版） > 有预览标识
        if lv[3] and not rv[3]:
            return True   # 本地是预览版，远程是正式版
        if not lv[3] and rv[3]:
            return False  # 本地是正式版，远程是预览版
        
        # 如果两者都是预览版或都是正式版，则按字母顺序比较
        return rv[3] > lv[3]

    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """
        检查GitHub上是否有新版本。
        :return: 如果有新版本，则返回包含版本信息的字典，否则返回None。
        """
        try:
            repo = PROJECT_URL.split(GITHUB_DOMAIN)[-1].rstrip("/")
            api_url = f"https://api.github.com/repos/{repo}/releases/latest"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data.get("tag_name", "").lstrip('v')

            if self._is_newer(latest_version, VERSION):
                return {
                    "version": latest_version,
                    "url": release_data.get("html_url"),
                    "notes": release_data.get("body"),
                    "assets": release_data.get("assets", [])
                }
            return None
        except Exception as e:
            logger.log_error(f"更新检查失败: {str(e)}")
            return None

    def _check_network_connectivity(self, domain="api.github.com", port=443):
        """检查到特定域名的网络连通性。"""
        try:
            socket.create_connection((domain, port), timeout=5)
            logger.log_debug(f"成功连接到 {domain}:{port}")
            return True
        except OSError as e:
            logger.log_warning(f"网络连接失败: {e}")
            return False

    def _create_progress_window(self):
        """创建并显示下载进度窗口。"""
        self.progress_window = tk.Toplevel(self.parent_window)
        self.progress_window.title("正在下载更新")
        self.progress_window.geometry("350x150")
        self.progress_window.transient(self.parent_window)
        self.progress_window.grab_set()
        self.progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用关闭按钮

        self.progress_label = tk.Label(self.progress_window, text="正在准备下载...")
        self.progress_label.pack(pady=10)

        self.progress_bar = ttk.Progressbar(self.progress_window, orient="horizontal", length=320, mode="determinate")
        self.progress_bar.pack(pady=10)

        self.speed_label = tk.Label(self.progress_window, text="")
        self.speed_label.pack(pady=5)

    def _update_progress(self, current_bytes, total_bytes, start_time):
        """更新进度条和标签，包括下载速度和剩余时间。"""
        if not self.progress_window or not self.progress_window.winfo_exists():
            return

        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            speed = current_bytes / elapsed_time
            remaining_bytes = total_bytes - current_bytes
            eta = remaining_bytes / speed if speed > 0 else 0
        else:
            speed = 0
            eta = float('inf')

        percent = (current_bytes / total_bytes) * 100 if total_bytes > 0 else 0
        self.progress_bar['value'] = percent
        self.progress_label.config(text=f"已下载 {current_bytes/1024/1024:.2f} MB / {total_bytes/1024/1024:.2f} MB")
        self.speed_label.config(text=f"速度: {speed/1024:.2f} KB/s | 预计剩余: {eta:.0f} 秒")
        self.progress_window.update_idletasks()

    def _close_progress_window(self):
        """关闭进度窗口。"""
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None

    def _download_update(self, download_url: str, destination_path: str) -> Optional[str]:
        """在单独的线程中下载更新文件。"""
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            start_time = time.time()
            with open(destination_path, 'wb') as f:
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if self._stop_event.is_set():
                        logger.log_info("下载被中断。")
                        return None
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    self.parent_window.after(0, self._update_progress, downloaded_size, total_size, start_time)
            
            return destination_path
        except requests.exceptions.RequestException as e:
            logger.log_error(f"下载失败: {e}")
            self.parent_window.after(0, lambda: messagebox.showerror("下载失败", f"下载更新时出错:\n{e}"))
            return None
        finally:
            self.parent_window.after(0, self._close_progress_window)

    def _install_update(self, downloaded_file_path: str):
        """执行更新安装，处理权限问题。"""
        import subprocess
        import sys
        import os
        import ctypes

        if sys.platform != 'win32':
            messagebox.showinfo("不支持", "自动安装目前仅支持Windows。")
            return

        current_exe = sys.executable
        install_dir = os.path.dirname(current_exe)

        def has_write_permission(directory: str) -> bool:
            test_file = os.path.join(directory, "permission_test.tmp")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                return True
            except (IOError, PermissionError):
                return False

        try:
            bat_path = os.path.join(os.environ['TEMP'], 'update_installer.bat')
            script_content = f'''@echo off
chcp 65001 > nul
echo "正在关闭当前应用程序，请稍候..."
taskkill /f /pid {os.getpid()}
timeout /t 3 /nobreak > nul
echo "正在替换文件..."
move /y "{downloaded_file_path}" "{current_exe}"
echo "正在重启应用程序..."
start "" "{current_exe}"
del "%~f0"
'''
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            if not has_write_permission(install_dir):
                logger.log_warning(f"安装目录 {install_dir} 无写权限，尝试提权。")
                # 使用 ShellExecuteW 以管理员权限运行
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", "cmd.exe", f'/c "{bat_path}"', None, 1
                )
                if ret <= 32:
                    messagebox.showerror("权限错误", "无法获取管理员权限以完成安装。")
            else:
                logger.log_info("安装目录有写权限，正常执行。")
                subprocess.Popen(bat_path, creationflags=subprocess.CREATE_NEW_CONSOLE)

        except Exception as e:
            logger.log_error(f"安装脚本创建失败: {e}")
            messagebox.showerror("安装失败", f"创建安装脚本时出错:\n{e}")

    def run_update_flow(self, silent: bool = False):
        """协调整个更新流程，处理强制中断。"""
        logger.log_info(f"请求启动更新流程 (silent={silent})。")

        if self._update_lock.locked():
            if silent:
                logger.log_info("后台更新已在运行，静默请求被忽略。")
                return
            
            logger.log_warning("更新流程已被锁定，可能正在运行。尝试中断旧流程...")
            if messagebox.askyesno("确认", "另一个更新检查似乎正在进行中。\n是否要中断它并开始新的检查？"):
                self._stop_current_thread()
            else:
                return

        if self._update_lock.acquire(timeout=5):
            try:
                self._stop_event.clear()
                
                if not self._check_network_connectivity():
                    if not silent:
                        messagebox.showerror("网络错误", "无法连接到GitHub更新服务器，请检查您的网络连接。")
                    else:
                        logger.log_info("网络连接不可用，静默更新检查已取消。")
                    return

                latest_release = self.check_for_updates()
                if not latest_release:
                    if not silent:
                        messagebox.showinfo("检查更新", "当前已是最新版本。")
                    return

                asset = next((a for a in latest_release.get("assets", []) if a.get("name", "").endswith(".exe")), None)
                if not asset or not asset.get("browser_download_url"):
                    if not silent:
                        messagebox.showwarning("未找到文件", "找到了新版本，但没有合适的安装文件。")
                    return

                if messagebox.askyesno("发现新版本", f"发现新版本 {latest_release['version']}。\n\n是否立即下载并安装？"):
                    self._create_progress_window()
                    download_dest = os.path.join(os.environ['TEMP'], asset["name"])
                    
                    self._current_thread = threading.Thread(
                        target=self._process_download_and_install,
                        args=(asset["browser_download_url"], download_dest),
                        daemon=True
                    )
                    self._current_thread.start()
            finally:
                self._update_lock.release()
                logger.log_info("更新流程结束，释放锁。")
        else:
            logger.log_error("无法获取更新锁，操作超时。")

    def _process_download_and_install(self, url, dest):
        """下载和安装的处理函数，在线程中运行。"""
        downloaded_path = self._download_update(url, dest)
        if downloaded_path and not self._stop_event.is_set():
            self.parent_window.after(0, lambda: self._install_update(downloaded_path))

    def _stop_current_thread(self):
        """向当前运行的线程发送停止信号。"""
        if self._current_thread and self._current_thread.is_alive():
            logger.log_info(f"正在向线程 {self._current_thread.name} 发送停止信号。")
            self._stop_event.set()
            self.parent_window.after(0, self._close_progress_window)

    def start_background_check(self):
        """
        在后台线程中启动静默更新流程。
        """
        if self._update_lock.locked():
            logger.log_info("后台更新检查请求被忽略，因为更新流程已在运行。")
            return
            
        background_thread = threading.Thread(
            target=lambda: self.run_update_flow(silent=True),
            daemon=True
        )
        background_thread.start()

def main():
    """用于测试的临时入口点"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    updater = Updater(root)
    updater.run_update_flow()
    root.mainloop()

if __name__ == "__main__":
    main()
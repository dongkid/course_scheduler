import requests
import re
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Tuple, Optional, Dict, Any, Callable, List
import os
import math
from queue import Queue

from constants import VERSION, PROJECT_URL, GITHUB_DOMAIN, VERSION_PATTERN
from logger import logger

import time
import socket

# --- Constants for Multi-threaded Download ---
CHUNK_SIZE = 512 * 1024  # 512KB per chunk for fine-grained task queue
MAX_THREADS = 10  # Max number of download threads
DOWNLOAD_RETRY = 2 # Retries for a single chunk

class Updater:
    """处理应用程序更新的类，包括检查、下载和安装。"""

    def __init__(self, parent_window: tk.Tk, config_handler=None):
        """
        初始化Updater。
        :param parent_window: 父Tkinter窗口，用于显示对话框。
        :param config_handler: 配置处理器实例
        """
        self.parent_window = parent_window
        self.config_handler = config_handler
        self.progress_window: Optional[tk.Toplevel] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.progress_label: Optional[tk.Label] = None
        self.speed_label: Optional[tk.Label] = None
        self.cancel_button: Optional[tk.Button] = None
        self._update_lock = threading.Lock()
        self._current_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.max_retries = 3
        self.retry_delay = 5
        
        # --- For multi-threaded download ---
        self.download_threads: List[threading.Thread] = []
        self.task_queue: Optional[Queue] = None
        self.shared_progress: Dict[str, Any] = {
            "lock": threading.Lock(),
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "start_time": 0,
            "error": None,
            "part_paths": []
        }

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
        根据配置决定是否检查预发布版本。
        :return: 如果有新版本，则返回包含版本信息的字典，否则返回None。
        """
        logger.log_debug("开始检查更新...")
        
        # 从配置中获取是否检查预发布版
        check_prerelease = self.config_handler.check_prerelease if self.config_handler else False
        logger.log_debug(f"检查预发布版本: {'是' if check_prerelease else '否'}")

        try:
            repo = PROJECT_URL.split(GITHUB_DOMAIN)[-1].rstrip("/")
            
            if check_prerelease:
                # 检查所有版本
                api_url = f"https://api.github.com/repos/{repo}/releases"
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                releases = response.json()
                if not releases:
                    logger.log_debug("没有找到任何发布。")
                    return None

                latest_release_data = None
                highest_version = "0.0.0"
                for release in releases:
                    if release.get('draft', False):
                        continue
                    tag_name = release.get("tag_name", "").lstrip('v')
                    if self._is_newer(tag_name, highest_version):
                        highest_version = tag_name
                        latest_release_data = release
                
                if not latest_release_data:
                    logger.log_debug("在所有发布中未找到有效版本。")
                    return None
                
                release_data = latest_release_data
            else:
                # 只检查最新的稳定版
                api_url = f"https://api.github.com/repos/{repo}/releases/latest"
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                release_data = response.json()

            latest_version = release_data.get("tag_name", "").lstrip('v')
            logger.log_debug(f"查询到最新版本: {latest_version}，当前版本: {VERSION}")

            if self._is_newer(latest_version, VERSION):
                logger.log_debug(f"发现新版本: {latest_version}")
                return {
                    "version": latest_version,
                    "url": release_data.get("html_url"),
                    "notes": release_data.get("body"),
                    "assets": release_data.get("assets", [])
                }
            logger.log_debug("当前已是最新版本。")
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

    def _configure_styles(self):
        """配置下载窗口的ttk样式。"""
        style = ttk.Style()
        style.configure("Updater.TFrame", background="white")
        style.configure("Updater.TLabel", background="white", font=("Microsoft YaHei", 9))
        style.configure("Updater.TButton", font=("Microsoft YaHei", 9))
        # 为进度条创建一个自定义样式
        style.configure("Updater.Horizontal.TProgressbar", troughcolor='white', background='#0078D7', bordercolor='white', lightcolor='#0078D7', darkcolor='#0078D7')


    def _create_progress_window(self):
        """创建并显示下载进度窗口。"""
        self._configure_styles() # 应用样式

        self.progress_window = tk.Toplevel(self.parent_window)
        self.progress_window.title("正在下载更新")
        self.progress_window.configure(bg="white")

        window_width = 350
        window_height = 180
        screen_width = self.progress_window.winfo_screenwidth()
        screen_height = self.progress_window.winfo_screenheight()
        position_x = (screen_width // 2) - (window_width // 2)
        position_y = (screen_height // 2) - (window_height // 2)
        self.progress_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

        self.progress_window.transient(self.parent_window)
        self.progress_window.grab_set()
        self.progress_window.protocol("WM_DELETE_WINDOW", self._stop_current_thread)

        main_frame = ttk.Frame(self.progress_window, style="Updater.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.progress_label = ttk.Label(main_frame, text="正在准备下载...", style="Updater.TLabel")
        self.progress_label.pack(pady=(0, 5), anchor='w')

        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=320, mode="determinate", style="Updater.Horizontal.TProgressbar")
        self.progress_bar.pack(pady=5, fill=tk.X, expand=True)

        self.speed_label = ttk.Label(main_frame, text="", style="Updater.TLabel")
        self.speed_label.pack(pady=(0, 10), anchor='w')

        self.cancel_button = ttk.Button(main_frame, text="取消", command=self._stop_current_thread, style="Updater.TButton")
        self.cancel_button.pack(side=tk.RIGHT)
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
        if speed >= 1024 * 1024:
            speed_text = f"{speed / 1024 / 1024:.2f} MB/s"
        else:
            speed_text = f"{speed / 1024:.2f} KB/s"
        
        self.speed_label.config(text=f"速度: {speed_text} | 预计剩余: {eta:.0f} 秒")

    def _close_progress_window(self):
        """关闭进度窗口。"""
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None

    def _worker(self, url: str):
        """工作线程，从队列中获取并下载块。"""
        while not self._stop_event.is_set():
            try:
                task = self.task_queue.get_nowait()
            except Exception: # Queue Empty
                break # 队列为空，线程退出

            part_path, start_byte, end_byte, retries = task
            
            try:
                headers = {'Range': f'bytes={start_byte}-{end_byte}'}
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                with open(part_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self._stop_event.is_set():
                            # 如果任务被中断，将其放回队列以便其他线程可以处理
                            self.task_queue.put(task)
                            return
                        
                        f.write(chunk)
                        with self.shared_progress["lock"]:
                            self.shared_progress["downloaded_bytes"] += len(chunk)
                
                self.task_queue.task_done()

            except Exception as e:
                if self._stop_event.is_set():
                    self.task_queue.put(task) # 中断时放回任务
                    return

                logger.log_warning(f"下载块 {part_path} 失败: {e}。剩余重试次数: {retries}")
                if retries > 0:
                    # 失败，重新放入队列
                    task = (part_path, start_byte, end_byte, retries - 1)
                    self.task_queue.put(task)
                else:
                    logger.error(f"块 {part_path} 在所有重试后仍然失败。")
                    with self.shared_progress["lock"]:
                        self.shared_progress["error"] = e
                    # 即使一个块失败，也标记为完成以避免死锁
                    self.task_queue.task_done()
                
    def _combine_files(self, destination_path: str):
        """将下载的分块合并成一个文件。"""
        logger.log_info("开始合并文件分块...")
        part_paths = sorted(self.shared_progress["part_paths"], key=lambda p: int(p.split('.part')[-1]))
        try:
            with open(destination_path, 'wb') as dest_file:
                for part_path in part_paths:
                    if not os.path.exists(part_path):
                        logger.error(f"合并时未找到分块文件: {part_path}。下载可能不完整。")
                        raise FileNotFoundError(f"Missing part file: {part_path}")
                    with open(part_path, 'rb') as part_file:
                        dest_file.write(part_file.read())
            logger.log_info(f"文件成功合并到: {destination_path}")
        finally:
            # 清理临时分块文件
            for part_path in part_paths:
                if os.path.exists(part_path):
                    try:
                        os.remove(part_path)
                    except OSError as e:
                        logger.log_warning(f"删除临时文件 {part_path} 失败: {e}")

    def _single_thread_download(self, download_url: str, destination_path: str) -> Optional[str]:
        """原始的单线程下载逻辑，作为备用方案。"""
        logger.log_info("回退到单线程下载模式。")
        start_time = time.time()
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            downloaded_size = 0
            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._stop_event.is_set():
                        logger.log_info("单线程下载被中断。")
                        return None
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    self.parent_window.after(0, self._update_progress, downloaded_size, total_size, start_time)
            
            logger.log_info("单线程文件下载成功。")
            return destination_path
        except Exception as e:
            logger.log_error(f"单线程下载失败: {e}")
            self.parent_window.after(0, lambda: messagebox.showerror("下载失败", f"无法下载更新文件。\n错误: {e}"))
            return None

    def _download_update(self, download_url: str, destination_path: str) -> Optional[str]:
        """
        使用基于工作队列的动态多线程下载更新文件。
        """
        all_temp_files = []
        try:
            # 1. 检查服务器能力 (带重试机制)
            logger.log_info(f"开始下载: {download_url}")
            head_response = None
            for attempt in range(self.max_retries):
                try:
                    head_response = requests.head(download_url, timeout=10, allow_redirects=True)
                    head_response.raise_for_status()
                    break # 成功则跳出循环
                except requests.exceptions.RequestException as e:
                    logger.log_warning(f"获取文件头信息失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        raise # 所有重试失败后，重新引发异常

            if not head_response:
                 raise ConnectionError("无法获取文件元数据。")

            total_size = int(head_response.headers.get('content-length', 0))
            supports_range = head_response.headers.get('accept-ranges') == 'bytes'

            if not total_size or not supports_range:
                return self._single_thread_download(download_url, destination_path)

            # 2. 创建任务队列
            logger.log_info(f"文件总大小: {total_size / 1024 / 1024:.2f} MB。使用工作队列模式下载。")
            self.task_queue = Queue()
            
            # 重置共享进度
            self.shared_progress.update({
                "downloaded_bytes": 0,
                "total_bytes": total_size,
                "start_time": time.time(),
                "error": None,
                "part_paths": []
            })

            # 填充任务队列
            num_chunks = math.ceil(total_size / CHUNK_SIZE)
            for i in range(num_chunks):
                start_byte = i * CHUNK_SIZE
                end_byte = min((i + 1) * CHUNK_SIZE - 1, total_size - 1)
                part_path = f"{destination_path}.part{i}"
                all_temp_files.append(part_path)
                self.shared_progress["part_paths"].append(part_path)
                task = (part_path, start_byte, end_byte, DOWNLOAD_RETRY)
                self.task_queue.put(task)

            # 3. 创建并启动工作线程
            self.download_threads = []
            thread_count = min(num_chunks, MAX_THREADS)
            for _ in range(thread_count):
                thread = threading.Thread(target=self._worker, args=(download_url,), daemon=True)
                self.download_threads.append(thread)
                thread.start()

            # 4. 监控进度并等待完成
            while not self.task_queue.empty():
                if self._stop_event.is_set() or self.shared_progress["error"]:
                    break
                
                with self.shared_progress["lock"]:
                    downloaded = self.shared_progress["downloaded_bytes"]
                    start_time = self.shared_progress["start_time"]
                
                self.parent_window.after(0, self._update_progress, downloaded, total_size, start_time)
                time.sleep(0.2) # UI更新频率

            self.task_queue.join() # 等待所有任务完成

            # 5. 检查结果
            if self._stop_event.is_set():
                logger.log_info("下载被用户取消。")
                return None
            
            if self.shared_progress["error"]:
                err = self.shared_progress["error"]
                logger.log_error(f"下载因错误而失败: {err}")
                self.parent_window.after(0, lambda: messagebox.showerror("下载失败", f"下载更新时发生错误:\n{err}"))
                return None

            # 6. 合并文件
            self._combine_files(destination_path)
            
            # 最终进度更新到100%
            self.parent_window.after(0, self._update_progress, total_size, total_size, self.shared_progress["start_time"])
            logger.log_info("工作队列下载成功。")
            return destination_path

        except Exception as e:
            logger.log_error(f"下载失败 (严重错误): {e}")
            if not self._stop_event.is_set():
                # 修复lambda作用域问题
                self.parent_window.after(0, lambda e=e: messagebox.showerror("下载失败", f"下载更新时发生严重错误:\n{e}"))
            return None
        finally:
            # 确保所有临时文件在任何情况下都被清理
            for temp_file in all_temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except OSError:
                        pass
            
            # 如果下载失败或取消，删除可能已创建的不完整目标文件
            if os.path.exists(destination_path) and (self._stop_event.is_set() or self.shared_progress.get("error")):
                 try:
                    os.remove(destination_path)
                 except OSError:
                    pass

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
        """向当前运行的线程发送停止信号，并更新UI。"""
        if self._current_thread and self._current_thread.is_alive():
            logger.log_info(f"正在向主下载线程 {self._current_thread.name} 发送停止信号。")
            self._stop_event.set() # 设置事件，所有子线程都会检查到

            if self.cancel_button and self.cancel_button.winfo_exists():
                self.cancel_button.config(state=tk.DISABLED, text="正在取消...")
            if self.progress_label and self.progress_label.winfo_exists():
                self.progress_label.config(text="正在取消下载...")
            
            # 等待所有下载线程终止
            for thread in self.download_threads:
                thread.join(timeout=2)

            # 确保在UI更新后关闭窗口
            self.parent_window.after(200, self._close_progress_window)

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
    updater = Updater(root, config_handler=None) # 传递一个假的config_handler
    updater.run_update_flow()
    root.mainloop()

if __name__ == "__main__":
    main()
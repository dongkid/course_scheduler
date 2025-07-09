import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os
from tkinter import PhotoImage
from constants import APP_NAME, VERSION, PROJECT_URL
import threading

# 配置ttk样式
def configure_styles():
    style = ttk.Style()
    style.configure("AboutWindow.TFrame", background="white", padding=0)
    style.configure("AboutWindow.TLabel", background="white", font=("Microsoft YaHei", 8), padding=0)
    style.configure("AboutWindow.Title.TLabel", font=("Microsoft YaHei", 12, "bold"), padding=0)
    style.configure("AboutWindow.Url.TLabel", foreground="blue", font=("Microsoft YaHei", 5, "underline"), padding=0)
    style.configure("AboutWindow.TButton", font=("Microsoft YaHei", 8), padding=2)
    style.layout("AboutWindow.TFrame", [])
    style.layout("AboutWindow.TLabel", [])

class AboutWindow:
    def __init__(self, parent):
        """初始化关于窗口"""
        self.app = parent  # parent 现在是 app 实例
        self.parent = self.app.root
        self.window = self._create_window()
        self._initialize_ui()
        self._start_updater_preload()

    def _create_window(self) -> tk.Toplevel:
        """创建并配置关于窗口"""
        window = tk.Toplevel(self.parent)
        window.title("关于")
        window.geometry("500x200")
        window.minsize(500, 200)
        window.maxsize(600, 240)  # 设置窗口最大大小
        window.configure(bg="white")
        return window

    def _start_updater_preload(self):
        """在后台线程中预加载Updater模块。"""
        threading.Thread(target=self._preload_updater_task, daemon=True).start()

    def _preload_updater_task(self):
        """预加载Updater模块和实例的任务。"""
        # 检查updater实例是否已存在，避免重复创建
        if not hasattr(self.app, 'updater') or not self.app.updater:
            from updater import Updater
            # 再次检查，以防在导入期间主线程已创建实例（处理竞态条件）
            if not hasattr(self.app, 'updater') or not self.app.updater:
                self.app.updater = Updater(self.app.root, self.app.config_handler)

    def _update_font_size(self, event=None):
        """根据窗口宽度动态调整所有文本字体大小"""
        width = self.window.winfo_width()
        base_size = max(10, min(50, int(width / 25)))  # 基础字体大小
        style = ttk.Style()
        # 标题字体
        style.configure("AboutWindow.Title.TLabel", font=("Microsoft YaHei", base_size, "bold"), padding=0)
        # 普通文本字体
        style.configure("AboutWindow.TLabel", font=("Microsoft YaHei", int(base_size * 0.8)), padding=0)
        # URL文本字体
        style.configure("AboutWindow.Url.TLabel", font=("Microsoft YaHei", int(base_size * 0.6), "underline"), padding=0)

    def _initialize_ui(self) -> None:
        """初始化关于界面"""
        # 绑定窗口大小变化事件
        self.window.bind("<Configure>", self._update_font_size)
        
        # 主容器
        main_frame = ttk.Frame(self.window, style="AboutWindow.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部区域：图标和标题
        top_frame = ttk.Frame(main_frame, style="AboutWindow.TFrame",width=3)
        top_frame.pack(fill=tk.X, pady=(0, 3))
        
        try:
            icon = PhotoImage(file=os.path.join(sys._MEIPASS, 'res', 'icon.png')) if hasattr(sys, '_MEIPASS') else PhotoImage(file="res/icon.png")
            icon = icon.subsample(15, 15)  # 进一步缩小图标
            icon_label = tk.Label(top_frame, image=icon, bg="white")
            icon_label.image = icon
            icon_label.pack(side=tk.LEFT, padx=(0, 10))
        except Exception as e:
            print(f"无法加载图标: {e}")
        
        title_frame = ttk.Frame(top_frame, style="AboutWindow.TFrame")
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(title_frame, text=APP_NAME, style="AboutWindow.Title.TLabel").pack(anchor=tk.W)
        ttk.Label(title_frame, text=f"版本: {VERSION}", style="AboutWindow.TLabel").pack(anchor=tk.W)

        # 信息区域
        info_frame = ttk.Frame(main_frame, style="AboutWindow.TFrame")
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # 项目地址
        url_frame = ttk.Frame(info_frame, style="AboutWindow.TFrame")
        url_frame.pack(fill=tk.X, pady=2)
        
        def open_project_url():
            if sys.platform == 'win32':
                subprocess.Popen(['start', PROJECT_URL], shell=True)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', PROJECT_URL])
            else:
                subprocess.Popen(['xdg-open', PROJECT_URL])
            
        url_label = ttk.Label(
            url_frame,
            text=f"项目地址: {PROJECT_URL}",
            style="AboutWindow.Url.TLabel",
            cursor="hand2"
        )
        url_label.pack(anchor=tk.W)
        url_label.bind("<Button-1>", lambda e: open_project_url())

        # 开源协议
        license_frame = ttk.Frame(info_frame, style="AboutWindow.TFrame")
        license_frame.pack(fill=tk.X, pady=2)
        ttk.Label(license_frame, text="开源协议: GNU General Public License v3.0", style="AboutWindow.TLabel").pack(anchor=tk.W)

        # 检查更新按钮
        update_frame = ttk.Frame(info_frame, style="AboutWindow.TFrame")
        update_frame.pack(fill=tk.X, pady=2)
        
        self.check_update_btn = ttk.Button(
            update_frame,
            text="检查更新",
            style="AboutWindow.TButton",
            command=self.start_update_check
        )
        self.check_update_btn.pack(side=tk.RIGHT, padx=10)

        # 检查预发布版选项
        self.prerelease_var = tk.BooleanVar(value=self.app.config_handler.check_prerelease)
        prerelease_check = ttk.Checkbutton(
            update_frame,
            text="检查预览版",
            variable=self.prerelease_var,
            command=self.toggle_prerelease_check,
            style="AboutWindow.TCheckbutton"
        )
        prerelease_check.pack(side=tk.RIGHT, padx=(0, 10))

    def start_update_check(self):
        """启动异步更新检查"""
        self.check_update_btn.config(state=tk.DISABLED, text="检查中...")
        threading.Thread(target=self._perform_update_check, daemon=True).start()

    def _perform_update_check(self):
        """执行实际的更新检查"""
        # 如果自动更新被禁用，updater可能不存在，需要即时创建
        if not self.app.updater:
            from updater import Updater
            self.app.updater = Updater(self.app.root, self.app.config_handler)
            
        # 使用 app 中唯一的 updater 实例
        self.app.updater.run_update_flow()
        # 检查完成后，恢复按钮状态
        self.window.after(0, lambda: self.check_update_btn.config(state=tk.NORMAL, text="检查更新"))

    def toggle_prerelease_check(self):
        """切换是否检查预发布版本的配置"""
        self.app.config_handler.check_prerelease = self.prerelease_var.get()
        self.app.config_handler.save_config()

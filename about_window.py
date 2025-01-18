import tkinter as tk
import subprocess
import sys
from tkinter import PhotoImage
from constants import APP_NAME, VERSION, PROJECT_URL

class AboutWindow:
    def __init__(self, parent):
        """初始化关于窗口"""
        self.parent = parent
        self.window = self._create_window()
        self._initialize_ui()

    def _create_window(self) -> tk.Toplevel:
        """创建并配置关于窗口"""
        window = tk.Toplevel(self.parent)
        window.title("关于")
        window.geometry("500x200")
        return window

    def _initialize_ui(self) -> None:
        """初始化关于界面"""
        # 主容器
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 图标和标题
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        try:
            icon = PhotoImage(file=sys._MEIPASS + "/icon.png") if hasattr(sys, '_MEIPASS') else PhotoImage(file="res/icon.png")
            # 调整图标大小
            icon = icon.subsample(10, 10)  # 缩小为原来的1/5
            icon_label = tk.Label(header_frame, image=icon)
            icon_label.image = icon  # 保持引用
            icon_label.pack(side=tk.LEFT, padx=(0, 20))
        except Exception as e:
            print(f"无法加载图标: {e}")
        
        title_label = tk.Label(
            header_frame,
            text=APP_NAME,
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 信息面板
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # 版本信息
        version_frame = tk.Frame(info_frame)
        version_frame.pack(fill=tk.X, pady=5)
        tk.Label(version_frame, text="版本:", width=8, anchor=tk.W).pack(side=tk.LEFT)
        tk.Label(version_frame, text=VERSION).pack(side=tk.LEFT)
        
        # 项目地址
        url_frame = tk.Frame(info_frame)
        url_frame.pack(fill=tk.X, pady=5)
        tk.Label(url_frame, text="项目地址:", width=8, anchor=tk.W).pack(side=tk.LEFT)
        
        def open_project_url():
            if sys.platform == 'win32':
                subprocess.Popen(['start', PROJECT_URL], shell=True)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', PROJECT_URL])
            else:
                subprocess.Popen(['xdg-open', PROJECT_URL])
            
        url_label = tk.Label(
            url_frame,
            text=PROJECT_URL,
            fg="blue",
            cursor="hand2"
        )
        url_label.pack(side=tk.LEFT)
        url_label.bind("<Button-1>", lambda e: open_project_url())

        # 开源协议
        license_frame = tk.Frame(info_frame)
        license_frame.pack(fill=tk.X, pady=5)
        tk.Label(license_frame, text="开源协议:", width=8, anchor=tk.W).pack(side=tk.LEFT)
        tk.Label(license_frame, text="GNU General Public License v3.0").pack(side=tk.LEFT)

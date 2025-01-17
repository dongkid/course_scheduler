import tkinter as tk
from tkinter import ttk
from typing import Callable
from tools.fullscreen_time import FullscreenTimeWindow

class ToolsWindow:
    """小工具窗口类"""
    def __init__(self, root: tk.Tk):
        """初始化小工具窗口
        
        Args:
            root: 主窗口
        """
        self.root = root
        self.window = None
        self.style = ttk.Style()
        
    def show(self):
        """显示小工具窗口"""
        if self.window is None or not self.window.winfo_exists():
            self._create_window()
        else:
            self.window.lift()
            
    def _create_window(self):
        """创建小工具窗口"""
        self.window = tk.Toplevel(self.root)
        self.window.title("小工具")
        self.window.resizable(False, False)
        self.window.geometry("800x300")
        self.window.configure(bg="white")
        
        # 配置样式
        self.style.configure("TFrame", background="white")
        self.style.configure("TLabel", background="white", 
                           font=("微软雅黑", 14))
        self.style.configure("Title.TLabel", font=("微软雅黑", 24, "bold"),
                           foreground="#2c3e50")
        self.style.configure("Subtitle.TLabel", font=("微软雅黑", 14),
                           foreground="#7f8c8d")
        self.style.configure("TButton", font=("微软雅黑", 12), 
                           padding=10, width=15)
        self.style.map("TButton",
                      foreground=[("active", "#ffffff")],
                      background=[("active", "#3498db")])
        
        # 主容器
        main_frame = ttk.Frame(self.window)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # 添加标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame,
            text="小工具",
            style="Title.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        # 添加按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        # 全屏大号时间按钮
        fullscreen_time_btn = ttk.Button(
            button_frame,
            text="全屏大号时间",
            command=self._show_fullscreen_time,
            style="TButton"
        )
        fullscreen_time_btn.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 未完待续按钮
        todo_btn = ttk.Button(
            button_frame,
            text="未完待续",
            command=self._show_todo,
            style="TButton"
        )
        todo_btn.pack(side=tk.LEFT, padx=10, pady=5)
        
    def _show_fullscreen_time(self):
        """显示全屏大号时间"""
        self.fullscreen_time_window = FullscreenTimeWindow(self.root)
        self.fullscreen_time_window.show()
        
    def _show_todo(self):
        """显示未完待续"""
        # TODO: 实现未完待续功能
        pass

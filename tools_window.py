import tkinter as tk
from tkinter import ttk
from typing import Callable

class ToolsWindow:
    """小工具窗口类"""
    def __init__(self, root: tk.Tk, config_handler, main_app):
        """初始化小工具窗口
        
        Args:
            root: 主窗口
            config_handler: 配置处理器
            main_app: 主应用实例
        """
        self.root = root
        self.config_handler = config_handler
        self.main_app = main_app
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
        if self.config_handler.experimental_dpi_awareness:
            self.window.geometry("1000x300") # 增加高度
        else:
            self.window.geometry("800x200")
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
                           padding=10, width=10)
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
        button_frame.pack(pady=20, expand=True, fill=tk.X)

        buttons = {
            "全屏大号时间": self._show_fullscreen_time,
            "天气": self._show_weather,
            "数独": self._show_sudoku,
            "AI 助手": self._show_ai_assistant,
            "未完待续": self._show_todo
        }

        # Configure grid columns to share space equally
        for i in range(len(buttons)):
            button_frame.grid_columnconfigure(i, weight=1)

        for i, (text, command) in enumerate(buttons.items()):
            btn = ttk.Button(
                button_frame,
                text=text,
                command=command,
                style="TButton"
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
        
    def _show_fullscreen_time(self):
        """显示全屏大号时间"""
        from tools.fullscreen_time import FullscreenTimeWindow
        self.fullscreen_time_window = FullscreenTimeWindow(self.root, self.config_handler)
        self.fullscreen_time_window.show()
        
    def _show_todo(self):
        """显示未完待续"""
        # TODO: 实现未完待续功能
        pass
        
    def _show_weather(self):
        """显示天气"""
        from tools.weather import WeatherTool
        self.weather_tool = WeatherTool()
        self.weather_tool.show()
        
    def _show_sudoku(self):
        """显示数独游戏"""
        from tools.sudoku_ui import SudokuApp
        self.sudoku_window = SudokuApp(self.root)

    def _show_ai_assistant(self):
        """显示AI助手"""
        from tools.ai_assistant import AIAssistantWindow
        self.ai_assistant_window = AIAssistantWindow(self.main_app)
        self.ai_assistant_window.show()

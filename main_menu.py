import tkinter as tk
from tkinter import ttk
from typing import Callable
from constants import VERSION

class MainMenu:
    """主菜单类"""
    def __init__(self, root: tk.Tk, config_handler, dpi_manager, button_commands: dict[str, Callable]):
        """初始化主菜单
        
        Args:
            root: 主窗口
            config_handler: 配置处理器
            dpi_manager: DPI管理器
            button_commands: 按钮命令字典，格式为{"按钮文本": 回调函数}
        """
        self.root = root
        self.config_handler = config_handler
        self.dpi_manager = dpi_manager
        self.button_commands = button_commands
        self.menu_window = None
        self.style = ttk.Style()
        
    def show(self):
        """显示主菜单"""
        if self.menu_window is None or not self.menu_window.winfo_exists():
            self._create_menu_window()
        else:
            self.menu_window.lift()
            
    def _create_menu_window(self):
        """创建主菜单窗口"""
        self.menu_window = tk.Toplevel(self.root)
        self.menu_window.title("主菜单")
        self.menu_window.resizable(False, False)

        # 使用DPI管理器动态计算尺寸
        width = self.dpi_manager.scale(1100)
        height = self.dpi_manager.scale(250)
        self.menu_window.geometry(f"{width}x{height}")
        self.menu_window.configure(bg="white")

        # 动态配置样式
        self.style.configure("TFrame", background="white")
        self.style.configure("TLabel", background="white",
                           font=("微软雅黑", self.dpi_manager.scale(14)))
        self.style.configure("Title.TLabel", font=("微软雅黑", self.dpi_manager.scale(24), "bold"),
                           foreground="#2c3e50")
        self.style.configure("Subtitle.TLabel", font=("微软雅黑", self.dpi_manager.scale(14)),
                           foreground="#7f8c8d")
        scaled_padding = self.dpi_manager.scale(10)
        self.style.configure("TButton", font=("微软雅黑", self.dpi_manager.scale(12)),
                           padding=scaled_padding)
        self.style.map("TButton",
                      foreground=[("active", "#ffffff")],
                      background=[("active", "#3498db")])

        # 主容器
        scaled_padx = self.dpi_manager.scale(20)
        scaled_pady = self.dpi_manager.scale(20)
        main_frame = ttk.Frame(self.menu_window)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=scaled_padx, pady=scaled_pady)

        # 添加标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, self.dpi_manager.scale(10)))
        
        title_label = ttk.Label(
            title_frame,
            text="欢迎使用桌面课程表",
            style="Title.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        # 添加副标题
        subtitle_label = ttk.Label(
            main_frame,
            text=f"主菜单  v{VERSION}",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(pady=(0, self.dpi_manager.scale(20)))

        # 添加按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()

        for text, command in self.button_commands.items():
            btn = ttk.Button(
                button_frame,
                text=text,
                command=command,
                style="TButton"
            )
            scaled_padx = self.dpi_manager.scale(5)
            scaled_pady = self.dpi_manager.scale(10)
            btn.pack(side=tk.LEFT, padx=scaled_padx, pady=scaled_pady, fill=tk.X, expand=True)

    def create_menu_button(self, parent: tk.Widget) -> ttk.Button:
        """创建主菜单按钮"""
        # 动态配置主菜单按钮样式
        scaled_font_size = self.dpi_manager.scale(12)
        scaled_padding = self.dpi_manager.scale(3)
        self.style.configure("Menu.TButton",
                           font=("微软雅黑", scaled_font_size),
                           padding=scaled_padding,
                           width=8,
                           foreground="#000000",
                           background="#ffffff",
                           borderwidth=0)

        return ttk.Button(
            parent,
            text="主菜单",
            command=self.show,
            style="Menu.TButton"
        )
        

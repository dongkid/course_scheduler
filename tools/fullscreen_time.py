import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Callable
import pycaw

class FullscreenTimeWindow:
    """全屏时间窗口类"""
    
    def __init__(self, root: tk.Tk):
        """初始化全屏时间窗口
        
        Args:
            root: 主窗口
        """
        self.root = root
        self.window = None
        self.time_label = None
        self.update_time_id = None
        
    def show(self):
        """显示全屏时间窗口"""
        if self.window is None or not self.window.winfo_exists():
            self._create_window()
        else:
            self.window.lift()
            
    def _create_window(self):
        """创建全屏时间窗口"""
        self.window = tk.Toplevel(self.root)
        self.window.attributes("-fullscreen", True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg="white")
        self.window.bind("<Escape>", lambda e: self.window.destroy())
        
        # 配置复选框样式
        style = ttk.Style()
        style.configure("White.TCheckbutton",
                      background="white",
                      foreground="black")
        
        # 添加静音复选框
        self.mute_var = tk.BooleanVar(value=False)
        self.mute_checkbox = ttk.Checkbutton(
            self.window,
            text="屏蔽系统声音", 
            variable=self.mute_var,
            command=self._toggle_mute,
            style="White.TCheckbutton"
        )
        self.mute_checkbox.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
        
        # 创建时间标签
        self.time_label = tk.Label(
            self.window,
            font=("微软雅黑", 300, "bold"),
            fg="black",
            bg="white"
        )
        self.time_label.pack(expand=True)
        
        # 开始更新时间
        self._update_time()
        
    def _update_time(self):
        """更新时间显示"""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        self.time_label.config(text=time_str)
        self.update_time_id = self.window.after(1000, self._update_time)
        
    def _toggle_mute(self):
        """切换静音状态"""
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, 0, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            
            if self.mute_var.get():
                volume.SetMute(1, None)
            else:
                volume.SetMute(0, None)
        except Exception as e:
            print(f"静音操作失败: {e}")
            
    def destroy(self):
        """销毁窗口"""
        if self.update_time_id:
            self.window.after_cancel(self.update_time_id)
        if self.window:
            # 取消静音
            self.mute_var.set(False)
            self._toggle_mute()
            self.window.destroy()

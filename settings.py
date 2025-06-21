import tkinter as tk
from tkinter import ttk
import sys
from tkinter import messagebox, colorchooser
from datetime import datetime
from constants import DEFAULT_GEOMETRY, CONFIG_FILE, APP_NAME, AUTHOR, VERSION, PROJECT_URL
from about_window import AboutWindow
from logger import logger

class SettingsWindow:
    def __init__(self, main_app):
        """初始化设置窗口"""
        try:
            self.main_app = main_app
            self.window = self._create_window()
            self.applying = False
            self._initialize_ui()
        except Exception as e:
            logger.log_error(e)
            raise

    def _create_window(self) -> tk.Toplevel:
        """创建并配置设置窗口"""
        window = tk.Toplevel()
        window.title("设置")
        window.geometry("650x850")
        window.resizable(False, False)
        window.configure(bg="white")
        
        # 配置样式
        self.style = ttk.Style()
        self.style.configure("TFrame", background="white")
        self.style.configure("TLabel", background="white", 
                           font=("微软雅黑", 14))
        # 新增小按钮样式
        self.style.configure("PMSmall.TButton", 
                           font=("微软雅黑", 10),
                           padding=0,
                           width=3)
        self.style.configure("TLabelframe", background="white")
        self.style.configure("TLabelframe.Label", background="white")
        self.style.configure("TNotebook", background="white")
        self.style.configure("TNotebook.Tab", background="white", padding=[10, 5])
        # 定义白色风格的Checkbutton
        self.style.configure("White.TCheckbutton",
                           background="white",
                           font=("微软雅黑", 12))
        self.style.map("White.TCheckbutton",
                      background=[("active", "white")],
                      foreground=[("active", "black")])
        self.style.configure("Title.TLabel", font=("微软雅黑", 24, "bold"),
                           foreground="#2c3e50")
        self.style.configure("Subtitle.TLabel", font=("微软雅黑", 14),
                           foreground="#7f8c8d")
        self.style.configure("TButton", font=("微软雅黑", 12), 
                           padding=10, width=15)
        self.style.map("TButton",
                      foreground=[("active", "#ffffff")],
                      background=[("active", "#3498db")])
        
        return window

    def _initialize_ui(self) -> None:
        """初始化设置界面"""
        # 主容器
        main_frame = ttk.Frame(self.window, style="TFrame")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # 添加标题
        title_frame = ttk.Frame(main_frame, style="TFrame")
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame,
            text="设置",
            style="Title.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        # 添加副标题
        subtitle_label = ttk.Label(
            main_frame,
            text=f"设置  v{VERSION}",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # 创建Notebook组件
        self.notebook = ttk.Notebook(main_frame, style="TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True)
        # 设置Notebook内部Frame的背景颜色
        for child in self.notebook.winfo_children():
            child.configure(background="white")
        
        # 创建各个设置标签页
        self._create_layout_tab()
        self._create_window_tab()
        self._create_course_tab()
        self._create_theme_tab()
        self._create_tools_tab()
        self._create_other_tab()

        # 在Notebook下方创建操作按钮
        button_frame = ttk.Frame(main_frame, style="TFrame")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text="应用",
            command=self.apply_settings,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
        
        ttk.Button(
            button_frame,
            text="重启程序",
            command=self.restart_ui,
            style="TButton"
        ).pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
        
    def _create_layout_tab(self) -> None:
        """创建排版设置标签页"""
        layout_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(layout_frame, text="排版设置")
        
        def create_spinbox(frame, entry_var, row):
            """创建带加减按钮的输入控件"""
            # 减按钮（-1）
            ttk.Button(
                frame, 
                text="-", 
                style="PMSmall.TButton",
            command=lambda: entry_var.set(max(0, int(entry_var.get() or 0) - 1))
            ).grid(row=row, column=2, padx=(10,0), pady=5, ipadx=2, ipady=1)
            
            # 加按钮（+1）
            ttk.Button(
                frame,
                text="+",
                style="PMSmall.TButton",
            command=lambda: entry_var.set(int(entry_var.get() or 0) + 1)
            ).grid(row=row, column=3, padx=(0,10), pady=5, ipadx=2, ipady=1)
            
        # ========== 控件大小设置 ==========
        control_size_frame = ttk.LabelFrame(layout_frame, text="控件大小", style="TFrame")
        control_size_frame.pack(fill=tk.X, padx=10, pady=5)

        # 时间显示大小（新增按钮）
        time_size_var = tk.StringVar(value=self.main_app.config_handler.time_display_size)
        ttk.Label(control_size_frame, text="时间显示大小:").grid(row=0, column=0, padx=5, pady=5)
        self.time_display_size = ttk.Entry(control_size_frame, width=5, textvariable=time_size_var)
        self.time_display_size.grid(row=0, column=1, padx=5, pady=5)
        create_spinbox(control_size_frame, time_size_var, 0)

        # 倒计时大小（新增按钮）
        countdown_size_var = tk.StringVar(value=self.main_app.config_handler.countdown_size)
        ttk.Label(control_size_frame, text="倒计时大小:").grid(row=1, column=0, padx=5, pady=5)
        self.countdown_size = ttk.Entry(control_size_frame, width=5, textvariable=countdown_size_var)
        self.countdown_size.grid(row=1, column=1, padx=5, pady=5)
        create_spinbox(control_size_frame, countdown_size_var, 1)

        # 课程表大小（新增按钮）
        schedule_size_var = tk.StringVar(value=self.main_app.config_handler.schedule_size)
        ttk.Label(control_size_frame, text="课程表大小:").grid(row=2, column=0, padx=5, pady=5)
        self.schedule_size = ttk.Entry(control_size_frame, width=5, textvariable=schedule_size_var)
        self.schedule_size.grid(row=2, column=1, padx=5, pady=5)
        create_spinbox(control_size_frame, schedule_size_var, 2)

        # ========== 间距设置 ==========
        padding_frame = ttk.LabelFrame(layout_frame, text="间距设置", style="TFrame")
        padding_frame.pack(fill=tk.X, padx=10, pady=5)

        # 水平间距（新增按钮）
        horizontal_var = tk.StringVar(value=self.main_app.config_handler.horizontal_padding)
        ttk.Label(padding_frame, text="水平间距:").grid(row=0, column=0, padx=5, pady=5)
        self.horizontal_padding = ttk.Entry(padding_frame, width=5, textvariable=horizontal_var)
        self.horizontal_padding.grid(row=0, column=1, padx=5, pady=5)
        create_spinbox(padding_frame, horizontal_var, 0)

        # 垂直间距（新增按钮）
        vertical_var = tk.StringVar(value=self.main_app.config_handler.vertical_padding)
        ttk.Label(padding_frame, text="垂直间距:").grid(row=1, column=0, padx=5, pady=5)
        self.vertical_padding = ttk.Entry(padding_frame, width=5, textvariable=vertical_var)
        self.vertical_padding.grid(row=1, column=1, padx=5, pady=5)
        create_spinbox(padding_frame, vertical_var, 1)
    
    def _create_window_tab(self) -> None:
        """创建窗口控制标签页"""
        window_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(window_frame, text="窗口控制")
        
        # 窗口位置控制
        pos_frame = ttk.LabelFrame(window_frame, text="窗口位置", style="TFrame")
        pos_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def create_button(frame, text, dx, dy):
            button = ttk.Button(frame, text=text, width=5, style="TButton")
            button.pack(side=tk.LEFT, padx=5, pady=5)
            
            def start_move():
                self.move_window(dx, dy)
                current_delay = getattr(button, 'current_delay', 100)
                new_delay = max(10, current_delay - 5)
                button.current_delay = new_delay
                button.after_id = button.after(new_delay, start_move)
            
            def stop_move():
                if hasattr(button, 'after_id'):
                    button.after_cancel(button.after_id)
                    del button.after_id
                if hasattr(button, 'current_delay'):
                    del button.current_delay
            
            button.bind("<ButtonPress-1>", lambda e: start_move())
            button.bind("<ButtonRelease-1>", lambda e: stop_move())
            return button
        
        create_button(pos_frame, "←", -10, 0)
        create_button(pos_frame, "→", 10, 0)
        create_button(pos_frame, "↑", 0, -10)
        create_button(pos_frame, "↓", 0, 10)

        # 窗口大小控制
        size_frame = ttk.LabelFrame(window_frame, text="窗口大小", style="TFrame")
        size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 宽度设置带加减按钮
        width_var = tk.StringVar(value=self.main_app.root.winfo_width())
        ttk.Label(size_frame, text="宽度:").grid(row=0, column=0, padx=5, pady=5)
        self.width_entry = ttk.Entry(size_frame, width=5, textvariable=width_var)
        self.width_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 宽度加减按钮
        ttk.Button(
            size_frame, 
            text="-", 
            style="PMSmall.TButton",
            command=lambda: width_var.set(max(100, int(width_var.get() or 100) - 10))
        ).grid(row=0, column=2, padx=(10,0), pady=5)
        ttk.Button(
            size_frame,
            text="+",
            style="PMSmall.TButton",
            command=lambda: width_var.set(int(width_var.get() or 100) + 10)
        ).grid(row=0, column=3, padx=(0,10), pady=5)

        # 高度设置带加减按钮
        height_var = tk.StringVar(value=self.main_app.root.winfo_height())
        ttk.Label(size_frame, text="高度:").grid(row=1, column=0, padx=5, pady=5)
        self.height_entry = ttk.Entry(size_frame, width=5, textvariable=height_var)
        self.height_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 高度加减按钮
        ttk.Button(
            size_frame, 
            text="-", 
            style="PMSmall.TButton",
            command=lambda: height_var.set(max(100, int(height_var.get() or 100) - 10))
        ).grid(row=1, column=2, padx=(10,0), pady=5)
        ttk.Button(
            size_frame,
            text="+",
            style="PMSmall.TButton",
            command=lambda: height_var.set(int(height_var.get() or 100) + 10)
        ).grid(row=1, column=3, padx=(0,10), pady=5)

    def _create_course_tab(self) -> None:
        """创建课程设置标签页"""
        course_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(course_frame, text="课程设置")
        
        # 课程时长设置
        duration_frame = ttk.LabelFrame(course_frame, text="课程时长设置", style="TFrame")
        duration_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(duration_frame, text="课程时长（分钟）:").grid(row=0, column=0, padx=5, pady=5)
        self.duration_entry = ttk.Entry(duration_frame, width=5)
        self.duration_entry.grid(row=0, column=1, padx=5, pady=5)
        self.duration_entry.insert(0, str(self.main_app.config_handler.course_duration))
        
        # 自动补全结束时间
        self.auto_complete_var = tk.BooleanVar(value=self.main_app.config_handler.auto_complete_end_time)
        self.auto_complete_check = ttk.Checkbutton(
            duration_frame, text="自动补全结束时间",
            variable=self.auto_complete_var,
            style="White.TCheckbutton")
        self.auto_complete_check.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # 自动计算下一个课程时间
        self.auto_calculate_var = tk.BooleanVar(value=self.main_app.config_handler.auto_calculate_next_course)
        self.auto_calculate_check = ttk.Checkbutton(
            duration_frame, text="自动计算下一个课程时间",
            variable=self.auto_calculate_var,
            style="White.TCheckbutton")
        self.auto_calculate_check.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        # 课间时间设置
        ttk.Label(duration_frame, text="课间时间（分钟）:").grid(row=3, column=0, padx=5, pady=5)
        self.break_duration_entry = ttk.Entry(duration_frame, width=5)
        self.break_duration_entry.grid(row=3, column=1, padx=5, pady=5)
        self.break_duration_entry.insert(0, str(self.main_app.config_handler.break_duration))

        # 课表轮换设置
        rotation_frame = ttk.LabelFrame(course_frame, text="课表轮换设置", style="TFrame")
        rotation_frame.pack(fill=tk.X, padx=10, pady=5)

        # 启用轮换复选框
        self.rotation_var = tk.BooleanVar(value=self.main_app.config_handler.schedule_rotation_enabled)
        self.rotation_check = ttk.Checkbutton(
            rotation_frame, 
            text="启用每周课表轮换",
            variable=self.rotation_var,
            style="White.TCheckbutton"
        )
        self.rotation_check.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        # 课表选择
        ttk.Label(rotation_frame, text="第一周课表:").grid(row=1, column=0, padx=5)
        self.schedule1_var = tk.StringVar(value=self.main_app.config_handler.rotation_schedule1)
        self.schedule1_combo = ttk.Combobox(
            rotation_frame,
            textvariable=self.schedule1_var,
            values=list(self.main_app.schedule["schedules"].keys()),
            state="readonly"
        )
        self.schedule1_combo.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(rotation_frame, text="第二周课表:").grid(row=2, column=0, padx=5)
        self.schedule2_var = tk.StringVar(value=self.main_app.config_handler.rotation_schedule2)
        self.schedule2_combo = ttk.Combobox(
            rotation_frame,
            textvariable=self.schedule2_var,
            values=list(self.main_app.schedule["schedules"].keys()),
            state="readonly"
        )
        self.schedule2_combo.grid(row=2, column=1, padx=5, pady=2)

        # 倒计时与默认课表设置
        gaokao_frame = ttk.LabelFrame(course_frame, text="倒计时与默认课表", style="TFrame")
        gaokao_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 倒计时设置
        countdown_frame = ttk.LabelFrame(gaokao_frame, text="倒计时设置", style="TFrame")
        countdown_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(countdown_frame, text="倒计时名称:").grid(row=0, column=0, padx=5, pady=5)
        self.countdown_name_entry = ttk.Entry(countdown_frame, width=10)
        self.countdown_name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.countdown_name_entry.insert(0, self.main_app.config_handler.countdown_name)
        
        ttk.Label(countdown_frame, text="倒计时日期:").grid(row=1, column=0, padx=5, pady=5)
        self.countdown_date_entry = ttk.Entry(countdown_frame, width=10)
        self.countdown_date_entry.grid(row=1, column=1, padx=5, pady=5)
        self.countdown_date_entry.insert(0, self.main_app.config_handler.countdown_date.strftime("%Y-%m-%d"))

        # 默认课表设置
        courses_frame = ttk.LabelFrame(gaokao_frame, text="默认课表设置", style="TFrame")
        courses_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.courses_text = tk.Text(courses_frame, height=5, width=30)
        self.courses_text.pack(padx=5, pady=5)
        self.courses_text.insert(tk.END, "\n".join(self.main_app.config_handler.default_courses))
        
        ttk.Label(courses_frame, text="每行一个课程名称").pack()

    def _create_theme_tab(self) -> None:
        """创建主题设置标签页"""
        theme_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(theme_frame, text="主题设置")
        
        # 字体设置
        font_frame = ttk.LabelFrame(theme_frame, text="字体设置", style="TFrame")
        font_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 字体大小设置
        ttk.Label(font_frame, text="字体大小:").grid(row=0, column=0, padx=5, pady=5)
        self.font_size = ttk.Scale(font_frame, from_=8, to=32, orient=tk.HORIZONTAL)
        self.font_size.set(self.main_app.config_handler.font_size)
        self.font_size.grid(row=0, column=1, padx=5, pady=5)
        
        # 字体颜色设置
        def choose_color():
            color = colorchooser.askcolor()[1]
            if color:
                self.font_color = color
                self.color_preview.config(bg=color)
        
        self.font_color = self.main_app.config_handler.font_color
        self.color_preview = ttk.Label(font_frame, text="颜色", background=self.font_color, width=5)
        self.color_preview.grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(font_frame, text="选择颜色", command=choose_color, style="TButton").grid(row=1, column=1, padx=5, pady=5)
        
        # 透明度设置
        transparent_frame = ttk.LabelFrame(theme_frame, text="透明度设置", style="TFrame")
        transparent_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.transparent_var = tk.BooleanVar(value=self.main_app.config_handler.transparent_background)
        self.transparent_check = ttk.Checkbutton(
            transparent_frame, text="主界面透明度",
            variable=self.transparent_var,
            style="White.TCheckbutton")
        self.transparent_check.pack()

    def _create_tools_tab(self) -> None:
        """创建小工具设置标签页"""
        tools_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(tools_frame, text="小工具")
        
        # 添加全屏时间副标题设置
        fullscreen_frame = ttk.LabelFrame(tools_frame, text="全屏时间设置", style="TFrame")
        fullscreen_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(fullscreen_frame, text="副标题内容:").grid(row=0, column=0, padx=5, pady=5)
        self.fullscreen_subtitle_entry = ttk.Entry(fullscreen_frame, width=30)
        self.fullscreen_subtitle_entry.grid(row=0, column=1, padx=5, pady=5)
        self.fullscreen_subtitle_entry.insert(0, self.main_app.config_handler.fullscreen_subtitle)

        # 天气工具设置
        weather_frame = ttk.LabelFrame(tools_frame, text="天气工具设置", style="TFrame")
        weather_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(weather_frame, text="和风天气API Key:").grid(row=0, column=0, padx=5, pady=5)
        self.heweather_key_entry = ttk.Entry(weather_frame, width=35)
        self.heweather_key_entry.grid(row=0, column=1, padx=5, pady=5)
        self.heweather_key_entry.insert(0, self.main_app.config_handler.heweather_api_key)

    def _create_other_tab(self) -> None:
        """创建其他设置标签页"""
        other_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(other_frame, text="其他设置")
        
        # 开机自启动设置
        auto_start_frame = ttk.LabelFrame(other_frame, text="开机自启动", style="TFrame")
        auto_start_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.auto_start_var = tk.BooleanVar(value=self.main_app.config_handler.auto_start)
        self.auto_start_check = ttk.Checkbutton(
            auto_start_frame, text="开机时自动启动程序",
            variable=self.auto_start_var,
            style="White.TCheckbutton")
        self.auto_start_check.pack(side=tk.LEFT, padx=5)

        # 调试模式设置
        debug_frame = ttk.LabelFrame(other_frame, text="调试模式", style="TFrame")
        debug_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.debug_var = tk.BooleanVar(value=self.main_app.config_handler.debug_mode)
        self.debug_check = ttk.Checkbutton(
            debug_frame, text="启用调试模式",
            variable=self.debug_var,
            style="White.TCheckbutton")
        self.debug_check.pack(side=tk.LEFT, padx=5)

        # 自动更新设置
        update_frame = ttk.LabelFrame(other_frame, text="自动更新", style="TFrame")
        update_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.auto_update_check_var = tk.BooleanVar(value=self.main_app.config_handler.auto_update_check_enabled)
        self.auto_update_check = ttk.Checkbutton(
            update_frame, text="启动时检查更新",
            variable=self.auto_update_check_var,
            style="White.TCheckbutton")
        self.auto_update_check.pack(side=tk.LEFT, padx=5)

        # 日志设置
        log_frame = ttk.LabelFrame(other_frame, text="日志设置", style="TFrame")
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(log_frame, text="日志保留天数:").grid(row=0, column=0, padx=5, pady=5)
        self.log_retention_days_entry = ttk.Entry(log_frame, width=5)
        self.log_retention_days_entry.grid(row=0, column=1, padx=5, pady=5)
        self.log_retention_days_entry.insert(0, str(self.main_app.config_handler.log_retention_days))


    def destroy_children(self, widget):
        """递归销毁所有子组件"""
        for child in widget.winfo_children():
            if child.winfo_children():
                self.destroy_children(child)
            child.destroy()

    def restart_ui(self, open_settings=False) -> None:
        """触发进程级完全重启"""
        if self.main_app.config_handler.debug_mode:
            from restart_manager import RestartManager
            RestartManager.restart_application(self.main_app, open_settings=open_settings)
        else:
            if messagebox.askyesno("确认", "确定要重启程序吗？"):
                from restart_manager import RestartManager
                RestartManager.restart_application(self.main_app, open_settings=open_settings)

    def _show_about(self) -> None:
        """显示关于对话框"""
        AboutWindow(self.window)
    
    def move_window(self, dx, dy):
        screen_width = self.main_app.root.winfo_screenwidth()
        screen_height = self.main_app.root.winfo_screenheight()
        window_width = self.main_app.root.winfo_width()
        window_height = self.main_app.root.winfo_height()
        
        x = self.main_app.root.winfo_x() + dx
        y = self.main_app.root.winfo_y() + dy
        
        # 确保窗口不会移出屏幕
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        
        # 更新geometry并保存
        self.main_app.config_handler.geometry = f"{window_width}x{window_height}+{x}+{y}"
        self.main_app.root.geometry(f"+{x}+{y}")
        self.main_app.config_handler.save_config()
    
    def _save_heweather_key(self):
        """保存和风天气API Key"""
        try:
            self.main_app.config_handler.heweather_api_key = self.heweather_key_entry.get()
            self.main_app.config_handler.save_config()
            messagebox.showinfo("成功", "API Key已保存")
        except Exception as e:
            logger.log_error(e)
            messagebox.showerror("错误", "保存Key时发生错误")

    def apply_settings(self):
        if self.applying:  # 如果正在处理，直接返回
            return
        self.applying = True  # 设置标志位为处理中
        
        # 保存旧值用于比较
        old_layout = {
            'horizontal_padding': self.main_app.config_handler.horizontal_padding,
            'vertical_padding': self.main_app.config_handler.vertical_padding,
            'time_display_size': self.main_app.config_handler.time_display_size,
            'countdown_size': self.main_app.config_handler.countdown_size,
            'schedule_size': self.main_app.config_handler.schedule_size,
            'font_size': self.main_app.config_handler.font_size,
            'font_color': self.main_app.config_handler.font_color
        }
        
        try:
            # 应用排版设置
            try:
                horizontal_padding = max(0, int(self.horizontal_padding.get() or 0))
                vertical_padding = max(0, int(self.vertical_padding.get() or 0))
                self.main_app.config_handler.horizontal_padding = horizontal_padding
                self.main_app.config_handler.vertical_padding = vertical_padding
            except ValueError:
                messagebox.showerror("错误", "请输入有效的间距值")
                return
            
            # 应用窗口大小设置
            try:
                width = int(self.width_entry.get())
                height = int(self.height_entry.get())
                if width < 100 or height < 100:
                    raise ValueError
                x = self.main_app.root.winfo_x()
                y = self.main_app.root.winfo_y()
                # 构建新的geometry并保存到配置
                new_geometry = f"{width}x{height}+{x}+{y}"
                self.main_app.root.geometry(new_geometry)
                self.main_app.config_handler.geometry = new_geometry
                self.main_app.root.update()
                self.main_app.root.update_idletasks()
                # 更新输入框中的值
                self.width_entry.delete(0, tk.END)
                self.width_entry.insert(0, str(width))
                self.height_entry.delete(0, tk.END)
                self.height_entry.insert(0, str(height))
            except:
                messagebox.showerror("错误", "请输入有效的窗口尺寸")
                return
            
            # 应用倒计时设置
            try:
                self.main_app.config_handler.countdown_name = self.countdown_name_entry.get()
                countdown_date = datetime.strptime(self.countdown_date_entry.get(), "%Y-%m-%d")
                if countdown_date < datetime.now():
                    messagebox.showerror("错误", "倒计时日期不能是过去的时间")
                    return
                self.main_app.config_handler.countdown_date = countdown_date
            except ValueError:
                messagebox.showerror("错误", "请输入有效的日期格式 (YYYY-MM-DD)")
                return
            
            # 应用课程时长设置
            try:
                duration = int(self.duration_entry.get())
                if duration <= 0:
                    raise ValueError
                self.main_app.config_handler.course_duration = duration
            except ValueError:
                messagebox.showerror("错误", "请输入有效的课程时长")
                return
            
            # 应用开机自启动设置
            self.main_app.config_handler.auto_start = self.auto_start_var.get()
            if self.main_app.config_handler.auto_start:
                from auto_start import enable_auto_start
                # 处理打包后的路径问题
                exe_path = sys.executable if not getattr(sys, 'frozen', False) else sys._MEIPASS + '/course_scheduler.exe'
                enable_auto_start("CourseScheduler", exe_path)
            else:
                from auto_start import disable_auto_start
                disable_auto_start("CourseScheduler")
            
            # 应用debug模式设置
            self.main_app.config_handler.debug_mode = self.debug_var.get()
            
            # 应用自动更新检查设置
            self.main_app.config_handler.auto_update_check_enabled = self.auto_update_check_var.get()
            
            # 应用自动补全结束时间设置
            self.main_app.config_handler.auto_complete_end_time = self.auto_complete_var.get()
            
            # 应用自动计算下一个课程时间设置
            self.main_app.config_handler.auto_calculate_next_course = self.auto_calculate_var.get()
            
            # 应用课间时间设置
            try:
                break_duration = int(self.break_duration_entry.get())
                if break_duration < 0:
                    raise ValueError
                self.main_app.config_handler.break_duration = break_duration
            except ValueError:
                messagebox.showerror("错误", "请输入有效的课间时间")
                return
            
            # 应用默认课表设置
            courses = self.courses_text.get("1.0", tk.END).strip().split("\n")
            self.main_app.config_handler.default_courses = [course for course in courses if course]
            
            # 应用控件大小设置
            try:
                self.main_app.config_handler.time_display_size = max(0, int(self.time_display_size.get() or 0))
                self.main_app.config_handler.countdown_size = max(0, int(self.countdown_size.get() or 0))
                self.main_app.config_handler.schedule_size = max(0, int(self.schedule_size.get() or 0))
            except ValueError:
                messagebox.showerror("错误", "请输入有效的正整数")
                return
            
            # 应用透明背景设置
            self.main_app.config_handler.transparent_background = self.transparent_var.get()
            
            # 应用字体设置
            self.main_app.config_handler.font_size = int(self.font_size.get())
            self.main_app.config_handler.font_color = self.font_color
            
            # 应用全屏时间副标题设置
            self.main_app.config_handler.fullscreen_subtitle = self.fullscreen_subtitle_entry.get()
            
            # 保存和风天气API Key
            self.main_app.config_handler.heweather_api_key = self.heweather_key_entry.get()
            
            # 保存课表轮换设置
            self.main_app.config_handler.schedule_rotation_enabled = self.rotation_var.get()
            self.main_app.config_handler.rotation_schedule1 = self.schedule1_var.get()
            self.main_app.config_handler.rotation_schedule2 = self.schedule2_var.get()
            
            # 应用日志保留天数设置
            try:
                log_retention_days = int(self.log_retention_days_entry.get())
                if log_retention_days <= 0:
                    raise ValueError
                self.main_app.config_handler.log_retention_days = log_retention_days
            except ValueError:
                messagebox.showerror("错误", "请输入有效的日志保留天数（正整数）")
                return
            
            self.main_app.config_handler.save_config()
            # 更新字体设置
            self.main_app._update_font_settings()
            
            # 检查排版设置是否修改
            new_layout = {
                'horizontal_padding': self.main_app.config_handler.horizontal_padding,
                'vertical_padding': self.main_app.config_handler.vertical_padding,
                'time_display_size': self.main_app.config_handler.time_display_size,
                'countdown_size': self.main_app.config_handler.countdown_size,
                'schedule_size': self.main_app.config_handler.schedule_size,
                'font_size': self.main_app.config_handler.font_size,
                'font_color': self.main_app.config_handler.font_color
            }
            
            if new_layout != old_layout:
                if messagebox.askyesno("提示", "部分排版设置需要重启程序才能生效，是否立即重启？"):
                    self.restart_ui(open_settings=True)
            else:
                messagebox.showinfo("成功", "设置已保存")
        except Exception as e:
            logger.log_error(e)
            messagebox.showerror("错误", "保存设置时发生错误")
        finally:
            self.applying = False  # 重置标志位

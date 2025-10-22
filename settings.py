import tkinter as tk
from tkinter import ttk
import sys
from tkinter import messagebox, colorchooser, simpledialog
from datetime import datetime
from constants import DEFAULT_GEOMETRY, CONFIG_FILE, APP_NAME, AUTHOR, VERSION, PROJECT_URL
from about_window import AboutWindow
from logger import logger


class ScrollableFrame(ttk.Frame):
    """可用于Notebook标签页的滚动框架"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮滚动
        self.scrollable_frame.bind("<Enter>", self._on_enter)
        self.scrollable_frame.bind("<Leave>", self._on_leave)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_enter(self, event):
        self.scrollable_frame.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_leave(self, event):
        self.scrollable_frame.unbind_all("<MouseWheel>")


class SettingsWindow:
    def __init__(self, main_app):
        """初始化设置窗口"""
        try:
            self.main_app = main_app
            self.window = self._create_window()
            self.applying = False
            self._initialize_ui()
            self._load_config_into_ui() # 加载初始配置
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
                           padding=5,
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
        self.style.configure("White.TRadiobutton",
                           background="white",
                           font=("微软雅黑", 12))
        self.style.map("White.TRadiobutton",
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
        
        # 为DPI感知模式定义一个特殊的按钮样式
        if self.main_app.config_handler.experimental_dpi_awareness:
            self.style.configure("DPI.TButton", font=("微软雅黑", 14), padding=12, width=15)
        else:
            self.style.configure("DPI.TButton", font=("微软雅黑", 12), padding=10, width=15)
        
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
        self._create_ui_settings_tab()
        self._create_course_tab()
        self._create_theme_tab()
        self._create_tools_tab()
        self._create_other_tab()
        self._create_backup_restore_tab()

        # 在Notebook下方创建操作按钮
        # 在Notebook下方创建配置管理和操作按钮
        self._create_config_selector(main_frame)

        button_frame = ttk.Frame(main_frame, style="TFrame")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text="应用",
            command=self.apply_settings,
            style="DPI.TButton"
        ).pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
        
        ttk.Button(
            button_frame,
            text="重启程序",
            command=self.restart_ui,
            style="DPI.TButton"
        ).pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
    
    def _create_config_selector(self, parent):
        """创建配置选择和管理控件"""
        selector_frame = ttk.Frame(parent, style="TFrame")
        selector_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(selector_frame, text="当前配置:", bg="white").pack(side=tk.LEFT, padx=(0, 5))

        self.config_var = tk.StringVar(value=self.main_app.config_handler.config.get("current_config"))
        self.config_combobox = ttk.Combobox(
            selector_frame,
            textvariable=self.config_var,
            state="readonly"
        )
        self.config_combobox['values'] = self.main_app.config_handler.get_config_names()
        self.config_combobox.pack(side=tk.LEFT, padx=5)

        # 添加新配置按钮
        ttk.Button(selector_frame, text="+", command=self._add_new_config, style="PMSmall.TButton").pack(side=tk.LEFT, padx=5)
        
        # 添加复制配置按钮
        ttk.Button(selector_frame, text="⧉", command=self._copy_config, style="PMSmall.TButton").pack(side=tk.LEFT, padx=5)
        
        # 添加重命名按钮
        ttk.Button(selector_frame, text="✎", command=self._rename_config, style="PMSmall.TButton").pack(side=tk.LEFT, padx=5)
        
        # 添加删除配置按钮
        ttk.Button(selector_frame, text="-", command=self._delete_config, style="PMSmall.TButton").pack(side=tk.LEFT, padx=5)

        # 绑定配置切换事件
        self.config_combobox.bind("<<ComboboxSelected>>", self._on_config_change)
        
    def _create_ui_settings_tab(self) -> None:
        """创建界面设置标签页"""
        scrollable_tab = ScrollableFrame(self.notebook)
        self.notebook.add(scrollable_tab, text="界面设置")
        ui_frame = scrollable_tab.scrollable_frame

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

        # 窗口位置控制
        pos_frame = ttk.LabelFrame(ui_frame, text="窗口位置", style="TFrame")
        pos_frame.pack(fill=tk.X, padx=10, pady=5)
        
        create_button(pos_frame, "←", -10, 0)
        create_button(pos_frame, "→", 10, 0)
        create_button(pos_frame, "↑", 0, -10)
        create_button(pos_frame, "↓", 0, 10)

        # 窗口大小控制
        size_frame = ttk.LabelFrame(ui_frame, text="窗口大小", style="TFrame")
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
            
        # ========== 控件大小设置 ==========
        control_size_frame = ttk.LabelFrame(ui_frame, text="控件大小", style="TFrame")
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
        padding_frame = ttk.LabelFrame(ui_frame, text="间距设置", style="TFrame")
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

    def _create_course_tab(self) -> None:
        """创建课程设置标签页"""
        scrollable_tab = ScrollableFrame(self.notebook)
        self.notebook.add(scrollable_tab, text="课程设置")
        course_frame = scrollable_tab.scrollable_frame
        
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

        # 预览设置
        preview_frame = ttk.LabelFrame(course_frame, text="预览设置", style="TFrame")
        preview_frame.pack(fill=tk.X, padx=10, pady=5)
        self.auto_preview_tomorrow_var = tk.BooleanVar(value=self.main_app.config_handler.auto_preview_tomorrow_enabled)
        self.auto_preview_tomorrow_check = ttk.Checkbutton(
            preview_frame, text="结束后自动预览明天课表",
            variable=self.auto_preview_tomorrow_var,
            style="White.TCheckbutton")
        self.auto_preview_tomorrow_check.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky=tk.W)

        # 第N节课后预览
        ttk.Label(preview_frame, text="第N节课后预览 (0为全结束后):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.preview_trigger_count_var = tk.StringVar(value=self.main_app.config_handler.preview_tomorrow_trigger_count)
        self.preview_trigger_count_entry = ttk.Entry(preview_frame, width=5, textvariable=self.preview_trigger_count_var)
        self.preview_trigger_count_entry.grid(row=1, column=1, padx=5, pady=5)

        # 减按钮
        ttk.Button(
            preview_frame,
            text="-",
            style="PMSmall.TButton",
            command=lambda: self.preview_trigger_count_var.set(max(0, int(self.preview_trigger_count_var.get() or 0) - 1))
        ).grid(row=1, column=2, padx=(5,0), pady=5)
        
        # 加按钮
        ttk.Button(
            preview_frame,
            text="+",
            style="PMSmall.TButton",
            command=lambda: self.preview_trigger_count_var.set(int(self.preview_trigger_count_var.get() or 0) + 1)
        ).grid(row=1, column=3, padx=(0,5), pady=5)

        # 当前课程时间显示设置
        display_mode_frame = ttk.LabelFrame(course_frame, text="当前课程时间显示设置", style="TFrame")
        display_mode_frame.pack(fill=tk.X, padx=10, pady=5)

        self.course_time_display_mode_var = tk.StringVar(value=self.main_app.config_handler.current_course_time_display_mode)
        
        modes = [("默认", "default"), ("结束时间", "end_time"), ("倒计时", "countdown")]
        for i, (text, mode) in enumerate(modes):
            ttk.Radiobutton(
                display_mode_frame,
                text=text,
                variable=self.course_time_display_mode_var,
                value=mode,
                style="White.TRadiobutton"
            ).grid(row=0, column=i, padx=5, pady=5, sticky=tk.W)

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
        scrollable_tab = ScrollableFrame(self.notebook)
        self.notebook.add(scrollable_tab, text="主题设置")
        theme_frame = scrollable_tab.scrollable_frame
        
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
                text_color = self._get_contrasting_color(color)
                self.color_preview.config(bg=color, fg=text_color)
        
        self.font_color = self.main_app.config_handler.font_color
        initial_text_color = self._get_contrasting_color(self.font_color)
        self.color_preview = tk.Label(font_frame, text="颜色",
                                      background=self.font_color,
                                      foreground=initial_text_color,
                                      width=5)
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
        scrollable_tab = ScrollableFrame(self.notebook)
        self.notebook.add(scrollable_tab, text="小工具")
        tools_frame = scrollable_tab.scrollable_frame
        
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

        # 天气API提供商选择
        ttk.Label(weather_frame, text="天气数据源:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.weather_provider_var = tk.StringVar(value=self.main_app.config_handler.weather_api_provider)
        
        heweather_radio = ttk.Radiobutton(
            weather_frame, text="和风天气", variable=self.weather_provider_var,
            value="heweather", command=self._on_provider_change, style="White.TRadiobutton"
        )
        heweather_radio.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        timer7_radio = ttk.Radiobutton(
            weather_frame, text="7Timer!", variable=self.weather_provider_var,
            value="7timer", command=self._on_provider_change, style="White.TRadiobutton"
        )
        timer7_radio.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # 和风天气API Key输入框 (根据选择动态显示)
        self.heweather_key_label = ttk.Label(weather_frame, text="和风天气API Key:")
        self.heweather_key_entry = ttk.Entry(weather_frame, width=35)
        self.heweather_key_entry.insert(0, self.main_app.config_handler.heweather_api_key)

        self._on_provider_change() # 初始化显隐状态

        # AI助手设置
        ai_frame = ttk.LabelFrame(tools_frame, text="AI助手设置", style="TFrame")
        ai_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(ai_frame, text="Base URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ai_base_url_entry = ttk.Entry(ai_frame, width=35)
        self.ai_base_url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.ai_base_url_entry.insert(0, self.main_app.config_handler.ai_assistant_base_url)

        ttk.Label(ai_frame, text="API Key:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ai_api_key_entry = ttk.Entry(ai_frame, width=35, show="*")
        self.ai_api_key_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.ai_api_key_entry.insert(0, self.main_app.config_handler.ai_assistant_api_key)

        ttk.Label(ai_frame, text="模型名称:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.ai_model_name_entry = ttk.Entry(ai_frame, width=35)
        self.ai_model_name_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.ai_model_name_entry.insert(0, self.main_app.config_handler.ai_assistant_model_name)

    def _create_other_tab(self) -> None:
        """创建其他设置标签页"""
        scrollable_tab = ScrollableFrame(self.notebook)
        self.notebook.add(scrollable_tab, text="其他设置")
        other_frame = scrollable_tab.scrollable_frame
        
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

        # 实验性功能
        experimental_frame = ttk.LabelFrame(other_frame, text="实验性功能", style="TFrame")
        experimental_frame.pack(fill=tk.X, padx=10, pady=5)

        self.dpi_awareness_var = tk.BooleanVar(value=self.main_app.config_handler.experimental_dpi_awareness)
        self.dpi_awareness_check = ttk.Checkbutton(
            experimental_frame, text="启用实验性DPI感知 (需要重启)",
            variable=self.dpi_awareness_var,
            style="White.TCheckbutton")
        self.dpi_awareness_check.pack(side=tk.LEFT, padx=5)

    def _create_backup_restore_tab(self) -> None:
        """创建备份与还原标签页"""
        scrollable_tab = ScrollableFrame(self.notebook)
        self.notebook.add(scrollable_tab, text="备份与还原")
        backup_frame = scrollable_tab.scrollable_frame

        # --- 导出区域 ---
        export_frame = ttk.LabelFrame(backup_frame, text="导出数据")
        export_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)

        ttk.Label(export_frame, text="选择要导出的配置:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.config_listbox = tk.Listbox(export_frame, selectmode=tk.MULTIPLE, height=5, bg="white", highlightthickness=0)
        for config_name in self.main_app.config_handler.get_config_names():
            self.config_listbox.insert(tk.END, config_name)
        self.config_listbox.pack(fill=tk.X, expand=True, padx=5, pady=2)

        self.include_schedule_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            export_frame,
            text="同时导出课表数据",
            variable=self.include_schedule_var,
            style="White.TCheckbutton"
        ).pack(anchor=tk.W, padx=5, pady=5)

        ttk.Button(
            export_frame,
            text="导出...",
            command=self._handle_export,
            style="TButton"
        ).pack(pady=5)

        # --- 导入区域 ---
        import_frame = ttk.LabelFrame(backup_frame, text="导入数据")
        import_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)

        self.import_mode_var = tk.StringVar(value="incremental")
        
        ttk.Radiobutton(
            import_frame,
            text="增量导入 (合并数据，存在则覆盖)",
            variable=self.import_mode_var,
            value="incremental",
            style="White.TRadiobutton"
        ).pack(anchor=tk.W, padx=5)

        ttk.Radiobutton(
            import_frame,
            text="覆盖导入 (清空现有数据后导入)",
            variable=self.import_mode_var,
            value="overwrite",
            style="White.TRadiobutton"
        ).pack(anchor=tk.W, padx=5)

        ttk.Button(
            import_frame,
            text="从文件导入...",
            command=self._handle_import,
            style="TButton"
        ).pack(pady=10)

    def _handle_export(self):
        """处理导出按钮点击事件"""
        from backup_restore_manager import BackupRestoreManager
        selected_indices = self.config_listbox.curselection()
        selected_configs = [self.config_listbox.get(i) for i in selected_indices]
        include_schedule = self.include_schedule_var.get()

        if not selected_configs and not include_schedule:
            messagebox.showwarning("未选择", "请至少选择一个配置方案或勾选课表数据进行导出。", parent=self.window)
            return

        manager = BackupRestoreManager(self.main_app)
        manager.export_data(selected_configs, include_schedule)

    def _handle_import(self):
        """处理导入按钮点击事件"""
        from backup_restore_manager import BackupRestoreManager
        mode = self.import_mode_var.get()
        manager = BackupRestoreManager(self.main_app)
        manager.import_data(mode)
        # 导入后，可能需要刷新设置窗口中的某些内容
        self._load_config_into_ui()
        self._update_config_combobox()


    def _get_contrasting_color(self, hex_color):
        """Calculates contrasting text color (black or white) for a given hex background color."""
        try:
            r, g, b = self.window.winfo_rgb(hex_color)
            # Brightness calculation using a common formula (YIQ)
            # If brightness is over half of the max value (65535), use black text.
            brightness = ((r * 299) + (g * 587) + (b * 114)) / 1000
            return 'black' if brightness > 32767 else 'white'
        except tk.TclError:
            # Fallback for invalid color names or during initialization issues
            return 'black'

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
        
        # 更新geometry
        self.main_app.config_handler.geometry = f"{window_width}x{window_height}+{x}+{y}"
        self.main_app.root.geometry(f"+{x}+{y}")
    
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
            'font_color': self.main_app.config_handler.font_color,
            'experimental_dpi_awareness': self.main_app.config_handler.experimental_dpi_awareness
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
            self.main_app.config_handler.weather_api_provider = self.weather_provider_var.get()
            self.main_app.config_handler.heweather_api_key = self.heweather_key_entry.get()

            # 保存AI助手设置
            self.main_app.config_handler.ai_assistant_base_url = self.ai_base_url_entry.get()
            self.main_app.config_handler.ai_assistant_api_key = self.ai_api_key_entry.get()
            self.main_app.config_handler.ai_assistant_model_name = self.ai_model_name_entry.get()
            
            # 保存课表轮换设置
            self.main_app.config_handler.schedule_rotation_enabled = self.rotation_var.get()
            self.main_app.config_handler.rotation_schedule1 = self.schedule1_var.get()
            self.main_app.config_handler.rotation_schedule2 = self.schedule2_var.get()

            # 保存课表轮换设置
            self.main_app.config_handler.schedule_rotation_enabled = self.rotation_var.get()
            self.main_app.config_handler.rotation_schedule1 = self.schedule1_var.get()
            self.main_app.config_handler.rotation_schedule2 = self.schedule2_var.get()

            # 应用当前课程时间显示模式设置
            self.main_app.config_handler.current_course_time_display_mode = self.course_time_display_mode_var.get()

            # 应用预览设置
            self.main_app.config_handler.auto_preview_tomorrow_enabled = self.auto_preview_tomorrow_var.get()
            try:
                trigger_count = int(self.preview_trigger_count_var.get())
                if trigger_count < 0:
                    raise ValueError
                self.main_app.config_handler.preview_tomorrow_trigger_count = trigger_count
            except ValueError:
                messagebox.showerror("错误", "请输入有效的预览触发课程数（非负整数）", parent=self.window)
                return
            
            # 应用日志保留天数设置
            try:
                log_retention_days = int(self.log_retention_days_entry.get())
                if log_retention_days <= 0:
                    raise ValueError
                self.main_app.config_handler.log_retention_days = log_retention_days
            except ValueError:
                messagebox.showerror("错误", "请输入有效的日志保留天数（正整数）")
                return
            
            # 应用DPI感知设置
            self.main_app.config_handler.experimental_dpi_awareness = self.dpi_awareness_var.get()
            
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
                'font_color': self.main_app.config_handler.font_color,
                'experimental_dpi_awareness': self.main_app.config_handler.experimental_dpi_awareness
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

    def _add_new_config(self):
        """添加新配置"""
        new_name = simpledialog.askstring("新配置", "请输入新配置名称:", parent=self.window)
        if new_name and new_name.strip():
            new_name = new_name.strip()
            if self.main_app.config_handler.add_config(new_name):
                self._update_config_combobox(new_name)
                messagebox.showinfo("成功", f"配置 '{new_name}' 已添加", parent=self.window)
            else:
                messagebox.showerror("错误", "该名称已存在", parent=self.window)

    def _copy_config(self):
        """复制当前配置"""
        original_name = self.config_var.get()
        new_name = simpledialog.askstring("复制配置", "请输入新配置的名称:", initialvalue=f"{original_name}_副本", parent=self.window)
        if new_name and new_name != original_name:
            if self.main_app.config_handler.copy_config(original_name, new_name):
                self._update_config_combobox(new_name)
                messagebox.showinfo("成功", "配置已复制", parent=self.window)
            else:
                messagebox.showerror("错误", "复制失败，新名称可能已存在", parent=self.window)

    def _rename_config(self):
        """重命名当前配置"""
        old_name = self.config_var.get()
        new_name = simpledialog.askstring("重命名配置", "请输入新名称:", initialvalue=old_name, parent=self.window)
        if new_name and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            if self.main_app.config_handler.rename_config(old_name, new_name):
                self._update_config_combobox(new_name)
                messagebox.showinfo("成功", "配置已重命名", parent=self.window)
            else:
                messagebox.showerror("错误", "重命名失败，新名称可能已存在", parent=self.window)

    def _delete_config(self):
        """删除当前配置"""
        name_to_delete = self.config_var.get()
        if messagebox.askyesno("确认删除", f"确定要删除配置 '{name_to_delete}' 吗？", parent=self.window):
            if self.main_app.config_handler.delete_config(name_to_delete):
                new_current = self.main_app.config_handler.config.get("current_config")
                self._update_config_combobox(new_current)
                self._load_config_into_ui() # 重新加载新当前配置的UI
                messagebox.showinfo("成功", "配置已删除", parent=self.window)
            else:
                messagebox.showwarning("警告", "无法删除，至少需要保留一个配置", parent=self.window)

    def _on_config_change(self, event=None):
        """处理配置切换事件"""
        new_config_name = self.config_var.get()
        self.main_app.config_handler.switch_config(new_config_name)
        self._load_config_into_ui()

    def _update_config_combobox(self, new_value=None):
        """更新配置下拉框的内容和选定值"""
        self.config_combobox['values'] = self.main_app.config_handler.get_config_names()
        if new_value:
            self.config_combobox.set(new_value)
        else:
            self.config_combobox.set(self.main_app.config_handler.config.get("current_config"))

    def _load_config_into_ui(self):
        """将当前配置加载到整个UI界面"""
        handler = self.main_app.config_handler
        
        # 排版设置
        self.time_display_size.delete(0, tk.END)
        self.time_display_size.insert(0, str(handler.time_display_size))
        self.countdown_size.delete(0, tk.END)
        self.countdown_size.insert(0, str(handler.countdown_size))
        self.schedule_size.delete(0, tk.END)
        self.schedule_size.insert(0, str(handler.schedule_size))
        self.horizontal_padding.delete(0, tk.END)
        self.horizontal_padding.insert(0, str(handler.horizontal_padding))
        self.vertical_padding.delete(0, tk.END)
        self.vertical_padding.insert(0, str(handler.vertical_padding))

        # 窗口控制
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, self.main_app.root.winfo_width())
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, self.main_app.root.winfo_height())

        # 课程设置
        self.duration_entry.delete(0, tk.END)
        self.duration_entry.insert(0, str(handler.course_duration))
        self.auto_complete_var.set(handler.auto_complete_end_time)
        self.auto_calculate_var.set(handler.auto_calculate_next_course)
        self.break_duration_entry.delete(0, tk.END)
        self.break_duration_entry.insert(0, str(handler.break_duration))
        self.auto_preview_tomorrow_var.set(handler.auto_preview_tomorrow_enabled)
        self.preview_trigger_count_var.set(str(handler.preview_tomorrow_trigger_count))
        self.rotation_var.set(handler.schedule_rotation_enabled)
        self.course_time_display_mode_var.set(handler.current_course_time_display_mode)
        self.schedule1_var.set(handler.rotation_schedule1)
        self.schedule2_var.set(handler.rotation_schedule2)
        self.countdown_name_entry.delete(0, tk.END)
        self.countdown_name_entry.insert(0, handler.countdown_name)
        self.countdown_date_entry.delete(0, tk.END)
        self.countdown_date_entry.insert(0, handler.countdown_date.strftime("%Y-%m-%d"))
        self.courses_text.delete("1.0", tk.END)
        self.courses_text.insert(tk.END, "\n".join(handler.default_courses))

        # AI助手设置
        self.ai_base_url_entry.delete(0, tk.END)
        self.ai_base_url_entry.insert(0, handler.ai_assistant_base_url)
        self.ai_api_key_entry.delete(0, tk.END)
        self.ai_api_key_entry.insert(0, handler.ai_assistant_api_key)
        self.ai_model_name_entry.delete(0, tk.END)
        self.ai_model_name_entry.insert(0, handler.ai_assistant_model_name)

        # 其他设置
        self.auto_start_var.set(handler.auto_start)
        self.debug_var.set(handler.debug_mode)
        self.auto_update_check_var.set(handler.auto_update_check_enabled)
        self.log_retention_days_entry.delete(0, tk.END)
        self.log_retention_days_entry.insert(0, str(handler.log_retention_days))
        self.dpi_awareness_var.set(handler.experimental_dpi_awareness)

    def _on_provider_change(self):
        """根据选择的天气API提供商，显示或隐藏API Key输入框"""
        if self.weather_provider_var.get() == "heweather":
            self.heweather_key_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
            self.heweather_key_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        else:
            self.heweather_key_label.grid_remove()
            self.heweather_key_entry.grid_remove()


class DpiDebugWindow:
    """一个用于调试DPI设置的小窗口"""
    def __init__(self, main_app):
        self.main_app = main_app
        self.window = tk.Toplevel()
        self.window.title("DPI调试")
        self.window.geometry("350x450")
        self.window.resizable(False, False)
        self.window.configure(bg="white")

        self.style = ttk.Style()
        self.style.configure("DPI.TLabel", background="white", font=("微软雅黑", 10))
        self.style.configure("DPI.TButton", font=("微软雅黑", 10), padding=5)
        self.style.configure("DPI.TFrame", background="white")
        self.style.configure("DPI.TRadiobutton", background="white", font=("微软雅黑", 10))

        self._initialize_ui()

    def _initialize_ui(self):
        main_frame = ttk.Frame(self.window, style="DPI.TFrame")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self._create_position_controls(main_frame)
        self._create_size_controls(main_frame)
        self._create_dpi_controls(main_frame)

    def _create_dpi_controls(self, parent):
        dpi_frame = ttk.LabelFrame(parent, text="DPI感知模式", style="DPI.TFrame")
        dpi_frame.pack(fill=tk.X, padx=5, pady=5)

        self.dpi_awareness_var = tk.BooleanVar(value=self.main_app.config_handler.experimental_dpi_awareness)

        ttk.Checkbutton(
            dpi_frame,
            text="启用实验性DPI感知",
            variable=self.dpi_awareness_var,
            style="DPI.TRadiobutton",
            command=self._on_dpi_change
        ).pack(anchor=tk.W, padx=5)

    def _on_dpi_change(self):
        new_value = self.dpi_awareness_var.get()
        if new_value != self.main_app.config_handler.experimental_dpi_awareness:
            self.main_app.config_handler.experimental_dpi_awareness = new_value
            self.main_app.config_handler.save_config()
            messagebox.showinfo("需要重启", "DPI感知模式设置已更改，需要重启程序才能生效。", parent=self.window)

    def _create_position_controls(self, parent):
        pos_frame = ttk.LabelFrame(parent, text="主窗口位置", style="DPI.TFrame")
        pos_frame.pack(fill=tk.X, padx=5, pady=5)

        button_frame = ttk.Frame(pos_frame, style="DPI.TFrame")
        button_frame.pack()

        self._create_move_button(button_frame, "↑", 0, -10)
        self._create_move_button(button_frame, "←", -10, 0)
        self._create_move_button(button_frame, "→", 10, 0)
        self._create_move_button(button_frame, "↓", 0, 10)

    def _create_size_controls(self, parent):
        size_frame = ttk.LabelFrame(parent, text="主窗口大小", style="DPI.TFrame")
        size_frame.pack(fill=tk.X, padx=5, pady=5)

        # 宽度
        width_frame = ttk.Frame(size_frame, style="DPI.TFrame")
        width_frame.pack(fill=tk.X)
        ttk.Label(width_frame, text="宽度:", style="DPI.TLabel").pack(side=tk.LEFT, padx=5)
        self.width_var = tk.StringVar(value=self.main_app.root.winfo_width())
        width_entry = ttk.Entry(width_frame, textvariable=self.width_var, width=7)
        width_entry.pack(side=tk.LEFT, padx=5)
        width_entry.bind("<Return>", self._apply_size)
        self._create_spin_buttons(width_frame, self.width_var, 10)

        # 高度
        height_frame = ttk.Frame(size_frame, style="DPI.TFrame")
        height_frame.pack(fill=tk.X)
        ttk.Label(height_frame, text="高度:", style="DPI.TLabel").pack(side=tk.LEFT, padx=5)
        self.height_var = tk.StringVar(value=self.main_app.root.winfo_height())
        height_entry = ttk.Entry(height_frame, textvariable=self.height_var, width=7)
        height_entry.pack(side=tk.LEFT, padx=5)
        height_entry.bind("<Return>", self._apply_size)
        self._create_spin_buttons(height_frame, self.height_var, 10)

    def _create_move_button(self, parent, text, dx, dy):
        button = ttk.Button(parent, text=text, width=3, style="DPI.TButton")
        button.pack(side=tk.LEFT, padx=5, pady=5)

        def start_move(event=None):
            self._move_window(dx, dy)
            button.after_id = button.after(100, start_move)

        def stop_move(event=None):
            if hasattr(button, 'after_id'):
                button.after_cancel(button.after_id)

        button.bind("<ButtonPress-1>", start_move)
        button.bind("<ButtonRelease-1>", stop_move)

    def _create_spin_buttons(self, parent, var, step):
        ttk.Button(parent, text="-", width=2, style="DPI.TButton", command=lambda: self._adjust_var(var, -step)).pack(side=tk.LEFT, padx=2)
        ttk.Button(parent, text="+", width=2, style="DPI.TButton", command=lambda: self._adjust_var(var, step)).pack(side=tk.LEFT, padx=2)

    def _adjust_var(self, var, amount):
        try:
            current_value = int(var.get())
            var.set(str(current_value + amount))
            self._apply_size()
        except ValueError:
            pass

    def _move_window(self, dx, dy):
        try:
            root = self.main_app.root
            new_x = root.winfo_x() + dx
            new_y = root.winfo_y() + dy
            root.geometry(f"+{new_x}+{new_y}")
        except Exception as e:
            logger.log_error(f"移动窗口时出错: {e}")

    def _apply_size(self, event=None):
        try:
            root = self.main_app.root
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            root.geometry(f"{width}x{height}")
        except (ValueError, tk.TclError) as e:
            logger.log_error(f"应用窗口大小时出错: {e}")
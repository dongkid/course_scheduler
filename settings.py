import tkinter as tk
from tkinter import messagebox
from constants import DEFAULT_GEOMETRY, CONFIG_FILE, APP_NAME, AUTHOR, VERSION, PROJECT_URL
from about_window import AboutWindow
from logger import logger

class SettingsWindow:
    def __init__(self, main_app):
        """初始化设置窗口"""
        try:
            self.main_app = main_app
            self.window = self._create_window()
            self._initialize_ui()
        except Exception as e:
            logger.log_error(e)
            raise

    def _create_window(self) -> tk.Toplevel:
        """创建并配置设置窗口"""
        window = tk.Toplevel()
        window.title("设置")
        window.minsize(650, 450)
        return window

    def _initialize_ui(self) -> None:
        """初始化设置界面"""
        # 配置网格布局权重
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_rowconfigure(2, weight=1)
        self.window.grid_rowconfigure(3, weight=1)
        self.window.grid_rowconfigure(4, weight=1)
        
        # 第一行：窗口控制
        control_frame = tk.LabelFrame(self.window, text="窗口控制")
        control_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        self._create_position_controls(control_frame)
        self._create_size_controls(control_frame)
        
        # 第二行：课程设置
        course_frame = tk.LabelFrame(self.window, text="课程设置")
        course_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        self._create_course_duration_controls(course_frame)
        
        # 第三行：倒计时与默认课表
        gaokao_frame = tk.LabelFrame(self.window, text="倒计时与默认课表")
        gaokao_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
        self._create_gaokao_controls(gaokao_frame)
        self._create_default_courses_controls(gaokao_frame)
        
        # 第四行：字体设置
        self._create_font_controls()
        
        # 第五行：开机自启动
        self._create_auto_start_controls()
        
        # 底部：操作按钮
        self._create_action_buttons()

    def _create_auto_start_controls(self) -> None:
        """创建开机自启动设置"""
        auto_start_frame = tk.LabelFrame(self.window, text="开机自启动")
        auto_start_frame.grid(row=3, column=1, padx=15, pady=15, sticky='nsew')
        
        self.auto_start_var = tk.BooleanVar(value=self.main_app.config_handler.auto_start)
        self.auto_start_check = tk.Checkbutton(
            auto_start_frame, text="开机时自动启动程序",
            variable=self.auto_start_var)
        self.auto_start_check.pack(side=tk.LEFT, padx=5)

    def _create_course_duration_controls(self, parent) -> None:
        """创建课程时长设置"""
        duration_frame = tk.LabelFrame(parent, text="课程时长设置")
        duration_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 课程时长设置
        tk.Label(duration_frame, text="课程时长（分钟）:").pack(side=tk.LEFT)
        self.duration_entry = tk.Entry(duration_frame, width=5)
        self.duration_entry.pack(side=tk.LEFT, padx=2)
        self.duration_entry.insert(0, str(self.main_app.config_handler.course_duration))

        # 自动补全结束时间
        self.auto_complete_var = tk.BooleanVar(value=self.main_app.config_handler.auto_complete_end_time)
        self.auto_complete_check = tk.Checkbutton(
            duration_frame, text="自动补全结束时间",
            variable=self.auto_complete_var)
        self.auto_complete_check.pack(side=tk.LEFT, padx=5)

        # 自动计算下一个课程时间
        self.auto_calculate_var = tk.BooleanVar(value=self.main_app.config_handler.auto_calculate_next_course)
        self.auto_calculate_check = tk.Checkbutton(
            duration_frame, text="自动计算下一个课程时间",
            variable=self.auto_calculate_var)
        self.auto_calculate_check.pack(side=tk.LEFT, padx=5)

        # 课间时间设置
        tk.Label(duration_frame, text="课间时间（分钟）:").pack(side=tk.LEFT)
        self.break_duration_entry = tk.Entry(duration_frame, width=5)
        self.break_duration_entry.pack(side=tk.LEFT, padx=2)
        self.break_duration_entry.insert(0, str(self.main_app.config_handler.break_duration))

    def _create_position_controls(self, parent) -> None:
        """创建窗口位置控制"""
        pos_frame = tk.LabelFrame(parent, text="窗口位置")
        pos_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        def create_button(frame, text, dx, dy):
            button = tk.Button(frame, text=text, width=5, height=2)
            button.pack(side=tk.LEFT, padx=5, pady=5)
            
            def start_move():
                self.move_window(dx, dy)
                # 初始延迟100ms，每次减少5ms，最小延迟20ms
                current_delay = getattr(button, 'current_delay', 100)
                new_delay = max(10, current_delay - 5)
                button.current_delay = new_delay
                button.after_id = button.after(new_delay, start_move)
            
            def stop_move():
                if hasattr(button, 'after_id'):
                    button.after_cancel(button.after_id)
                    del button.after_id
                # 重置延迟时间
                if hasattr(button, 'current_delay'):
                    del button.current_delay
            
            button.bind("<ButtonPress-1>", lambda e: start_move())
            button.bind("<ButtonRelease-1>", lambda e: stop_move())
            return button
        
        create_button(pos_frame, "←", -10, 0)
        create_button(pos_frame, "→", 10, 0)
        create_button(pos_frame, "↑", 0, -10)
        create_button(pos_frame, "↓", 0, 10)

    def _create_size_controls(self, parent) -> None:
        """创建窗口大小控制"""
        size_frame = tk.LabelFrame(parent, text="窗口大小")
        size_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        tk.Label(size_frame, text="宽度:").pack(side=tk.LEFT)
        self.width_entry = tk.Entry(size_frame, width=5)
        self.width_entry.pack(side=tk.LEFT, padx=2)
        self.width_entry.insert(0, self.main_app.root.winfo_width())
        
        tk.Label(size_frame, text="高度:").pack(side=tk.LEFT)
        self.height_entry = tk.Entry(size_frame, width=5)
        self.height_entry.pack(side=tk.LEFT, padx=2)
        self.height_entry.insert(0, self.main_app.root.winfo_height())

    def _create_gaokao_controls(self, parent) -> None:
        """创建高考设置控制"""
        gaokao_frame = tk.LabelFrame(parent, text="高考设置")
        gaokao_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        tk.Label(gaokao_frame, text="高考年份:").pack(side=tk.LEFT, padx=5)
        self.gaokao_entry = tk.Entry(gaokao_frame, width=10)
        self.gaokao_entry.pack(side=tk.LEFT, padx=5)
        self.gaokao_entry.insert(0, str(self.main_app.config_handler.gaokao_year))

    def _create_default_courses_controls(self, parent) -> None:
        """创建默认课表设置"""
        courses_frame = tk.LabelFrame(parent, text="默认课表设置")
        courses_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.courses_text = tk.Text(courses_frame, height=5, width=30)
        self.courses_text.pack(padx=5, pady=5)
        self.courses_text.insert(tk.END, "\n".join(self.main_app.config_handler.default_courses))
        
        tk.Label(courses_frame, text="每行一个课程名称").pack()

    def _create_font_controls(self) -> None:
        """创建字体设置控件"""
        font_frame = tk.LabelFrame(self.window, text="字体设置")
        font_frame.grid(row=3, column=0, padx=10, pady=10, sticky='nsew')
        
        # 字体大小设置
        tk.Label(font_frame, text="字体大小:").pack(side=tk.LEFT, padx=5)
        self.font_size = tk.Scale(font_frame, from_=8, to=32, orient=tk.HORIZONTAL)
        self.font_size.set(self.main_app.config_handler.font_size)
        self.font_size.pack(side=tk.LEFT, padx=5)
        
        # 字体颜色设置
        def choose_color():
            color = tk.colorchooser.askcolor()[1]
            if color:
                self.font_color = color
                self.color_preview.config(bg=color)
        
        self.font_color = self.main_app.config_handler.font_color
        self.color_preview = tk.Label(font_frame, text="颜色", bg=self.font_color, width=5)
        self.color_preview.pack(side=tk.LEFT, padx=5)
        tk.Button(font_frame, text="选择颜色", command=choose_color).pack(side=tk.LEFT, padx=5)

    def _create_action_buttons(self) -> None:
        """创建操作按钮"""
        button_frame = tk.Frame(self.window)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20, padx=15)
        
        tk.Button(button_frame, text="应用", command=self.apply_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="关于", command=self._show_about).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="重启界面", command=self.restart_ui).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="退出程序", command=self.main_app.root.quit).pack(side=tk.LEFT, padx=5)

    def restart_ui(self) -> None:
        """重启主界面"""
        # 销毁现有界面组件
        for widget in self.main_app.root.winfo_children():
            widget.destroy()
        
        # 重新初始化界面
        self.main_app._initialize_ui()
        messagebox.showinfo("成功", "主界面已重启")

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
        
        self.main_app.root.geometry(f"+{x}+{y}")
        self.main_app.config_handler.save_config()
    
    def apply_settings(self):
        try:
            # 应用窗口大小设置
            try:
                width = int(self.width_entry.get())
                height = int(self.height_entry.get())
                if width < 100 or height < 100:
                    raise ValueError
                x = self.main_app.root.winfo_x()
                y = self.main_app.root.winfo_y()
                self.main_app.root.geometry(f"{width}x{height}+{x}+{y}")
                self.main_app.root.update()
                self.main_app._adjust_ui_layout()
                self.main_app.root.update_idletasks()
                # 更新输入框中的值
                self.width_entry.delete(0, tk.END)
                self.width_entry.insert(0, str(width))
                self.height_entry.delete(0, tk.END)
                self.height_entry.insert(0, str(height))
            except:
                messagebox.showerror("错误", "请输入有效的窗口尺寸")
                return
            
            # 应用高考年份设置
            try:
                self.main_app.config_handler.gaokao_year = int(self.gaokao_entry.get())
            except ValueError:
                messagebox.showerror("错误", "请输入有效的年份")
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
                enable_auto_start("CourseScheduler", sys.executable)
            else:
                from auto_start import disable_auto_start
                disable_auto_start("CourseScheduler")
            
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
            
            # 应用字体设置
            self.main_app.config_handler.font_size = self.font_size.get()
            self.main_app.config_handler.font_color = self.font_color
            
            self.main_app.config_handler.save_config()
            messagebox.showinfo("成功", "设置已保存")
        except Exception as e:
            logger.log_error(e)
            messagebox.showerror("错误", "保存设置时发生错误")

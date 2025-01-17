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
        # 创建Notebook组件
        self.notebook = tk.ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建各个设置标签页
        self._create_layout_tab()
        self._create_window_tab()
        self._create_course_tab()
        self._create_theme_tab()
        self._create_other_tab()

        # 在Notebook下方创建操作按钮
        button_frame = tk.Frame(self.window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_frame, text="应用", command=self.apply_settings).pack(side=tk.TOP, pady=10)
        
    def _create_layout_tab(self) -> None:
        """创建排版设置标签页"""
        layout_frame = tk.Frame(self.notebook)
        self.notebook.add(layout_frame, text="排版设置")
        
        # 控件大小设置
        control_size_frame = tk.LabelFrame(layout_frame, text="控件大小")
        control_size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 时间显示控件大小
        tk.Label(control_size_frame, text="时间显示大小:").grid(row=0, column=0, padx=5, pady=5)
        self.time_display_size = tk.Entry(control_size_frame, width=5)
        self.time_display_size.grid(row=0, column=1, padx=5, pady=5)
        self.time_display_size.insert(0, str(self.main_app.config_handler.time_display_size))
        
        # 倒计时控件大小
        tk.Label(control_size_frame, text="倒计时大小:").grid(row=1, column=0, padx=5, pady=5)
        self.countdown_size = tk.Entry(control_size_frame, width=5)
        self.countdown_size.grid(row=1, column=1, padx=5, pady=5)
        self.countdown_size.insert(0, str(self.main_app.config_handler.countdown_size))
        
        # 课程表控件大小
        tk.Label(control_size_frame, text="课程表大小:").grid(row=2, column=0, padx=5, pady=5)
        self.schedule_size = tk.Entry(control_size_frame, width=5)
        self.schedule_size.grid(row=2, column=1, padx=5, pady=5)
        self.schedule_size.insert(0, str(self.main_app.config_handler.schedule_size))
        
        # 间距设置
        padding_frame = tk.LabelFrame(layout_frame, text="间距设置")
        padding_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 水平间距设置
        tk.Label(padding_frame, text="水平间距:").grid(row=0, column=0, padx=5, pady=5)
        self.horizontal_padding = tk.Entry(padding_frame, width=5)
        self.horizontal_padding.grid(row=0, column=1, padx=5, pady=5)
        self.horizontal_padding.insert(0, str(self.main_app.config_handler.horizontal_padding))
        
        # 垂直间距设置
        tk.Label(padding_frame, text="垂直间距:").grid(row=1, column=0, padx=5, pady=5)
        self.vertical_padding = tk.Entry(padding_frame, width=5)
        self.vertical_padding.grid(row=1, column=1, padx=5, pady=5)
        self.vertical_padding.insert(0, str(self.main_app.config_handler.vertical_padding))

    def _create_window_tab(self) -> None:
        """创建窗口控制标签页"""
        window_frame = tk.Frame(self.notebook)
        self.notebook.add(window_frame, text="窗口控制")
        
        # 窗口位置控制
        pos_frame = tk.LabelFrame(window_frame, text="窗口位置")
        pos_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def create_button(frame, text, dx, dy):
            button = tk.Button(frame, text=text, width=5, height=2)
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
        size_frame = tk.LabelFrame(window_frame, text="窗口大小")
        size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(size_frame, text="宽度:").grid(row=0, column=0, padx=5, pady=5)
        self.width_entry = tk.Entry(size_frame, width=5)
        self.width_entry.grid(row=0, column=1, padx=5, pady=5)
        self.width_entry.insert(0, self.main_app.root.winfo_width())
        
        tk.Label(size_frame, text="高度:").grid(row=1, column=0, padx=5, pady=5)
        self.height_entry = tk.Entry(size_frame, width=5)
        self.height_entry.grid(row=1, column=1, padx=5, pady=5)
        self.height_entry.insert(0, self.main_app.root.winfo_height())

    def _create_course_tab(self) -> None:
        """创建课程设置标签页"""
        course_frame = tk.Frame(self.notebook)
        self.notebook.add(course_frame, text="课程设置")
        
        # 课程时长设置
        duration_frame = tk.LabelFrame(course_frame, text="课程时长设置")
        duration_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(duration_frame, text="课程时长（分钟）:").grid(row=0, column=0, padx=5, pady=5)
        self.duration_entry = tk.Entry(duration_frame, width=5)
        self.duration_entry.grid(row=0, column=1, padx=5, pady=5)
        self.duration_entry.insert(0, str(self.main_app.config_handler.course_duration))
        
        # 自动补全结束时间
        self.auto_complete_var = tk.BooleanVar(value=self.main_app.config_handler.auto_complete_end_time)
        self.auto_complete_check = tk.Checkbutton(
            duration_frame, text="自动补全结束时间",
            variable=self.auto_complete_var)
        self.auto_complete_check.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # 自动计算下一个课程时间
        self.auto_calculate_var = tk.BooleanVar(value=self.main_app.config_handler.auto_calculate_next_course)
        self.auto_calculate_check = tk.Checkbutton(
            duration_frame, text="自动计算下一个课程时间",
            variable=self.auto_calculate_var)
        self.auto_calculate_check.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        # 课间时间设置
        tk.Label(duration_frame, text="课间时间（分钟）:").grid(row=3, column=0, padx=5, pady=5)
        self.break_duration_entry = tk.Entry(duration_frame, width=5)
        self.break_duration_entry.grid(row=3, column=1, padx=5, pady=5)
        self.break_duration_entry.insert(0, str(self.main_app.config_handler.break_duration))

        # 倒计时与默认课表设置
        gaokao_frame = tk.LabelFrame(course_frame, text="倒计时与默认课表")
        gaokao_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 倒计时设置
        countdown_frame = tk.LabelFrame(gaokao_frame, text="倒计时设置")
        countdown_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(countdown_frame, text="倒计时名称:").grid(row=0, column=0, padx=5, pady=5)
        self.countdown_name_entry = tk.Entry(countdown_frame, width=10)
        self.countdown_name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.countdown_name_entry.insert(0, self.main_app.config_handler.countdown_name)
        
        tk.Label(countdown_frame, text="倒计时日期:").grid(row=1, column=0, padx=5, pady=5)
        self.countdown_date_entry = tk.Entry(countdown_frame, width=10)
        self.countdown_date_entry.grid(row=1, column=1, padx=5, pady=5)
        self.countdown_date_entry.insert(0, self.main_app.config_handler.countdown_date.strftime("%Y-%m-%d"))

        # 默认课表设置
        courses_frame = tk.LabelFrame(gaokao_frame, text="默认课表设置")
        courses_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.courses_text = tk.Text(courses_frame, height=5, width=30)
        self.courses_text.pack(padx=5, pady=5)
        self.courses_text.insert(tk.END, "\n".join(self.main_app.config_handler.default_courses))
        
        tk.Label(courses_frame, text="每行一个课程名称").pack()

    def _create_theme_tab(self) -> None:
        """创建主题设置标签页"""
        theme_frame = tk.Frame(self.notebook)
        self.notebook.add(theme_frame, text="主题设置")
        
        # 字体设置
        font_frame = tk.LabelFrame(theme_frame, text="字体设置")
        font_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 字体大小设置
        tk.Label(font_frame, text="字体大小:").grid(row=0, column=0, padx=5, pady=5)
        self.font_size = tk.Scale(font_frame, from_=8, to=32, orient=tk.HORIZONTAL)
        self.font_size.set(self.main_app.config_handler.font_size)
        self.font_size.grid(row=0, column=1, padx=5, pady=5)
        
        # 字体颜色设置
        def choose_color():
            color = tk.colorchooser.askcolor()[1]
            if color:
                self.font_color = color
                self.color_preview.config(bg=color)
        
        self.font_color = self.main_app.config_handler.font_color
        self.color_preview = tk.Label(font_frame, text="颜色", bg=self.font_color, width=5)
        self.color_preview.grid(row=1, column=0, padx=5, pady=5)
        tk.Button(font_frame, text="选择颜色", command=choose_color).grid(row=1, column=1, padx=5, pady=5)
        
        # 透明度设置
        transparent_frame = tk.LabelFrame(theme_frame, text="透明度设置")
        transparent_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.transparent_var = tk.BooleanVar(value=self.main_app.config_handler.transparent_background)
        self.transparent_check = tk.Checkbutton(
            transparent_frame, text="主界面透明度",
            variable=self.transparent_var)
        self.transparent_check.pack()

    def _create_other_tab(self) -> None:
        """创建其他设置标签页"""
        other_frame = tk.Frame(self.notebook)
        self.notebook.add(other_frame, text="其他设置")
        
        # 开机自启动设置
        auto_start_frame = tk.LabelFrame(other_frame, text="开机自启动")
        auto_start_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.auto_start_var = tk.BooleanVar(value=self.main_app.config_handler.auto_start)
        self.auto_start_check = tk.Checkbutton(
            auto_start_frame, text="开机时自动启动程序",
            variable=self.auto_start_var)
        self.auto_start_check.pack(side=tk.LEFT, padx=5)



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
            # 应用排版设置
            try:
                horizontal_padding = int(self.horizontal_padding.get())
                vertical_padding = int(self.vertical_padding.get())
                if horizontal_padding < 0 or vertical_padding < 0:
                    raise ValueError
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
            
            # 应用控件大小设置
            try:
                self.main_app.config_handler.time_display_size = int(self.time_display_size.get())
                self.main_app.config_handler.countdown_size = int(self.countdown_size.get())
                self.main_app.config_handler.schedule_size = int(self.schedule_size.get())
            except ValueError:
                messagebox.showerror("错误", "请输入有效的控件大小值")
                return
            
            # 应用透明背景设置
            self.main_app.config_handler.transparent_background = self.transparent_var.get()
            
            # 应用字体设置
            self.main_app.config_handler.font_size = self.font_size.get()
            self.main_app.config_handler.font_color = self.font_color
            
            self.main_app.config_handler.save_config()
            # 更新字体设置
            self.main_app._update_font_settings()
            messagebox.showinfo("成功", "设置已保存")
        except Exception as e:
            logger.log_error(e)
            messagebox.showerror("错误", "保存设置时发生错误")

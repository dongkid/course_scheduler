from typing import Dict, List, Callable
import tkinter as tk
import os
import sys
import json
from datetime import datetime, date
from constants import SCHEDULE_FILE, WEEKDAYS
from config_handler import ConfigHandler
from logger import logger
from main_menu import MainMenu

class CourseScheduler:
    """课程表主应用类"""
    def __init__(self, startup_action=None):
        """初始化课程表应用
        Args:
            startup_action: 启动时要执行的动作
        """
        self.startup_action = startup_action
        self.last_second = -1  # 记录上次更新的秒数
        # 预计算并缓存icon路径
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.icon_path = os.path.join(base_path, 'res', 'icon.ico')
        # 初始化课程时间缓存
        self._course_time_cache = {}
        try:
            logger.log_debug("Initializing CourseScheduler application")
            # 先初始化配置
            self.config_handler = ConfigHandler()
            logger.log_debug("ConfigHandler initialized")
            self.config_handler.initialize_config()
            logger.log_debug("Configuration initialized")
            
            # 创建主窗口并应用配置
            self.root = self._create_root_window()
            logger.log_debug("Main window created")
            # 应用窗口尺寸并强制更新布局
            self.root.geometry(self.config_handler.geometry)
            self.root.update_idletasks()  # 立即应用窗口布局
            
            # 初始化其他成员变量
            self.schedule: Dict[str, List[Dict[str, str]]] = {}
            self.course_labels: List[tk.Label] = []
            self.course_duration = self.config_handler.course_duration
            self.editor_window = None
            self.settings_window = None
            self.about_window = None
            self.main_menu = None
            self.was_iconic = False  # 初始化窗口状态跟踪属性
            
            logger.log_debug("Initializing schedule")
            self._initialize_schedule()
            logger.log_debug("Schedule initialized")
            logger.log_debug("Initializing UI")
            self._initialize_ui()
            logger.log_debug("UI initialized")
            
            # 执行启动动作
            if self.startup_action == 'open_settings':
                self.open_settings()
            elif self.startup_action == 'open_menu' and self.main_menu:
                self.main_menu.show()
        except Exception as e:
            logger.log_error(e)
            raise

    def _create_root_window(self) -> tk.Tk:
        """创建并配置主窗口"""
        root = tk.Tk()
        root.title("课程表")
        
        # 使用缓存的icon路径
        
        # 简化窗口属性设置
        root.overrideredirect(True)  # 无边框
        root.resizable(False, False)  # 固定比例
        root.protocol("WM_DELETE_WINDOW", self.cleanup_resources)  # 退出时清理资源
        
        # 设置透明图标和窗口类型
        # 使用绝对路径并处理打包后的资源路径
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, 'res', 'icon.ico')
        root.iconbitmap(default=icon_path)
        root.wm_iconbitmap(icon_path)
        
        #窗口层级控制
        root.attributes('-toolwindow', True)  # 设置为工具窗口样式
        root.attributes('-topmost', True)
        root.after(100, lambda: root.attributes('-topmost', False))
        return root

    def cleanup_resources(self):
        """清理所有资源"""
        try:
            # 关闭所有子窗口
            for window in [self.editor_window, self.settings_window, self.about_window]:
                if window and window.window.winfo_exists():
                    window.window.destroy()
            
            # 取消所有定时器
            for timer_id in getattr(self, 'timer_ids', []):
                self.root.after_cancel(timer_id)
            
            # 销毁主窗口
            self.root.destroy()
        except Exception as e:
            logger.log_error(f"清理资源时出错: {str(e)}")
        finally:
            os._exit(0)  # 确保完全退出进程

    def _initialize_schedule(self) -> None:
        """加载或初始化课程表数据"""
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                schedule_data = json.load(f)
                # 兼容旧版单套课表
                if "schedules" not in schedule_data:
                    self.schedule = {
                        "current_schedule": "default",
                        "schedules": {
                            "default": schedule_data
                        }
                    }
                else:
                    self.schedule = schedule_data

            # 自动应用课表轮换逻辑
            if self.config_handler.schedule_rotation_enabled:
                try:
                    # 计算当前周数
                    start_date = self.config_handler.rotation_start_date.date()
                    current_date = datetime.now().date()
                    delta_weeks = (current_date - start_date).days // 7
                    
                    # 获取配置的课表
                    schedule1 = self.config_handler.rotation_schedule1
                    schedule2 = self.config_handler.rotation_schedule2
                    
                    # 确保课表存在
                    valid_schedules = list(self.schedule["schedules"].keys())
                    if schedule1 not in valid_schedules:
                        schedule1 = valid_schedules[0] if valid_schedules else "default"
                    if schedule2 not in valid_schedules:
                        schedule2 = valid_schedules[-1] if valid_schedules else "default"
                    
                    # 根据周数切换课表
                    if delta_weeks % 2 == 0:
                        self.schedule["current_schedule"] = schedule1
                    else:
                        self.schedule["current_schedule"] = schedule2
                        
                except Exception as e:
                    logger.log_error(f"课表轮换错误: {str(e)}")
                    self.schedule["current_schedule"] = self.config_handler.rotation_schedule1
        else:
            # 初始化默认课表
            self.schedule = {
                "current_schedule": "default",
                "schedules": {
                    "default": {
                        "0": [], "1": [], "2": [], "3": [], 
                        "4": [], "5": [], "6": []
                    }
                }
            }
            self._save_schedule()
    
    def save_schedule(self):
        """保存课表"""
        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.schedule, f, ensure_ascii=False, indent=2)
    
    def _initialize_ui(self) -> None:
        """初始化主界面"""
        # 应用配置中的间距设置
        self.root.configure(padx=self.config_handler.horizontal_padding, 
                          pady=self.config_handler.vertical_padding)
        
        self._create_time_display()
        self._create_countdown_display()
        self._create_schedule_display()
        
        # 创建主菜单按钮容器
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=self.config_handler.vertical_padding)
        
        # 初始化主菜单
        self.main_menu = MainMenu(
            self.root,
            {
                "编辑课表": self.open_editor,
                "小工具": self._show_tools_window,
                "设置": self.open_settings,
                "关于": self.open_about,
                # 重启功能存在问题，暂时注释。
                # "重启程序": self.restart_program,
                "退出程序": self._exit_with_confirmation
            }
        )
        
        # 添加主菜单按钮到按钮容器
        menu_button = self.main_menu.create_menu_button(self.button_frame)
        menu_button.pack(side=tk.LEFT, padx=5)
        
        self._update_font_settings()
        if self.config_handler.transparent_background:
            self.root.attributes("-transparentcolor", "white")
            self.root.configure(bg="white")
        self._start_update_loop()

    def _create_time_display(self) -> None:
        """创建时间显示区域"""
        self.time_label = tk.Label(
            self.root, 
            font=("微软雅黑", self.config_handler.time_display_size, "bold"),
            fg=self.config_handler.font_color,
            bg="#ecf0f1"
        )
        self.time_label.pack(pady=self.config_handler.vertical_padding, fill=tk.X)
        
        # 添加点击事件
        self.time_label.bind("<Button-1>", self._on_time_label_click)
        
    def _on_time_label_click(self, event):
        """处理时间标签点击事件"""
        from tkinter import messagebox
        from tools.fullscreen_time import FullscreenTimeWindow
        from tools.weather_ui import WeatherUI
        from tools.weather import WeatherAPI, WeatherTool
        
        # 点击计数器
        if not hasattr(self, '_click_count'):
            self._click_count = 0
        self._click_count += 1
        
        # 重置计数器定时器
        if hasattr(self, '_click_timer'):
            self.root.after_cancel(self._click_timer)
        self._click_timer = self.root.after(500, self._reset_click_count)
        
        # 处理点击逻辑
        if self._click_count == 1:
            # 单次点击显示迷你天气
            # 检查API密钥是否存在
            if self.config_handler.heweather_api_key:
                # 使用WeatherTool来获取或创建迷你天气界面
                if not hasattr(self, "weather_tool"):
                    self.weather_tool = WeatherTool()
                # 获取迷你天气界面（如果已存在会重用）
                self.weather_tool.get_mini_ui(master=self.root)
        elif self._click_count >= 3:
            # 三次点击显示全屏时间
            self._click_count = 0
            if messagebox.askyesno("确认", "是否打开全屏大号时间？"):
                if not hasattr(self, "fullscreen_time_window"):
                    from tools.fullscreen_time import FullscreenTimeWindow
                    self.fullscreen_time_window = FullscreenTimeWindow(self.root, self.config_handler)
                self.fullscreen_time_window.show()

    def _reset_click_count(self):
        """重置点击计数器"""
        self._click_count = 0
        
    def _show_click_tooltip(self, event):
        """显示点击提示气泡"""
        # 创建气泡窗口
        tooltip = tk.Toplevel(self.root)
        tooltip.wm_overrideredirect(True)
        tooltip.geometry(f"+{event.x_root+20}+{event.y_root+20}")
        
        # 气泡内容
        label = tk.Label(tooltip, text="待开发功能", bg="yellow", fg="black", padx=8, pady=4)
        label.pack()
        
        # 自动关闭定时器
        tooltip.after(1500, tooltip.destroy)

    def _create_countdown_display(self) -> None:
        """创建倒计时显示区域"""
        self.countdown_frame = tk.Frame(self.root)
        self.countdown_frame.pack(pady=self.config_handler.vertical_padding)
        
        # 第一行：显示自定义倒计时名称
        self.countdown_label1 = tk.Label(
            self.countdown_frame,
            text=f"距离{self.config_handler.countdown_name}",
            font=("微软雅黑", self.config_handler.countdown_size - 4),
            fg=self.config_handler.font_color,
            bg="#ecf0f1"
        )
        self.countdown_label1.pack()
        
        # 第二行：显示天数和"天"字
        self.countdown_line2_frame = tk.Frame(self.countdown_frame)
        self.countdown_line2_frame.pack()
        
        self.countdown_label2 = tk.Label(
            self.countdown_line2_frame,
            font=("微软雅黑", self.config_handler.countdown_size - 2, "bold"),
            fg=self.config_handler.font_color,
            bg="#ecf0f1"
        )
        self.countdown_label2.pack(side=tk.LEFT)
        
        self.countdown_label3 = tk.Label(
            self.countdown_line2_frame,
            text="天",
            font=("微软雅黑", self.config_handler.countdown_size - 4),
            fg=self.config_handler.font_color,
            bg="#ecf0f1"
        )
        self.countdown_label3.pack(side=tk.LEFT)

    def _create_schedule_display(self) -> None:
        """创建课程表显示区域"""
        self.schedule_frame = tk.Frame(self.root)
        self.schedule_frame.pack(padx=self.config_handler.horizontal_padding, 
                               pady=self.config_handler.vertical_padding, 
                               fill=tk.BOTH, expand=True)

    def _start_update_loop(self) -> None:
        """启动界面更新循环"""
        self.timer_ids = []  # 存储定时器ID
        self.update_display()
        self.timer_ids.append(self.root.after(1000, self.update_display))
    
    def update_display(self) -> None:
        """更新主界面显示内容"""
        try:
            now = datetime.now()
            current_second = now.second
            
            # 缓存当前时间对象避免重复计算
            current_time = now.time()
            
            # 只有秒数变化时才更新UI
            if current_second != self.last_second:
                self._update_time_display(now)
                self._update_countdown_display(now)
                self._update_schedule_display(now)
                self.last_second = current_second
                
            self._schedule_next_update()
            
            # 检测窗口状态变化
            is_iconic = self.root.state() == 'iconic'
            if self.was_iconic and not is_iconic:
                # 窗口从最小化恢复时重新置顶
                self.root.attributes('-topmost', True)
                self.root.after(100, lambda: self.root.attributes('-topmost', False))
            self.was_iconic = is_iconic
        except Exception as e:
            logger.log_error(e)

    def _update_time_display(self, now: datetime) -> None:
        """更新时间显示"""
        weekday = now.weekday()
        self.time_label.config(
            text=now.strftime("%Y-%m-%d\n%H:%M:%S\n") + 
            f"星期{WEEKDAYS[weekday]}"
        )

    def _update_countdown_display(self, now: datetime) -> None:
        """更新倒计时显示"""
        delta = (self.config_handler.countdown_date.date() - now.date()).days
        # 高考彩蛋：当倒计时名称是高考且天数<=100时显示红色
        if self.config_handler.countdown_name == "高考" and delta <= 100:
            self.countdown_label2.config(text=str(delta), fg="red")
        else:
            self.countdown_label2.config(text=str(delta), fg=self.config_handler.font_color)

    def _update_schedule_display(self, now: datetime) -> None:
        """更新课程表显示"""
        if not hasattr(self, 'course_labels'):
            self.course_labels = []
            
        weekday = str(now.weekday())
        today_schedule = self.schedule["schedules"][self.schedule["current_schedule"]].get(weekday, [])
        
        # 在更新前清除所有课程时间缓存
        self._course_time_cache.clear()
        
        # 过滤掉已销毁的标签
        self.course_labels = [label for label in self.course_labels if label.winfo_exists()]
        
        # 根据当前课表重新排列所有标签
        for i, course in enumerate(today_schedule):
            color = self._get_course_color(now, course)
            if i < len(self.course_labels):
                # 强制更新标签颜色状态
                self._update_existing_label(i, course, color, force_update=True)
                # 调整grid行号
                self.course_labels[i].master.grid(row=i)
            else:
                # 创建新标签并指定grid行号
                self._create_new_label(course, color, row=i)
        
        # 移除多余的标签
        self._remove_extra_labels(today_schedule)

    def _update_course_labels(self, now: datetime, schedule: List[Dict[str, str]]) -> None:
        """更新或创建课程标签"""
        for i, course in enumerate(schedule):
            color = self._get_course_color(now, course)
            
            if i < len(self.course_labels):
                self._update_existing_label(i, course, color)
            else:
                self._create_new_label(course, color)


    def _get_course_color(self, now: datetime, course: Dict[str, str]) -> str:
        """根据课程时间获取显示颜色"""
        # 使用课程名称+时间作为缓存键
        cache_key = f"{course['name']}_{course['start_time']}_{course['end_time']}"
        
        # 从缓存获取或计算
        if cache_key not in self._course_time_cache:
            self._course_time_cache[cache_key] = (
                datetime.strptime(course["start_time"], "%H:%M").time(),
                datetime.strptime(course["end_time"], "%H:%M").time()
            )
            
        start_time, end_time = self._course_time_cache[cache_key]
        current_time = now.time()
        
        if start_time <= current_time <= end_time:
            return "yellow"  # 正在上的课程为黄色
        elif current_time > end_time:
            return "green"   # 已上完的课程为绿色
        return "red"     # 未上过的课程为红色

    def _update_existing_label(self, index: int, course: Dict[str, str], color: str, force_update: bool = False) -> None:
        """更新现有课程标签"""
        label = self.course_labels[index]
        new_text = f"{course['start_time']} {course['name']}"
        
        # 始终更新文本和颜色状态
        label.config(text=new_text)
        label.last_color = color
        
        if hasattr(label, 'status_canvas'):
            # 缓存字体大小计算
            if not hasattr(label, 'cached_circle_size'):
                label.cached_circle_size = int(self.config_handler.schedule_size * 1.2)
            
            circle_size = label.cached_circle_size
            label.status_canvas.config(width=circle_size, height=circle_size)
            
            # 强制重绘Canvas
            label.status_canvas.delete("all")
            label.status_canvas.create_oval(0, 0, circle_size, circle_size, fill=color, outline=color)
            label.status_canvas.current_color = color
            label.status_canvas.config(bg=color)
        
        # 提升该课程标签的显示层级
        label.master.lift()

    def _update_font_settings(self) -> None:
        """更新所有UI组件的字体设置"""
        # 更新时间显示
        self.time_label.config(
            font=("微软雅黑", self.config_handler.font_size, "bold"),
            fg=self.config_handler.font_color
        )
        
        # 更新课程标签色块尺寸
        if hasattr(self, 'course_labels'):
            for label in self.course_labels:
                if hasattr(label, 'status_canvas'):
                    circle_size = int(self.config_handler.schedule_size * 1.2)
                    label.status_canvas.config(width=circle_size, height=circle_size)
                    label.status_canvas.coords(label.status_canvas.oval_id, 0, 0, circle_size, circle_size)
        
        # 更新倒计时显示
        self.countdown_label1.config(
            font=("微软雅黑", self.config_handler.font_size - 4),
            fg=self.config_handler.font_color
        )
        self.countdown_label2.config(
            font=("微软雅黑", self.config_handler.font_size - 2, "bold"),
            fg=self.config_handler.font_color
        )
        self.countdown_label3.config(
            font=("微软雅黑", self.config_handler.font_size - 4),
            fg=self.config_handler.font_color
        )
        
        # 更新课程标签
        self.course_labels = [label for label in self.course_labels if label.winfo_exists()]
        for label in self.course_labels:
            label.config(
                font=("微软雅黑", self.config_handler.schedule_size, "bold"),
                fg=self.config_handler.font_color
            )
        
        # 强制更新所有部件
        self.root.update_idletasks()

    def _adjust_ui_layout(self) -> None:
        """调整界面布局以适应窗口大小变化"""
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # 更新字体设置
        self._update_font_settings()
        
        # 调整课程表显示区域
        self.schedule_frame.config(padx=min(20, int(window_width / 20)))
        
        # 调整按钮布局
        for child in self.schedule_frame.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(pady=min(5, int(window_height / 50)))
        
        # 强制更新所有部件
        self.root.update_idletasks()

    def _create_new_label(self, course: Dict[str, str], color: str, row: int) -> None:
        """创建新课程标签"""
        course_frame = tk.Frame(self.schedule_frame)
        course_frame.grid(row=row, column=0, sticky="ew", pady=2)  # 使用指定的行号
        
        label = tk.Label(
            course_frame,
            text=f"{course['start_time']} {course['name']}",
            font=("微软雅黑", self.config_handler.schedule_size, "bold"),
            fg=self.config_handler.font_color,
            anchor='w'
        )
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 根据字体大小计算色块尺寸
        circle_size = int(self.config_handler.schedule_size * 1.2)
        status_canvas = tk.Canvas(
            course_frame,
            width=circle_size,
            height=circle_size,
            bg=color,
            highlightthickness=0
        )
        # 保存圆形图形的ID以便后续更新
        oval_id = status_canvas.create_oval(0, 0, circle_size, circle_size, fill=color, outline=color)
        status_canvas.oval_id = oval_id  # 存储图形ID
        status_canvas.pack(side=tk.RIGHT, padx=5)
        label.status_canvas = status_canvas
        self.course_labels.append(label)
        
        self.schedule_frame.grid_columnconfigure(0, weight=1)

    def _remove_extra_labels(self, schedule: List[Dict[str, str]]) -> None:
        """移除多余的课程标签"""
        # 移除所有超出当前课程数量的标签
        for i in range(len(schedule), len(self.course_labels)):
            if i < len(self.course_labels):
                label = self.course_labels[i]
                label.master.destroy()  # 销毁整个课程框架
        # 更新标签列表
        self.course_labels = self.course_labels[:len(schedule)]

    def _schedule_next_update(self) -> None:
        """安排下一次界面更新"""
        timer_id = self.root.after(1000, self.update_display)
        if hasattr(self, 'timer_ids'):
            self.timer_ids.append(timer_id)
    
    def restart_program(self) -> None:
        """彻底重启应用程序"""
        import sys, os
        
        # 1. 清理所有定时器
        for timer_id in getattr(self, 'timer_ids', []):
            self.root.after_cancel(timer_id)
            
        # 2. 销毁所有子窗口
        for window in [self.editor_window, self.settings_window, self.about_window]:
            if window and window.window.winfo_exists():
                window.window.destroy()
                
        # 3. 销毁主窗口并退出主循环
        self.root.quit()
        self.root.destroy()
        
        # 4. 彻底重启进程
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    
    def open_editor(self):
        from editor import EditorWindow
        if self.editor_window is None or not self.editor_window.window.winfo_exists():
            self.editor_window = EditorWindow(self)
        else:
            self.editor_window.window.lift()
    
    def open_settings(self):
        from settings import SettingsWindow
        if self.settings_window is None or not self.settings_window.window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.window.lift()
    
    def open_about(self):
        from about_window import AboutWindow
        if self.about_window is None or not self.about_window.window.winfo_exists():
            self.about_window = AboutWindow(self.root)
        else:
            self.about_window.window.lift()
            
    def _exit_with_confirmation(self):
        """带确认的退出函数"""
        # self.root.quit()
        from tkinter import messagebox
        if self.config_handler.debug_mode:
            self.root.quit()
        else:
            if messagebox.askyesno("确认", "确定要退出程序吗？"):
                self.root.quit()

    def _show_tools_window(self):
        """显示小工具窗口"""
        from tools_window import ToolsWindow
        if not hasattr(self, 'tools_window') or not self.tools_window.window.winfo_exists():
            self.tools_window = ToolsWindow(self.root, self.config_handler)
        self.tools_window.show()

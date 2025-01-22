from typing import Dict, List, Callable
import tkinter as tk
import os
import json
from datetime import datetime, date
from constants import SCHEDULE_FILE, WEEKDAYS
from config_handler import ConfigHandler
from logger import logger
from main_menu import MainMenu

class CourseScheduler:
    """课程表主应用类"""
    def __init__(self):
        """初始化课程表应用"""
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
            self.root.geometry(self.config_handler.geometry)
            
            # 初始化其他成员变量
            self.schedule: Dict[str, List[Dict[str, str]]] = {}
            self.course_labels: List[tk.Label] = []
            self.course_duration = self.config_handler.course_duration
            self.editor_window = None
            self.settings_window = None
            self.about_window = None
            self.main_menu = None
            
            logger.log_debug("Initializing schedule")
            self._initialize_schedule()
            logger.log_debug("Schedule initialized")
            logger.log_debug("Initializing UI")
            self._initialize_ui()
            logger.log_debug("UI initialized")
        except Exception as e:
            logger.log_error(e)
            raise

    def _create_root_window(self) -> tk.Tk:
        """创建并配置主窗口"""
        root = tk.Tk()
        root.title("课程表")
        root.overrideredirect(True)  # 无边框
        root.resizable(False, False)  # 固定比例
        root.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用关闭按钮
        return root

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
                "设置": self.open_settings,
                "关于": self.open_about,
                "重启主界面": self.restart_ui,
                "退出程序": self.root.quit,
                "小工具": self._show_tools_window
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
        
        result = messagebox.askyesno(
            "全屏时间",
            "是否开启全屏时间？"
        )
        if result:
            if not hasattr(self, "fullscreen_time_window"):
                self.fullscreen_time_window = FullscreenTimeWindow(self.root, self.config_handler)
            self.fullscreen_time_window.show()

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
        self.update_display()
        self.root.after(1000, self.update_display)
    
    def update_display(self) -> None:
        """更新主界面显示内容"""
        try:
            now = datetime.now()
            self._update_time_display(now)
            self._update_countdown_display(now)
            self._update_schedule_display(now)
            self._schedule_next_update()
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
        self.countdown_label2.config(text=str(delta))

    def _update_schedule_display(self, now: datetime) -> None:
        """更新课程表显示"""
        if not hasattr(self, 'course_labels'):
            self.course_labels = []
            
        weekday = str(now.weekday())
        today_schedule = self.schedule["schedules"][self.schedule["current_schedule"]].get(weekday, [])
        
        # 过滤掉已销毁的标签
        self.course_labels = [label for label in self.course_labels if label.winfo_exists()]
        
        # 仅更新或创建必要的标签
        for i, course in enumerate(today_schedule):
            color = self._get_course_color(now, course)
            if i < len(self.course_labels):
                self._update_existing_label(i, course, color)
            else:
                self._create_new_label(course, color)
        
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
        start_time = datetime.strptime(course["start_time"], "%H:%M").time()
        end_time = datetime.strptime(course["end_time"], "%H:%M").time()
        current_time = now.time()
        
        if start_time <= current_time <= end_time:
            return "yellow"  # 正在上的课程为黄色
        elif current_time > end_time:
            return "green"   # 已上完的课程为绿色
        return "#ffcccc"     # 未上过的课程为浅红色

    def _update_existing_label(self, index: int, course: Dict[str, str], color: str) -> None:
        """更新现有课程标签"""
        label = self.course_labels[index]
        label.config(
            text=f"{course['start_time']} {course['name']}"
        )
        if hasattr(label, 'status_canvas'):
            label.status_canvas.config(bg=color)

    def _update_font_settings(self) -> None:
        """更新所有UI组件的字体设置"""
        # 更新时间显示
        self.time_label.config(
            font=("微软雅黑", self.config_handler.font_size, "bold"),
            fg=self.config_handler.font_color
        )
        
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

    def _create_new_label(self, course: Dict[str, str], color: str) -> None:
        """创建新课程标签"""
        course_frame = tk.Frame(self.schedule_frame)
        course_frame.grid(row=len(self.course_labels), column=0, sticky="ew", pady=2)
        
        label = tk.Label(
            course_frame,
            text=f"{course['start_time']} {course['name']}",
            font=("微软雅黑", self.config_handler.schedule_size, "bold"),
            fg=self.config_handler.font_color,
            anchor='w'
        )
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        status_canvas = tk.Canvas(
            course_frame,
            width=10,  # 最小宽度
            height=10,
            bg=color,
            highlightthickness=0
        )
        # 绘制圆柱形
        status_canvas.create_oval(0, 0, 10, 10, fill=color, outline=color)
        status_canvas.pack(side=tk.RIGHT, padx=5)
        label.status_canvas = status_canvas
        self.course_labels.append(label)
        
        # 配置列权重
        self.schedule_frame.grid_columnconfigure(0, weight=1)

    def _remove_extra_labels(self, schedule: List[Dict[str, str]]) -> None:
        """移除多余的课程标签"""
        while len(self.course_labels) > len(schedule):
            last_label = self.course_labels.pop()
            last_label.pack_forget()
            last_label.status_canvas.pack_forget()

    def _schedule_next_update(self) -> None:
        """安排下一次界面更新"""
        self.root.after(1000, self.update_display)
    
    def restart_ui(self) -> None:
        """重启主界面"""
        # 清空课程标签列表
        self.course_labels = []
        
        # 销毁现有界面组件（包括schedule_frame）
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 显式删除框架引用
        if hasattr(self, 'schedule_frame'):
            del self.schedule_frame
        if hasattr(self, 'button_frame'):
            del self.button_frame
            
        # 重新初始化界面（包含_create_schedule_display的原始调用）
        self._initialize_ui()
        
        # 应用字体设置并强制布局更新
        self._adjust_ui_layout()
        self.root.update_idletasks()  # 立即刷新布局
        
        # 确保主菜单已重新初始化
        self.main_menu = MainMenu(
            self.root,
            {
                "编辑课表": self.open_editor,
                "设置": self.open_settings,
                "关于": self.open_about,
                "重启主界面": self.restart_ui,
                "退出程序": self.root.quit,
                "小工具": self._show_tools_window
            }
        )
    
    
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
            
    def _show_tools_window(self):
        """显示小工具窗口"""
        from tools_window import ToolsWindow
        if not hasattr(self, 'tools_window') or not self.tools_window.window.winfo_exists():
            self.tools_window = ToolsWindow(self.root, self.config_handler)
        self.tools_window.show()

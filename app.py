from typing import Dict, List
import tkinter as tk
import os
import json
from datetime import datetime, date
from constants import SCHEDULE_FILE, WEEKDAYS
from config_handler import ConfigHandler

class CourseScheduler:
    """课程表主应用类"""
    def __init__(self):
        """初始化课程表应用"""
        self.root = self._create_root_window()
        self.config_handler = ConfigHandler(self.root)
        self.config_handler.initialize_config()
        self.schedule: Dict[str, List[Dict[str, str]]] = {}
        self.course_labels: List[tk.Label] = []
        self.course_duration = 40 # 默认课程时长为45分钟
        
        self._initialize_schedule()
        self._initialize_ui()

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
                data = json.load(f)
                if isinstance(data, dict):
                    self.schedule = data
                else:
                    self.schedule = {str(i): [] for i in range(7)}
                    self._save_schedule()
        else:
            self.schedule = {str(i): [] for i in range(7)}
            self._save_schedule()
        
    def load_schedule(self):
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.schedule = data
                else:
                    self.schedule = {str(i): [] for i in range(7)}
                    self.save_schedule()
        else:
            self.schedule = {str(i): [] for i in range(7)}
            self.save_schedule()
    
    def save_schedule(self):
        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.schedule, f, ensure_ascii=False, indent=2)
    
    def _initialize_ui(self) -> None:
        """初始化主界面"""
        self._create_time_display()
        self._create_countdown_display()
        self._create_schedule_display()
        self._create_buttons()
        self._start_update_loop()

    def _create_time_display(self) -> None:
        """创建时间显示区域"""
        self.time_label = tk.Label(
            self.root, 
            font=("微软雅黑", 16, "bold"),
            fg="#2c3e50",
            bg="#ecf0f1"
        )
        self.time_label.pack(pady=15, fill=tk.X)

    def _create_countdown_display(self) -> None:
        """创建高考倒计时显示区域"""
        self.gaokao_frame = tk.Frame(self.root)
        self.gaokao_frame.pack(pady=2)
        
        # 第一行：显示"距离高考"
        self.gaokao_label1 = tk.Label(
            self.gaokao_frame,
            text="距离高考",
            font=("微软雅黑", 12),
            fg="#2c3e50",
            bg="#ecf0f1"
        )
        self.gaokao_label1.pack()
        
        # 第二行：显示天数和"天"字
        self.gaokao_line2_frame = tk.Frame(self.gaokao_frame)
        self.gaokao_line2_frame.pack()
        
        self.gaokao_label2 = tk.Label(
            self.gaokao_line2_frame,
            font=("微软雅黑", 14, "bold"),
            fg="#2c3e50",
            bg="#ecf0f1"
        )
        self.gaokao_label2.pack(side=tk.LEFT)
        
        self.gaokao_label3 = tk.Label(
            self.gaokao_line2_frame,
            text="天",
            font=("微软雅黑", 12),
            fg="#2c3e50",
            bg="#ecf0f1"
        )
        self.gaokao_label3.pack(side=tk.LEFT)

    def _create_schedule_display(self) -> None:
        """创建课程表显示区域"""
        self.schedule_frame = tk.Frame(self.root)
        self.schedule_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def _create_buttons(self) -> None:
        """创建功能按钮区域"""
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="编辑课表", command=self.open_editor).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="设置", command=self.open_settings).pack(side=tk.LEFT, padx=5)

    def _start_update_loop(self) -> None:
        """启动界面更新循环"""
        self.update_display()
        self.root.after(1000, self.update_display)
    
    def update_display(self) -> None:
        """更新主界面显示内容"""
        now = datetime.now()
        self._update_time_display(now)
        self._update_countdown_display(now)
        self._update_schedule_display(now)
        self._schedule_next_update()

    def _update_time_display(self, now: datetime) -> None:
        """更新时间显示"""
        weekday = now.weekday()
        self.time_label.config(
            text=now.strftime("%Y-%m-%d\n%H:%M:%S\n") + 
            f"星期{WEEKDAYS[weekday]}"
        )

    def _update_countdown_display(self, now: datetime) -> None:
        """更新高考倒计时显示"""
        gaokao_date = date(self.config_handler.gaokao_year, 6, 7)
        delta = (gaokao_date - now.date()).days
        self.gaokao_label2.config(text=str(delta))

    def _update_schedule_display(self, now: datetime) -> None:
        """更新课程表显示"""
        if not hasattr(self, 'course_labels'):
            self.course_labels = []
            
        weekday = str(now.weekday())
        today_schedule = self.schedule.get(weekday, [])
        
        self._update_course_labels(now, today_schedule)
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

    def _adjust_ui_layout(self) -> None:
        """调整界面布局以适应窗口大小变化"""
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # 调整时间显示字体大小，确保最小为10
        font_size = max(10, min(16, int(window_width / 15)))
        self.time_label.config(font=("Helvetica", font_size, "bold"))
        
        # 调整倒计时显示字体大小，确保最小为8
        countdown_size = max(8, min(12, int(window_width / 20)))
        self.gaokao_label1.config(font=("Helvetica", countdown_size))
        self.gaokao_label2.config(font=("Helvetica", countdown_size + 2, "bold"))
        self.gaokao_label3.config(font=("Helvetica", countdown_size))
        
        # 调整课程表显示区域
        self.schedule_frame.config(padx=min(20, int(window_width / 20)))
        
        # 调整按钮布局
        for child in self.schedule_frame.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(pady=min(5, int(window_height / 50)))
        
        # 强制更新所有部件
        self.time_label.update_idletasks()
        self.gaokao_frame.update_idletasks()
        self.schedule_frame.update_idletasks()
        self.root.update_idletasks()

    def _create_new_label(self, course: Dict[str, str], color: str) -> None:
        """创建新课程标签"""
        course_frame = tk.Frame(self.schedule_frame)
        course_frame.pack(fill=tk.X, pady=2)
        
        label = tk.Label(
            course_frame,
            text=f"{course['start_time']} {course['name']}",
            font=("微软雅黑", 12, "bold"),
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

    def _remove_extra_labels(self, schedule: List[Dict[str, str]]) -> None:
        """移除多余的课程标签"""
        while len(self.course_labels) > len(schedule):
            last_label = self.course_labels.pop()
            last_label.pack_forget()
            last_label.status_canvas.pack_forget()

    def _schedule_next_update(self) -> None:
        """安排下一次界面更新"""
        self.root.after(1000, self.update_display)
    
    def open_editor(self):
        from editor import EditorWindow
        EditorWindow(self)
    
    def open_settings(self):
        from settings import SettingsWindow
        SettingsWindow(self)

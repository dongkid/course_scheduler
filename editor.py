import tkinter as tk
from tkinter import ttk, messagebox
from constants import WEEKDAYS
from datetime import datetime, timedelta
from logger import logger

class TimePicker:
    def __init__(self, parent, initial_time):
        self.selected_time = None
        self.top = tk.Toplevel(parent)
        self.top.title("选择时间")
        
        # 解析初始时间
        try:
            hours, minutes = map(int, initial_time.split(':'))
        except:
            hours, minutes = 8, 0
        
        # 小时选择
        hour_frame = tk.Frame(self.top)
        hour_frame.pack(pady=5)
        tk.Label(hour_frame, text="小时:").pack(side=tk.LEFT)
        self.hour_var = tk.StringVar(value=str(hours))
        self.hour_combobox = ttk.Combobox(hour_frame, textvariable=self.hour_var, width=3)
        self.hour_combobox['values'] = [str(h).zfill(2) for h in range(24)]
        self.hour_combobox.pack(side=tk.LEFT)
        
        # 分钟选择
        minute_frame = tk.Frame(self.top)
        minute_frame.pack(pady=5)
        tk.Label(minute_frame, text="分钟:").pack(side=tk.LEFT)
        self.minute_var = tk.StringVar(value=str(minutes))
        self.minute_combobox = ttk.Combobox(minute_frame, textvariable=self.minute_var, width=3)
        self.minute_combobox['values'] = [str(m).zfill(2) for m in range(0, 60, 5)]
        self.minute_combobox.pack(side=tk.LEFT)
        
        # 确认按钮
        tk.Button(self.top, text="确定", command=self.on_confirm).pack(pady=10)
    
    def on_confirm(self):
        self.selected_time = f"{self.hour_var.get()}:{self.minute_var.get()}"
        self.top.destroy()

class EditorWindow:
    def __init__(self, main_app):
        """初始化课表编辑窗口"""
        try:
            self.main_app = main_app
            self.window = self._create_window()
            self.day_frames: List[tk.Frame] = []
            self.all_courses = self._get_all_courses()  # 初始化时加载所有课程
            self._initialize_ui()
        except Exception as e:
            logger.log_error(e)
            raise

    def _create_window(self) -> tk.Toplevel:
        """创建并配置编辑窗口"""
        window = tk.Toplevel()
        window.title("课表编辑")
        return window

    def _initialize_ui(self) -> None:
        """初始化编辑界面"""
        self._create_notebook()
        self._create_save_button()

    def _create_notebook(self) -> None:
        """创建标签页"""
        self.notebook = tk.ttk.Notebook(self.window)
        self.notebook.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        for i in range(7):
            day_frame = tk.Frame(self.notebook)
            self.day_frames.append(day_frame)
            self.notebook.add(day_frame, text=f"星期{WEEKDAYS[i]}")
            self.create_day_ui(day_frame, str(i))

    def _create_save_button(self) -> None:
        """创建保存按钮"""
        tk.Button(self.window, text="保存", command=self.save).pack(pady=10)
    
    def create_day_ui(self, frame, day):
        # 清除现有内容
        for widget in frame.winfo_children():
            widget.destroy()
        
        # 添加课程
        courses = self.main_app.schedule.get(day, [])
        for i, course in enumerate(courses):
            self.add_course_row(frame, i, course)
        
        # 更新课程名称建议
        self.all_courses = self._get_all_courses()
        
        # 添加新课程按钮
        tk.Button(frame, text="添加课程", command=lambda: self.add_course_row(frame, len(courses))).pack(pady=5)
        
        # 绑定标签页切换事件
        def on_tab_change(event):
            selected_tab = self.notebook.index(self.notebook.select())
            self.create_day_ui(self.day_frames[selected_tab], str(selected_tab))
        
        self.notebook.bind("<<NotebookTabChanged>>", on_tab_change)
    
    def add_course_row(self, frame, index, course=None):
        row_frame = tk.Frame(frame)
        row_frame.pack(fill=tk.X, pady=2)
        
        # 开始时间
        start_time_entry = tk.Entry(row_frame, width=6)
        start_time_entry.insert(0, course["start_time"] if course else "08:00")
        start_time_entry.pack(side=tk.LEFT, padx=2)
        
        # 开始时间调整按钮
        def show_start_time_picker():
            picker = TimePicker(self.window, start_time_entry.get())
            self.window.wait_window(picker.top)
            if picker.selected_time:
                start_time_entry.delete(0, tk.END)
                start_time_entry.insert(0, picker.selected_time)
                calculate_end_time()
        
        tk.Button(row_frame, text="🕒", command=show_start_time_picker).pack(side=tk.LEFT, padx=2)
        
        # 结束时间
        end_time_entry = tk.Entry(row_frame, width=6)
        end_time_entry.insert(0, course["end_time"] if course else "09:00")
        end_time_entry.pack(side=tk.LEFT, padx=2)
        
        # 结束时间调整按钮
        def show_end_time_picker():
            picker = TimePicker(self.window, end_time_entry.get())
            self.window.wait_window(picker.top)
            if picker.selected_time:
                end_time_entry.delete(0, tk.END)
                end_time_entry.insert(0, picker.selected_time)
        
        tk.Button(row_frame, text="🕒", command=show_end_time_picker).pack(side=tk.LEFT, padx=2)
        
        # 自定义课程名称输入框
        name_entry = tk.Entry(row_frame)
        if course and course["name"]:
            name_entry.insert(0, course["name"])
        name_entry.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # 历史课程选择框
        history_var = tk.StringVar()
        history_combobox = ttk.Combobox(row_frame, textvariable=history_var)
        history_combobox['values'] = list(self.all_courses)
        history_combobox.pack(side=tk.LEFT, padx=2)
        
        # 绑定历史课程选择事件
        def on_history_select(event):
            selected_course = history_var.get()
            if selected_course:
                name_entry.delete(0, tk.END)
                name_entry.insert(0, selected_course)
        
        history_combobox.bind("<<ComboboxSelected>>", on_history_select)
        
        # 自动计算结束时间
        def calculate_end_time():
            if not self.main_app.config_handler.auto_complete_end_time:
                return
            try:
                start_time_str = start_time_entry.get()
                start_time = datetime.strptime(start_time_str, "%H:%M")
                end_time = start_time + timedelta(minutes=self.main_app.course_duration)
                end_time_entry.delete(0, tk.END)
                end_time_entry.insert(0, end_time.strftime("%H:%M"))
            except ValueError:
                pass

        # 自动计算下一个课程时间
        def calculate_next_course_time():
            if not self.main_app.config_handler.auto_calculate_next_course:
                return
            try:
                # 获取当前行之前的最后一行
                previous_row = None
                for widget in frame.winfo_children():
                    if isinstance(widget, tk.Frame) and widget != row_frame:
                        previous_row = widget
                
                if previous_row:
                    # 获取上一行的结束时间
                    prev_entries = [w for w in previous_row.winfo_children() if isinstance(w, tk.Entry)]
                    if len(prev_entries) >= 2:
                        prev_end_time = prev_entries[1].get()
                        prev_time = datetime.strptime(prev_end_time, "%H:%M")
                        # 计算下一个课程的开始时间
                        next_start_time = prev_time + timedelta(minutes=self.main_app.config_handler.break_duration)
                        start_time_entry.delete(0, tk.END)
                        start_time_entry.insert(0, next_start_time.strftime("%H:%M"))
                        # 自动计算结束时间
                        calculate_end_time()
            except ValueError:
                pass

        # 时间格式验证和自动修正
        def validate_time():
            def fix_time_format(time_str):
                # 处理缺少冒号的情况
                if ':' not in time_str:
                    if len(time_str) == 3:
                        time_str = f"0{time_str[0]}:{time_str[1:]}"  # 8:00 -> 08:00
                    elif len(time_str) == 4:
                        time_str = f"{time_str[:2]}:{time_str[2:]}"  # 1230 -> 12:30
                    else:
                        return None
                
                # 分割小时和分钟
                parts = time_str.split(':')
                if len(parts) != 2:
                    return None
                
                # 处理缺少前导零的情况
                hour = parts[0].zfill(2)
                minute = parts[1].zfill(2)
                
                # 验证时间范围
                try:
                    hour_num = int(hour)
                    minute_num = int(minute)
                    if 0 <= hour_num < 24 and 0 <= minute_num < 60:
                        return f"{hour}:{minute}"
                except ValueError:
                    pass
                return None
            
            # 获取并修正时间
            start_time_str = start_time_entry.get()
            end_time_str = end_time_entry.get()
            
            fixed_start = fix_time_format(start_time_str)
            fixed_end = fix_time_format(end_time_str)
            
            if fixed_start:
                if fixed_start != start_time_str:
                    start_time_entry.delete(0, tk.END)
                    start_time_entry.insert(0, fixed_start)
                start_time_str = fixed_start
            if fixed_end:
                if fixed_end != end_time_str:
                    end_time_entry.delete(0, tk.END)
                    end_time_entry.insert(0, fixed_end)
                end_time_str = fixed_end
            
            # 验证时间格式和逻辑
            try:
                start_time = datetime.strptime(start_time_str, "%H:%M")
                end_time = datetime.strptime(end_time_str, "%H:%M")
                
                if start_time >= end_time:
                    start_time_entry.config(fg="red")
                    end_time_entry.config(fg="red")
                    return False
                
                start_time_entry.config(fg="black")
                end_time_entry.config(fg="black")
                return True
            except ValueError:
                if not fixed_start or not fixed_end:
                    start_time_entry.config(fg="red")
                    end_time_entry.config(fg="red")
                return False
        
        start_time_entry.bind("<FocusOut>", lambda e: [calculate_end_time(), validate_time()])
        
        # 添加课程时自动计算下一个课程时间
        calculate_next_course_time()
        end_time_entry.bind("<FocusOut>", lambda e: validate_time())
        
        # 删除按钮
        tk.Button(row_frame, text="×", fg="red", 
                 command=lambda: self.delete_course_row(row_frame)).pack(side=tk.RIGHT)
    
    def delete_course_row(self, row_frame):
        row_frame.destroy()
    
    def _update_suggestions(self, combobox):
        """根据用户输入更新课程名称建议"""
        current_text = combobox.get()
        if not current_text:
            combobox['values'] = list(self._get_all_courses())
            return
        
        suggestions = [course for course in self._get_all_courses() 
                      if current_text.lower() in course.lower()]
        combobox['values'] = suggestions
    
    def _get_all_courses(self):
        """获取所有历史课程名称"""
        all_courses = set()
        for day in self.main_app.schedule.values():
            for course in day:
                all_courses.add(course["name"])
        
        # 获取默认课程
        default_courses = self.main_app.config_handler.default_courses
        
        # 过滤掉用户历史课程中已存在的默认课程
        filtered_default_courses = [course for course in default_courses if course not in all_courses]
        
        # 合并用户历史课程和过滤后的默认课程
        return sorted(all_courses, reverse=True) + filtered_default_courses
    
    def save(self):
        try:
            # 保存所有课程
            for i, day_frame in enumerate(self.day_frames):
                day_schedule = []
                for row_frame in day_frame.winfo_children():
                    if isinstance(row_frame, tk.Frame):
                        entries = [widget for widget in row_frame.winfo_children() 
                                 if isinstance(widget, tk.Entry)]
                        if len(entries) >= 3:
                            start_time = entries[0].get()
                            end_time = entries[1].get()
                            name = entries[2].get()
                            if start_time and end_time and name:
                                day_schedule.append({
                                    "start_time": start_time,
                                    "end_time": end_time,
                                    "name": name
                                })
                self.main_app.schedule[str(i)] = day_schedule
            
            self.main_app.save_schedule()
            messagebox.showinfo("成功", "课表已保存")
        except Exception as e:
            logger.log_error(e)
            messagebox.showerror("错误", "保存课表时发生错误")

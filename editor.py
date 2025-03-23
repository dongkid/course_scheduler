import tkinter as tk
import time
from tkinter import ttk, messagebox, simpledialog
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
        ttk.Button(self.top, text="确定", command=self.on_confirm).pack(pady=10)
    
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
            self.current_schedule = self.main_app.schedule["current_schedule"]
            self.all_courses = self._get_all_courses()  # 初始化时加载所有课程
            self.schedule_times = {}  # 按课表存储课程时间
            for schedule_name in self.main_app.schedule["schedules"]:
                self.schedule_times[schedule_name] = []
            self.last_edited_day = None  # 存储最后编辑的日期
            self.current_schedule = self.main_app.schedule["current_schedule"]
            self.modified = False  # 跟踪课表是否被修改
            self._initialize_ui()
            self._create_schedule_selector()
        except Exception as e:
            logger.log_error(e)
            raise

    def _create_window(self) -> tk.Toplevel:
        """创建并配置编辑窗口"""
        window = tk.Toplevel()
        window.title("课表编辑")
        window.minsize(800, 600)
        return window

    def _create_schedule_selector(self):
        """创建课表选择控件"""
        selector_frame = tk.Frame(self.window)
        selector_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(selector_frame, text="当前课表:").pack(side=tk.LEFT)
        
        self.schedule_var = tk.StringVar(value=self.current_schedule)
        self.schedule_combobox = ttk.Combobox(
            selector_frame,
            textvariable=self.schedule_var,
            state="readonly"
        )
        self.schedule_combobox['values'] = list(self.main_app.schedule["schedules"].keys())
        self.schedule_combobox.pack(side=tk.LEFT, padx=5)
        
        # 添加新课表按钮
        ttk.Button(selector_frame, text="+", command=self._add_new_schedule, width=3, style="Small.TButton").pack(side=tk.LEFT, padx=5)
        
        # 添加复制课表按钮
        self.copy_button = ttk.Button(selector_frame, text="⧉", command=self._copy_schedule, width=3, style="Small.TButton")
        self.copy_button.pack(side=tk.LEFT, padx=5)
        
        # 添加重命名按钮
        self.rename_button = ttk.Button(selector_frame, text="✎", command=self._rename_schedule, width=3, style="Small.TButton")
        self.rename_button.pack(side=tk.LEFT, padx=5)
        
        # 添加删除课表按钮
        self.delete_button = ttk.Button(selector_frame, text="-", command=self._delete_schedule, width=3, style="Small.TButton")
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # 绑定课表切换事件
        self.schedule_combobox.bind("<<ComboboxSelected>>", self._on_schedule_change)

    def _rename_schedule(self):
        """重命名当前课表"""
        old_name = self.schedule_var.get()
        new_name = simpledialog.askstring("重命名课表", "请输入新名称:", initialvalue=old_name)
        
        if not new_name:
            return
            
        if new_name == old_name:
            return
            
        if new_name in self.main_app.schedule["schedules"]:
            messagebox.showerror("错误", "该名称已存在，请使用其他名称")
            return
            
        try:
            # 重命名课表数据
            self.main_app.schedule["schedules"][new_name] = self.main_app.schedule["schedules"].pop(old_name)
            # 更新当前课表名称
            self.current_schedule = new_name
            self.main_app.schedule["current_schedule"] = new_name
            # 更新时间记录
            self.schedule_times[new_name] = self.schedule_times.pop(old_name)
            # 更新选择框
            self.schedule_combobox['values'] = list(self.main_app.schedule["schedules"].keys())
            self.schedule_combobox.set(new_name)
            messagebox.showinfo("成功", "课表已重命名")
        except Exception as e:
            logger.log_error(e)
            messagebox.showerror("错误", f"重命名失败: {str(e)}")

    def _generate_copy_name(self, original_name):
        """生成唯一的副本名称"""
        base_name = f"{original_name}_副本"
        counter = 1
        new_name = base_name
        while new_name in self.main_app.schedule["schedules"]:
            new_name = f"{base_name}{counter}"
            counter += 1
        return new_name

    def _copy_schedule(self):
        """复制当前课表"""
        current_name = self.schedule_var.get()
        new_name = self._generate_copy_name(current_name)
        
        # 深拷贝课表数据
        original_schedule = self.main_app.schedule["schedules"][current_name]
        new_schedule = {
            str(day): [course.copy() for course in courses] 
            for day, courses in original_schedule.items()
        }
        
        # 添加新课表
        self.main_app.schedule["schedules"][new_name] = new_schedule
        self.schedule_times[new_name] = self.schedule_times[current_name].copy()
        
        # 更新选择框
        self.schedule_combobox['values'] = list(self.main_app.schedule["schedules"].keys())
        self.schedule_combobox.set(new_name)
        self.current_schedule = new_name
        self.main_app.schedule["current_schedule"] = new_name
        self._update_ui_with_new_schedule()
        self._reset_modified_flag()

    def _add_new_schedule(self):
        """添加新课表"""
        new_name = simpledialog.askstring("新课表", "请输入新课表名称:")
        if new_name and new_name not in self.main_app.schedule["schedules"]:
            # 初始化新课表
            self.main_app.schedule["schedules"][new_name] = {
                "0": [], "1": [], "2": [], "3": [], 
                "4": [], "5": [], "6": []
            }
            # 初始化新课表的时间记录
            self.schedule_times[new_name] = []
            # 更新选择框
            self.schedule_combobox['values'] = list(self.main_app.schedule["schedules"].keys())
            self.schedule_combobox.set(new_name)
            # 更新当前课表
            self.current_schedule = new_name
            self.main_app.schedule["current_schedule"] = new_name
            # 更新UI
            self._update_ui_with_new_schedule()
            # 标记为未修改
            self._reset_modified_flag()

    def _delete_schedule(self):
        """删除当前课表"""
        if len(self.main_app.schedule["schedules"]) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个课表")
            return
            
        current_schedule = self.schedule_var.get()
        if messagebox.askyesno("删除课表", f"确定要删除课表'{current_schedule}'吗？"):
            # 删除课表
            del self.main_app.schedule["schedules"][current_schedule]
            del self.schedule_times[current_schedule]
            
            # 切换到其他课表
            new_schedule = next(iter(self.main_app.schedule["schedules"]))
            self.schedule_combobox['values'] = list(self.main_app.schedule["schedules"].keys())
            self.schedule_combobox.set(new_schedule)
            self._on_schedule_change()

    def _is_schedule_modified(self):
        """检查当前课表是否有未保存的修改"""
        return self.modified

    def _reset_modified_flag(self):
        """重置修改状态"""
        self.modified = False

    def _on_schedule_change(self, event=None):
        """切换课表时的处理"""
        new_schedule = self.schedule_var.get()
        if new_schedule != self.current_schedule:
            # 保存当前自动计算设置
            original_auto_calculate = self.main_app.config_handler.auto_calculate_next_course
            
            try:
                # 临时禁用自动计算
                self.main_app.config_handler.auto_calculate_next_course = False
                
                # 检查当前课表是否有实际修改
                if self._is_schedule_modified():
                    # 检查是否有课程被添加或修改
                    has_changes = False
                    for day_frame in self.day_frames:
                        for widget in day_frame.winfo_children():
                            if isinstance(widget, tk.Frame):
                                entries = [w for w in widget.winfo_children() if isinstance(w, tk.Entry)]
                                if len(entries) >= 3:
                                    if entries[0].get() != "08:00" or entries[1].get() != "09:00" or entries[2].get():
                                        has_changes = True
                                        break
                        if has_changes:
                            break
                    
                    # 只有实际修改时才提示保存
                    if has_changes and messagebox.askyesno("切换课表", "当前课表有未保存的修改，是否保存？"):
                        self.save()
                
                # 切换到新课表
                self.current_schedule = new_schedule
                self.main_app.schedule["current_schedule"] = new_schedule
                # 确保新课时有时间记录
                if new_schedule not in self.schedule_times:
                    self.schedule_times[new_schedule] = []
                # 更新UI而不重新创建
                self._update_ui_with_new_schedule()
                # 重置修改状态
                self._reset_modified_flag()
                
            finally:
                # 恢复自动计算设置
                self.main_app.config_handler.auto_calculate_next_course = original_auto_calculate

    def _update_ui_with_new_schedule(self):
        """用新课表数据更新现有UI"""
        # 更新每个标签页的内容
        for i, day_frame in enumerate(self.day_frames):
            self.create_day_ui(day_frame, str(i))

    def _initialize_ui(self) -> None:
        """初始化编辑界面"""
        # 初始化缓存
        self._ui_cache = {}
        self._last_suggestions = set()
        
        # 如果已经创建过notebook，直接更新内容
        if hasattr(self, 'notebook'):
            self._update_ui_with_new_schedule()
        else:
            self._create_notebook()
            self._create_save_button()

    def _create_notebook(self) -> None:
        """创建标签页"""
        self.notebook = tk.ttk.Notebook(self.window)
        self.notebook.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 预创建所有标签页
        for i in range(7):
            day_frame = tk.Frame(self.notebook)
            self.day_frames.append(day_frame)
            self.notebook.add(day_frame, text=f"星期{WEEKDAYS[i]}")
            
            # 初始化缓存
            self._ui_cache[str(i)] = {
                'courses': [],
                'last_update': 0
            }
            
            # 直接加载UI
            self.create_day_ui(day_frame, str(i))
            
        # 默认打开当天标签页
        current_weekday = datetime.now().weekday()
        self.notebook.select(current_weekday)

    def _create_save_button(self) -> None:
        """创建保存按钮"""
        # 创建样式
        style = ttk.Style()
        style.configure("Small.TButton", font=("微软雅黑", 8), padding=5)
        
        # 创建保存按钮
        save_button = ttk.Button(
            self.window, 
            text="保存", 
            command=self.save, 
            style="Small.TButton"
        )
        save_button.pack(pady=10)
    
    def create_day_ui(self, frame, day):
        # 清除现有内容
        for widget in frame.winfo_children():
            widget.destroy()
        
        # 添加课程
        courses = self.main_app.schedule["schedules"][self.current_schedule].get(day, [])
        
        # 如果当天没有课程且存在当前课表的上一次课程时间，提示是否导入
        if not courses and self.schedule_times[self.current_schedule] and len(self.schedule_times[self.current_schedule]) > 0:
            if messagebox.askyesno("导入课程时间", "是否导入当前课表的上一次课程时间？"):
                # 导入时禁用自动补全
                auto_complete = self.main_app.config_handler.auto_complete_end_time
                auto_calculate = self.main_app.config_handler.auto_calculate_next_course
                self.main_app.config_handler.auto_complete_end_time = False
                self.main_app.config_handler.auto_calculate_next_course = False
                
                for course_time in self.schedule_times[self.current_schedule]:
                    self.add_course_row(frame, len(courses), {
                        "start_time": course_time["start_time"],
                        "end_time": course_time["end_time"],
                        "name": "示例"
                    })
                
                # 恢复自动补全设置
                self.main_app.config_handler.auto_complete_end_time = auto_complete
                self.main_app.config_handler.auto_calculate_next_course = auto_calculate
                return
        
        # 正常添加课程（禁用自动补全）
        auto_complete = self.main_app.config_handler.auto_complete_end_time
        auto_calculate = self.main_app.config_handler.auto_calculate_next_course
        self.main_app.config_handler.auto_complete_end_time = False
        self.main_app.config_handler.auto_calculate_next_course = False
        
        for i, course in enumerate(courses):
            self.add_course_row(frame, i, course)
        
        # 恢复自动补全设置
        self.main_app.config_handler.auto_complete_end_time = auto_complete
        self.main_app.config_handler.auto_calculate_next_course = auto_calculate
        
        # 更新课程名称建议
        self.all_courses = self._get_all_courses()
        
        # 添加新课程按钮
        style = ttk.Style()
        style.configure("AddSchedule.TButton", font=("微软雅黑", 8), padding=5)
        ttk.Button(frame, text="添加课程", command=lambda: self.add_course_row(frame, len(courses)),style="AddSchedule.TButton").pack(pady=5)
        
        # 绑定标签页切换事件
        def on_tab_change(event):
            selected_tab = self.notebook.index(self.notebook.select())
            self.create_day_ui(self.day_frames[selected_tab], str(selected_tab))
        
        self.notebook.bind("<<NotebookTabChanged>>", on_tab_change)
    
    def add_course_row(self, frame, index, course=None):
        row_frame = tk.Frame(frame)
        row_frame.pack(fill=tk.X, pady=2)
        # 仅在用户实际添加新课程时标记为已修改
        if course is None:
            self.modified = True
        
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
        # 标记为已修改
        self.modified = True
    
    def _update_suggestions(self, combobox):
        """根据用户输入更新课程名称建议"""
        current_text = combobox.get()
        if not current_text:
            # 使用缓存数据
            if not self._last_suggestions:
                self._last_suggestions = set(self._get_all_courses())
            combobox['values'] = list(self._last_suggestions)
            return
        
        # 仅在输入变化时更新建议
        suggestions = [course for course in self._last_suggestions 
                      if current_text.lower() in course.lower()]
        if suggestions:
            combobox['values'] = suggestions
        else:
            # 重新获取所有课程
            self._last_suggestions = set(self._get_all_courses())
            combobox['values'] = [course for course in self._last_suggestions 
                                if current_text.lower() in course.lower()]
    
    def _get_all_courses(self):
        """获取所有历史课程名称"""
        all_courses = set()
        # 遍历当前课表
        current_schedule = self.main_app.schedule["schedules"][self.current_schedule]
        for day in current_schedule.values():
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
            self.schedule_times[self.current_schedule] = []  # 清空当前课表的课程时间
            # 重置修改状态
            self._reset_modified_flag()
            current_schedule = self.main_app.schedule["schedules"][self.current_schedule]
            
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
                                # 如果是最后编辑的日期，保存当前课表的课程时间
                                if str(i) == self.last_edited_day:
                                    self.schedule_times[self.current_schedule].append({
                                        "start_time": start_time,
                                        "end_time": end_time
                                    })
                current_schedule[str(i)] = day_schedule
            
            # 更新最后编辑日期为当前日期
            selected_tab = self.notebook.index(self.notebook.select())
            self.last_edited_day = str(selected_tab)
            
            self.main_app.save_schedule()
            
            # 保存后立即刷新当前标签页
            current_tab = self.notebook.index(self.notebook.select())
            self.create_day_ui(self.day_frames[current_tab], str(current_tab))
            
            messagebox.showinfo("成功", f"课表'{self.current_schedule}'已保存")
        except Exception as e:
            logger.log_error(e)

from typing import List
import tkinter as tk
import uuid
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
            self.window.protocol("WM_DELETE_WINDOW", self._on_close)
            self._init_styles()  # 初始化样式
            self.day_frames: List[tk.Frame] = []
            # 确保存在last_modified字段
            if "last_modified" not in self.main_app.schedule:
                self.main_app.schedule["last_modified"] = datetime.now().timestamp()
            self.current_schedule = self.main_app.schedule["current_schedule"]
            self.all_courses = self._get_all_courses()  # 初始化时加载所有课程
            self.schedule_times = {}  # 按课表存储课程时间
            for schedule_name in self.main_app.schedule["schedules"]:
                self.schedule_times[schedule_name] = []
            self.last_edited_day = None  # 存储最后编辑的日期
            self.current_schedule = self.main_app.schedule["current_schedule"]
            self.modified = False  # 跟踪课表是否被修改
            self.selected_rows = set()  # 存储选中行的ID
            self.previous_tab_index = 0
            self._is_programmatic_tab_change = False
            self.is_dialog_open = False

            # 为临时开关创建BooleanVar
            self.auto_complete_var = tk.BooleanVar(value=self.main_app.config_handler.auto_complete_end_time)
            self.auto_calculate_var = tk.BooleanVar(value=self.main_app.config_handler.auto_calculate_next_course)

            self._initialize_ui()
            self._create_schedule_selector()
            self._create_batch_operations_bar()  # 添加批量操作按钮栏
        except Exception as e:
            logger.log_error(e)
            raise

    def _init_styles(self):
        """初始化控件样式"""
        style = ttk.Style()
        
        # 主窗口样式
        style.configure("Editor.TFrame", background="white")
        
        # Notebook样式 (新增部分)
        style.configure("TNotebook", background="white")
        style.configure("TNotebook.Tab", background="white", padding=[10, 5])
        
        # 按钮样式
        style.configure("Editor.TButton",
                      foreground="#333",
                      background="white",
                      font=("微软雅黑", 9),
                      padding=4)
        style.map("Editor.TButton",
                background=[("active", "#d0d0d0"), ("disabled", "#f0f0f0")])
        
        # 选中行样式
        style.configure("Selected.TFrame", background="white")
        
        # 输入框样式
        style.configure("Editor.TEntry",
                      fieldbackground="white",
                      foreground="#333",
                      padding="3 3 3 3")
        
        # 复选框样式
        style.configure("Editor.TCheckbutton",
                      background="white",
                      font=("微软雅黑", 9))

    def _create_window(self) -> tk.Toplevel:
        """创建并配置编辑窗口"""
        window = tk.Toplevel()
        window.title("课表编辑")
        window.minsize(800, 600)
        window.configure(bg="white")
        return window

    def _create_schedule_selector(self):
        """创建课表选择控件"""
        selector_frame = tk.Frame(self.window, bg="white")
        selector_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(selector_frame, text="当前课表:", bg="white").pack(side=tk.LEFT)
        
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

        # 添加临时控制开关（复选框），放在右侧
        auto_calc_check = ttk.Checkbutton(
            selector_frame,
            text="计算下节课时间",
            variable=self.auto_calculate_var,
            style="Editor.TCheckbutton"
        )
        auto_calc_check.pack(side=tk.RIGHT, padx=5)

        auto_complete_check = ttk.Checkbutton(
            selector_frame,
            text="自动补全结束时间",
            variable=self.auto_complete_var,
            style="Editor.TCheckbutton"
        )
        auto_complete_check.pack(side=tk.RIGHT, padx=5)
        
        # 绑定课表切换事件
        self.schedule_combobox.bind("<<ComboboxSelected>>", self._on_schedule_change)

    def _rename_schedule(self):
        """重命名当前课表"""
        if self.is_dialog_open:
            return
        self.is_dialog_open = True
        try:
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
                self.main_app.schedule["last_modified"] = datetime.now().timestamp() if "last_modified" in self.main_app.schedule else datetime.now().timestamp()
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
        finally:
            self.is_dialog_open = False

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
        self.main_app.schedule["last_modified"] = datetime.now().timestamp()
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
        if self.is_dialog_open:
            return
        self.is_dialog_open = True
        try:
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
        finally:
            self.is_dialog_open = False

    def _delete_schedule(self):
        """删除当前课表"""
        if self.is_dialog_open:
            return
        self.is_dialog_open = True
        try:
            self.main_app.schedule["last_modified"] = datetime.now().timestamp()
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
        finally:
            self.is_dialog_open = False

    def _is_schedule_modified(self):
        """检查当前课表是否有未保存的修改"""
        return self.modified

    def _reset_modified_flag(self):
        """重置修改状态"""
        self.modified = False

    def _on_schedule_change(self, event=None):
        """切换课表时的处理"""
        if self.is_dialog_open:
            return
        self.is_dialog_open = True
        try:
            new_schedule = self.schedule_var.get()
            if new_schedule == self.current_schedule:
                return

            if self.modified:
                response = messagebox.askyesno(
                    "保存更改",
                    "当前课表有未保存的修改，是否保存？",
                    parent=self.window
                )
                if response:  # Yes
                    self.save(show_message=False)
                else:
                    # 不保存，直接切换，后续UI刷新将丢弃更改
                    self._reset_modified_flag()

            # 切换到新课表
            self.current_schedule = new_schedule
            self.main_app.schedule["current_schedule"] = new_schedule
            if new_schedule not in self.schedule_times:
                self.schedule_times[new_schedule] = []
            self._update_ui_with_new_schedule()
            self._reset_modified_flag()
        finally:
            self.is_dialog_open = False

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
        self.notebook = ttk.Notebook(self.window, style="TNotebook")
        self.notebook.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 预创建所有标签页并设置白色背景
        for i in range(7):
            day_frame = tk.Frame(self.notebook, background="white")
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
        self.previous_tab_index = current_weekday
        # 绑定标签页切换事件 (只绑定一次)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        """处理标签页切换事件，增加未保存提示"""
        if self.is_dialog_open:
            self._is_programmatic_tab_change = True
            self.notebook.select(self.previous_tab_index)
            return

        if self._is_programmatic_tab_change:
            self._is_programmatic_tab_change = False
            return

        new_tab_index = self.notebook.index(self.notebook.select())
        if new_tab_index == self.previous_tab_index:
            return

        if self.modified:
            self.is_dialog_open = True
            try:
                response = messagebox.askyesnocancel(
                    "保存更改",
                    f"星期{WEEKDAYS[self.previous_tab_index]}的课程有未保存的修改。是否保存？",
                    parent=self.window
                )
            finally:
                self.is_dialog_open = False

            if response is True:  # Yes
                self._save_day(self.previous_tab_index)
                self._reset_modified_flag()
            elif response is False:  # No
                self._reset_modified_flag()
            else:  # Cancel
                self._is_programmatic_tab_change = True
                self.notebook.select(self.previous_tab_index)
                return

        # 允许切换，更新UI
        try:
            self.create_day_ui(self.day_frames[new_tab_index], str(new_tab_index))
            self.previous_tab_index = new_tab_index
        except tk.TclError:
            pass  # 窗口关闭时可能会引发此错误
    def _on_close(self):
        """处理窗口关闭事件"""
        if self.is_dialog_open:
            return
        self.is_dialog_open = True
        try:
            if self.modified:
                response = messagebox.askyesnocancel(
                    "保存更改",
                    "当前课表有未保存的修改，是否保存？",
                    parent=self.window
                )
                if response is True:  # Yes
                    self.save(show_message=False)
                    self.window.destroy()
                elif response is False:  # No
                    self.window.destroy()
                # else: Cancel, do nothing
            else:
                self.window.destroy()
        finally:
            self.is_dialog_open = False

    def _create_batch_operations_bar(self) -> None:
        """创建批量操作按钮栏"""
        style = ttk.Style()
        style.configure("Batch.TButton",
                      font=("微软雅黑", 9),
                      padding=(8, 4),
                      background="#e0e0e0")
        style.configure("Small.TButton",
                      font=("微软雅黑", 9),
                      padding=(4, 4),
                      width=8)
        
        batch_frame = tk.Frame(self.window, bg="white")
        batch_frame.pack(fill=tk.X, padx=12, pady=8, before=self.notebook)

        # 全选按钮 (左侧)
        ttk.Button(batch_frame, text="☑ 全选",
                 command=self._select_all,
                 style="Small.TButton").pack(side=tk.LEFT, padx=4)

        # 批量操作按钮 (右侧)
        ttk.Button(batch_frame, text="导入课程",
                 command=self._import_from_clipboard,
                 style="Batch.TButton").pack(side=tk.RIGHT, padx=4)
        
        ttk.Button(batch_frame, text="复制选中",
                 command=self._copy_selected,
                 style="Batch.TButton").pack(side=tk.RIGHT, padx=4)
        
        ttk.Button(batch_frame, text="批量删除",
                 command=self._batch_delete,
                 style="Batch.TButton").pack(side=tk.RIGHT, padx=4)

    def _select_all(self):
        """全选/取消全选当前标签页的所有课程行"""
        BG_COLOR_SELECTED = "#e3f2fd"
        BG_COLOR_DEFAULT = "white"
        
        current_tab_index = self.notebook.index(self.notebook.select())
        current_day_frame = self.day_frames[current_tab_index]
        
        # 收集当前标签页所有有效行ID
        row_ids = set()
        for widget in current_day_frame.winfo_children():
            if isinstance(widget, tk.Frame) and hasattr(widget, 'row_id'):
                row_ids.add(widget.row_id) # type: ignore
        
        # 判断全选状态时使用集合包含关系
        all_selected = row_ids.issubset(self.selected_rows)
        
        # 批量更新选中状态
        if all_selected:
            self.selected_rows -= row_ids
        else:
            self.selected_rows.update(row_ids)
        
        # 单次遍历更新界面状态
        for widget in current_day_frame.winfo_children():
            if isinstance(widget, tk.Frame) and hasattr(widget, 'row_id'):
                is_selected = widget.row_id in self.selected_rows # type: ignore
                widget.config(bg=BG_COLOR_SELECTED if is_selected else BG_COLOR_DEFAULT)
                if hasattr(widget, 'check_var'):
                    widget.check_var.set(1 if is_selected else 0) # type: ignore

    def _create_save_button(self) -> None:
        """创建保存按钮"""
        # 创建样式
        style = ttk.Style()
        style.configure("Save.TButton", font=("微软雅黑", 8), padding=(8, 4))
        
        # 创建保存按钮
        save_button = ttk.Button(
            self.window,
            text="保存",
            command=self.save,
            style="Save.TButton"
        )
        save_button.pack(side=tk.BOTTOM, pady=10)
    
    def create_day_ui(self, frame, day):
        # 清除现有内容
        for widget in frame.winfo_children():
            widget.destroy()
        
        courses = self.main_app.schedule["schedules"][self.current_schedule].get(day, [])
        courses_to_display = courses

        # 如果当天没有课程且存在当前课表的上一次课程时间，提示是否导入
        if not courses and self.schedule_times[self.current_schedule]:
            if self.is_dialog_open:
                return
            self.is_dialog_open = True
            try:
                should_import = messagebox.askyesno("导入课程时间", "是否导入当前课表的上一次课程时间？")
            finally:
                self.is_dialog_open = False
            
            if should_import:
                courses_to_display = [{
                    "start_time": ct["start_time"],
                    "end_time": ct["end_time"],
                    "name": "示例"
                } for ct in self.schedule_times[self.current_schedule]]

        # 绘制课程行
        for i, course in enumerate(courses_to_display):
            self.add_course_row(frame, i, course)

        # 更新课程名称建议
        self.all_courses = self._get_all_courses()

        # 添加新课程按钮
        style = ttk.Style()
        style.configure("AddSchedule.TButton", font=("微软雅黑", 8), padding=5)

        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(pady=5)

        # "添加课程"按钮
        # 使用 len(courses_to_display) 来确保索引正确
        ttk.Button(btn_frame, text="添加课程",
                 command=lambda: self.add_course_row(frame, len(courses_to_display)),
                 style="AddSchedule.TButton").pack(side=tk.LEFT, padx=2)
        
    
    def add_course_row(self, parent_frame, index, course=None):
        row_frame = tk.Frame(parent_frame, bg="white", bd=0, relief=tk.FLAT)
        row_frame.pack(fill=tk.X, pady=4, padx=2)
        # 生成唯一且稳定的行ID
        row_id = str(uuid.uuid4())[:8].upper()  # 使用UUID前8位大写字符
        row_frame.row_id = row_id  # type: ignore # 存储唯一ID
        
        
        # 添加勾选框
        row_frame.check_var = tk.IntVar() # type: ignore
        checkbutton = ttk.Checkbutton(
            row_frame,
            variable=row_frame.check_var, # type: ignore
            command=lambda: self._toggle_row_selection(row_id, row_frame),
            style="Editor.TCheckbutton"
        )
        checkbutton.pack(side=tk.LEFT, padx=(4, 0))
        
        # 仅在用户实际添加新课程时标记为已修改
        if course is None:
            self.modified = True
        
        # 开始时间
        start_time_entry = tk.Entry(row_frame, width=6, bd=1, relief=tk.SOLID)
        start_time_entry.insert(0, course["start_time"] if course else "08:00")
        start_time_entry.pack(side=tk.LEFT, padx=4, pady=2)
        row_frame.start_time_entry = start_time_entry # type: ignore
        
        # 开始时间调整按钮
        def show_start_time_picker():
            picker = TimePicker(self.window, start_time_entry.get())
            self.window.wait_window(picker.top)
            if picker.selected_time:
                start_time_entry.delete(0, tk.END)
                start_time_entry.insert(0, picker.selected_time)
                calculate_end_time()
        
        ttk.Button(row_frame, text="🕒", command=show_start_time_picker,
                 style="Editor.TButton").pack(side=tk.LEFT, padx=2)
        
        # 结束时间
        end_time_entry = tk.Entry(row_frame, width=6, bd=1, relief=tk.SOLID)
        end_time_entry.insert(0, course["end_time"] if course else "09:00")
        end_time_entry.pack(side=tk.LEFT, padx=4, pady=2)
        row_frame.end_time_entry = end_time_entry # type: ignore
        
        # 结束时间调整按钮
        def show_end_time_picker():
            picker = TimePicker(self.window, end_time_entry.get())
            self.window.wait_window(picker.top)
            if picker.selected_time:
                end_time_entry.delete(0, tk.END)
                end_time_entry.insert(0, picker.selected_time)
        
        ttk.Button(row_frame, text="🕒", command=show_end_time_picker,
                 style="Editor.TButton").pack(side=tk.LEFT, padx=2)
        
        # 自定义课程名称输入框
        name_entry = tk.Entry(row_frame, bd=1, relief=tk.SOLID)
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
            if not self.auto_complete_var.get():
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
            if not self.auto_calculate_var.get():
                return
            try:
                # 强制UI更新以获得正确的控件位置
                parent_frame.update_idletasks()
                
                # 按视觉Y坐标对所有可见的课程行进行排序
                all_rows = sorted(
                    [w for w in parent_frame.winfo_children() if isinstance(w, tk.Frame) and hasattr(w, 'row_id') and w.winfo_ismapped()],
                    key=lambda w: w.winfo_y()
                )

                # “上一行”是排序列表中的倒数第二个
                previous_row = all_rows[-2] if len(all_rows) > 1 else None

                if previous_row:
                    # 从上一行中找到所有输入框
                    prev_entries = [w for w in previous_row.winfo_children() if isinstance(w, tk.Entry)]
                    
                    # 按视觉X坐标排序，以可靠地识别开始/结束时间框
                    prev_entries.sort(key=lambda w: w.winfo_x())
                    
                    # 结束时间框应该是第二个
                    if len(prev_entries) >= 2:
                        prev_end_time_str = prev_entries[1].get()
                        
                        # 计算新课程的开始时间
                        prev_time = datetime.strptime(prev_end_time_str, "%H:%M")
                        next_start_time = prev_time + timedelta(minutes=self.main_app.config_handler.break_duration)
                        
                        # 更新当前新行的开始时间
                        start_time_entry.delete(0, tk.END)
                        start_time_entry.insert(0, next_start_time.strftime("%H:%M"))
                        
                        # 自动计算新行的结束时间
                        calculate_end_time()
            except (ValueError, IndexError) as e:
                logger.log_debug(f"自动计算下一课程时间失败: {e}")
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
        
        # 仅在用户添加新行时（即 course is None）自动计算下一个课程时间
        if course is None:
            calculate_next_course_time()
        
        end_time_entry.bind("<FocusOut>", lambda e: validate_time())
        
        # 删除按钮
        ttk.Button(row_frame, text="×", command=lambda: self.delete_course_row(row_frame),
                 style="Editor.TButton", width=2).pack(side=tk.RIGHT, padx=2)
        
        # 上移按钮
        def move_up():
            self.move_course_row(row_frame, -1)
        ttk.Button(row_frame, text="↑", command=move_up,
                 style="Editor.TButton", width=2).pack(side=tk.RIGHT, padx=2)
        
        # 下移按钮
        def move_down():
            self.move_course_row(row_frame, 1)
        ttk.Button(row_frame, text="↓", command=move_down,
                 style="Editor.TButton", width=2).pack(side=tk.RIGHT, padx=2)
    
    def delete_course_row(self, row_frame):
        row_frame.destroy()
        # 标记为已修改
        self.modified = True
        
    def move_course_row(self, row_frame, direction):
        """移动课程行位置 - 更安全的实现"""
        parent = row_frame.master
        if not parent.winfo_exists():
            return
            
        # 增强课程行过滤逻辑（保留原始检查条件）
        children = [
            child for child in parent.winfo_children()
            if isinstance(child, tk.Frame)
            and hasattr(child, 'row_id')
            and hasattr(child, 'check_var')
            and child.winfo_ismapped()
        ]
        # 按Y坐标排序并添加调试日志
        children = sorted(children, key=lambda w: w.winfo_y())
        logger.log_debug(f"[子元素列表] {[child.row_id for child in children]}") # type: ignore
        
        # 初始化rows_data前检查有效性
        if not children:
            logger.log_debug("无有效课程行可移动")
            return

        try:
            # 更新内存中的课程顺序
            current_tab = self.notebook.index(self.notebook.select())
            day_str = str(current_tab)
            day_frame = self.day_frames[current_tab]
            
            # 获取当前实际显示的课程行
            visible_rows = [
                row for row in day_frame.winfo_children()
                if isinstance(row, tk.Frame) and
                hasattr(row, 'row_id') and
                row.winfo_ismapped()
            ]
            visible_rows.sort(key=lambda w: w.winfo_y())
            
            # 更新内存中的课程顺序
            # 不立即更新内存数据，等待保存操作
            # 收集所有行的打包信息（带存在性检查）
            rows_data = []
            for child in children:
                if child.winfo_exists():
                    pack_info = child.pack_info()
                    rows_data.append({
                        'widget': child,
                        'pack_options': {
                            'fill': pack_info['fill'],
                            'pady': pack_info['pady'],
                            'padx': pack_info.get('padx', 0)
                        }
                    })
                else:
                    logger.log_debug(f"跳过已销毁元素: {child.row_id}") # type: ignore

        except Exception as e:
            logger.log_error(f"初始化行数据失败: {str(e)}")
            logger.log_debug(f"[错误上下文] children={[c.row_id for c in children]}") # type: ignore
            return
        
        try:
            index = children.index(row_frame)
            new_index = index + direction
            
            # 加强边界检查
            if new_index < 0 or new_index >= len(children):
                logger.log_debug(f"移动被阻止：index={index}, direction={direction}, total={len(children)}")
                return
                
            # 详细调试日志
            logger.log_debug(f"[移动操作] 方向:{direction} 当前索引:{index}->新索引:{new_index}")
            logger.log_debug(f"[移动前顺序] {[child.row_id for child in children]}") # type: ignore
                
            # 收集所有行的当前状态
            rows_data = []
            for child in children:
                pack_info = child.pack_info()
                rows_data.append({
                    'widget': child,
                    'pack_options': {
                        'fill': pack_info['fill'],
                        'pady': pack_info['pady'],
                        'padx': pack_info.get('padx', 0)
                    }
                })
            
            # 安全移动逻辑（带边界检查）
            if 0 <= index < len(rows_data) and 0 <= new_index < len(rows_data):
                moved_item = rows_data.pop(index)
                rows_data.insert(new_index, moved_item)
                
                # 重新pack前验证数据完整性
                for child in children:
                    if child.winfo_exists():
                        child.pack_forget()
                    else:
                        logger.log_debug(f"元素{child.row_id}已不存在，跳过") # type: ignore
                
                for i, item in enumerate(rows_data):
                    if item['widget'].winfo_exists():
                        item['widget'].pack(**item['pack_options'])
                        logger.log_debug(f"[顺序更新] 第{i+1}行 → {item['widget'].row_id} (Y坐标:{item['widget'].winfo_y()})")
                    else:
                        logger.log_debug(f"元素{item['widget'].row_id}已不存在，跳过pack")
            else:
                logger.log_debug(f"无效索引 index={index}, new_index={new_index} 总行数={len(rows_data)}")
            
            # 生成简短唯一ID并获取课程详细信息
            log_id = uuid.uuid4().hex[:8].upper()  # 使用UUID前8位大写字符
            try:
                entries = [w for w in row_frame.winfo_children() if isinstance(w, tk.Entry)]
                start_time = entries[0].get() if len(entries) > 0 else "N/A"
                end_time = entries[1].get() if len(entries) > 1 else "N/A"
                course_name = entries[2].get() if len(entries) > 2 else "N/A"
                
                # 获取当前星期几
                tab_index = self.notebook.index(self.notebook.select())
                weekday = WEEKDAYS[tab_index]
                
                logger.log_debug(
                    f"[{log_id}] 行移动追踪 | "
                    f"星期:{weekday} | "
                    # 使用实际0-based索引显示
                    f"逻辑索引:{index}→{new_index} | 可视顺序:{[c.row_id for c in children]} | 物理位置:{[c.winfo_y() for c in children]} | " # type: ignore
                    f"时间:{start_time}-{end_time} | "
                    f"课程:'{course_name}'"
                )
            except Exception as e:
                logger.log_error(f"日志记录错误: {str(e)}")
            self.modified = True
            
        except Exception as e:
            logger.log_error(f"移动行失败: {str(e)}")
            # 详细记录当前状态
            current_children = [
                child for child in parent.winfo_children()
                if isinstance(child, tk.Frame)
                and hasattr(child, 'row_id')
                and hasattr(child, 'check_var')
                and child.winfo_ismapped()
            ]
            logger.log_debug(f"[错误时子元素] {[child.row_id for child in current_children]}") # type: ignore
            logger.log_debug(f"[当前行Frame状态] winfo_exists: {row_frame.winfo_exists()}, row_id: {getattr(row_frame, 'row_id', '未知')}")
            
            # 安全恢复逻辑（带存在性检查）
            if 'rows_data' in locals():
                try:
                    logger.log_debug("尝试安全恢复布局...")
                    for child in children:
                        if child.winfo_exists():
                            child.pack_forget()
                        else:
                            logger.log_debug(f"元素{child.row_id}已不存在，跳过") # type: ignore
                    
                    for row in rows_data:
                        if row['widget'].winfo_exists():
                            row['widget'].pack(**row['pack_options'])
                            logger.log_debug(f"已恢复行 {row['widget'].row_id}")
                    logger.log_debug("[布局恢复完成]")
                except Exception as restore_error:
                    logger.log_error(f"恢复布局失败: {str(restore_error)}")
            else:
                logger.log_debug("无有效rows_data可用于恢复")
            try:
                for child in children:
                    child.pack_forget()
                for row in rows_data:
                    row['widget'].pack(**row['pack_options'])
                # 记录恢复后的实际顺序
                restored_children = [
                    child for child in parent.winfo_children()
                    if isinstance(child, tk.Frame) and
                    hasattr(child, 'row_id')
                ]
                logger.log_debug(f"[恢复后顺序] {[child.row_id for child in restored_children]}") # type: ignore
            except:
                logger.log_error("恢复原始布局失败")
            
        

    def _batch_delete(self):
        """批量删除选中课程"""
        if self.is_dialog_open:
            return
        self.is_dialog_open = True
        try:
            if not self.selected_rows:
                messagebox.showwarning("提示", "请先选中要删除的课程")
                return
                
            if messagebox.askyesno("确认删除", f"确定要删除选中的{len(self.selected_rows)}个课程吗？"):
                # 遍历所有day_frame查找选中行
                for day_frame in self.day_frames:
                    for row_frame in day_frame.winfo_children():
                        if isinstance(row_frame, tk.Frame) and hasattr(row_frame, 'row_id'):
                            if row_frame.row_id in self.selected_rows: # type: ignore
                                row_frame.destroy()
                                
                self.selected_rows.clear()
                self.modified = True
        finally:
            self.is_dialog_open = False
            
    def _copy_selected(self):
        """复制选中课程到剪贴板"""
        if self.is_dialog_open:
            return
        self.is_dialog_open = True
        try:
            if not self.selected_rows:
                messagebox.showwarning("提示", "请先选中要复制的课程")
                return
                
            courses_data = []
            # 收集选中课程数据
            for day_frame in self.day_frames:
                for row_frame in day_frame.winfo_children():
                    if isinstance(row_frame, tk.Frame) and hasattr(row_frame, 'row_id'):
                        if row_frame.row_id in self.selected_rows: # type: ignore
                            entries = [w for w in row_frame.winfo_children() if isinstance(w, tk.Entry)]
                            if len(entries) >= 3:
                                courses_data.append({
                                    "start_time": entries[0].get(),
                                    "end_time": entries[1].get(),
                                    "name": entries[2].get()
                                })
            
            if courses_data:
                try:
                    import json
                    import pyperclip
                    pyperclip.copy(json.dumps(courses_data))
                    messagebox.showinfo("成功", f"已复制{len(courses_data)}个课程到剪贴板")
                except Exception as e:
                    logger.log_error(e)
                    messagebox.showerror("错误", f"复制失败: {str(e)}")
        finally:
            self.is_dialog_open = False
    
    def _import_from_clipboard(self):
        """从剪贴板导入课程"""
        if self.is_dialog_open:
            return
        self.is_dialog_open = True
        try:
            import json
            import pyperclip
            clipboard_data = pyperclip.paste()
            courses = json.loads(clipboard_data)
            
            if not isinstance(courses, list):
                messagebox.showerror("错误", "剪贴板数据格式不正确")
                return
                
            current_tab = self.notebook.index(self.notebook.select())
            day_frame = self.day_frames[current_tab]
            
            # 获取当前课程数量
            existing_rows = [w for w in day_frame.winfo_children() if isinstance(w, tk.Frame)]
            insert_pos = len(existing_rows)
            
            # 添加课程
            for course in courses:
                if all(k in course for k in ["start_time", "end_time", "name"]):
                    self.add_course_row(day_frame, insert_pos, course)
                    insert_pos += 1
                    
            messagebox.showinfo("成功", f"已导入{len(courses)}个课程")
            self.modified = True
            
        except json.JSONDecodeError:
            messagebox.showerror("错误", "剪贴板中没有有效的课程数据")
        except Exception as e:
            logger.log_error(e)
            messagebox.showerror("错误", f"导入失败: {str(e)}")
        finally:
            self.is_dialog_open = False
    
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
        """获取所有历史课程名称（带缓存机制）"""
        # 使用缓存校验
        if hasattr(self, '_courses_cache'):
            cache_data, schedule_name, modified_time = self._courses_cache
            if (schedule_name == self.current_schedule and
                modified_time == self.main_app.schedule["last_modified"]):
                return cache_data
        
        # 使用集合推导式收集课程名称
        current_schedule = self.main_app.schedule["schedules"][self.current_schedule]
        all_courses = {
            course["name"]
            for day in current_schedule.values()
            for course in day
        }
        
        # 优化默认课程处理：使用集合操作
        default_set = set(self.main_app.config_handler.default_courses)
        filtered_defaults = list(default_set - all_courses)
        
        # 合并结果并缓存
        result = sorted(all_courses) + filtered_defaults
        self._courses_cache = (
            result,
            self.current_schedule,
            self.main_app.schedule.get("last_modified", datetime.now().timestamp())
        )
        return result
    
    def _save_day(self, day_index):
        """保存指定索引日期的课程数据，不进行UI交互。"""
        day_str = str(day_index)
        day_frame = self.day_frames[day_index]
        current_schedule_data = self.main_app.schedule["schedules"][self.current_schedule]

        day_schedule = []
        visible_rows = sorted(
            [row for row in day_frame.winfo_children() if isinstance(row, tk.Frame) and hasattr(row, 'row_id')],
            key=lambda w: w.winfo_y()
        )

        for row in visible_rows:
            entries = [w for w in row.winfo_children() if isinstance(w, tk.Entry)]
            if len(entries) >= 3:
                start_time, end_time, name = entries[0].get(), entries[1].get(), entries[2].get()
                if start_time and end_time and name:
                    day_schedule.append({"start_time": start_time, "end_time": end_time, "name": name})

        current_schedule_data[day_str] = day_schedule
        self.last_edited_day = day_str

        last_edited_day_courses = current_schedule_data.get(self.last_edited_day, [])
        self.schedule_times[self.current_schedule] = [
            {"start_time": c["start_time"], "end_time": c["end_time"]} for c in last_edited_day_courses
        ]

        self.main_app.schedule["last_modified"] = datetime.now().timestamp()
        self.main_app.save_schedule()

    def save(self, show_message=True):
        """保存当前活动标签页的课程。"""
        if self.is_dialog_open:
            return
        self.is_dialog_open = True
        try:
            selected_tab_index = self.notebook.index(self.notebook.select())
            self._save_day(selected_tab_index)
            self._reset_modified_flag()

            if show_message:
                messagebox.showinfo("成功", f"课表'{self.current_schedule}'已保存")

            # 保存后立即刷新当前标签页，以确保显示与数据一致
            day_str = str(selected_tab_index)
            day_frame = self.day_frames[selected_tab_index]
            self.create_day_ui(day_frame, day_str)
        except Exception as e:
            logger.log_error(f"保存课表时发生错误: {e}")
            messagebox.showerror("错误", f"保存失败: {str(e)}")
        finally:
            self.is_dialog_open = False

    def _toggle_row_selection(self, row_id, row_frame):
        """切换行的选中状态"""
        if row_id in self.selected_rows:
            self.selected_rows.remove(row_id)
            row_frame.config(bg="white")
        else:
            self.selected_rows.add(row_id)
            row_frame.config(bg="white")  # 选中行背景色

    def _update_row_visuals(self, row_frame, selected=False):
        """更新行的视觉效果"""
        if selected:
            row_frame.config(bg="#e3f2fd", relief=tk.RAISED, bd=1)
            if hasattr(row_frame, 'check_var'):
                row_frame.check_var.set(1)
        else:
            row_frame.config(bg="white", relief=tk.RIDGE, bd=1)
            if hasattr(row_frame, 'check_var'):
                row_frame.check_var.set(0)

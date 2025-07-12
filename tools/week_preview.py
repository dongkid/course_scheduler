import tkinter as tk
from constants import WEEKDAYS
import sys

# Conditional import for Windows-specific functionality
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

class WeekPreviewWindow(tk.Toplevel):
    """一个半透明、可穿透的窗口，用于预览整周的课表。"""

    def __init__(self, master, app, day_offset=None):
        """
        初始化周课表预览窗口。
        Args:
            master: 父窗口 (主应用的root)。
            app: CourseScheduler 应用实例。
            day_offset (int, optional): 要预览的日期偏移量。None表示整周。
        """
        super().__init__(master)
        self.app = app
        self.config_handler = app.config_handler
        self.day_offset = day_offset
        self.withdraw()  # Initially hidden

        # --- Window Style Configuration ---
        self.overrideredirect(True)  # No borders
        self.attributes('-alpha', 1.0)  # Less transparent for better readability
        self.attributes('-topmost', True) # Always on top

        # --- Click-through Configuration ---
        # On Windows, we use a more robust method for click-through
        # We use a common color and set it to be transparent.
        self.configure(bg='white')
        self.attributes("-transparentcolor", "white")
        if sys.platform == "win32":
            self.after(100, self._set_click_through) # Delay to ensure window handle exists

        self._build_ui()
        
        # Bind destroy event to clean up reference in the main app
        self.bind("<Destroy>", self._on_destroy)

    def _set_click_through(self):
        """(Windows Only) Set window style to be click-through."""
        try:
            hwnd = self.winfo_id()
            # Get current window style
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20) # GWL_EXSTYLE
            # Add WS_EX_TRANSPARENT style, which allows mouse events to fall through
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00000020)
        except Exception as e:
            # Using print because logger might not be available or safe here
            print(f"Failed to set click-through style: {e}")


    def _build_ui(self):
        """根据day_offset构建显示一天或整周课表的UI。"""
        # 清理旧UI（如果存在）
        for widget in self.winfo_children():
            widget.destroy()

        container = tk.Frame(self, bg="white")
        container.pack(padx=10, pady=10, fill="both", expand=True)

        current_schedule_name = self.app.schedule.get("current_schedule", "default")
        schedule_data = self.app.schedule.get("schedules", {}).get(current_schedule_name, {})

        # 1. 估算每个每日课表块的高度
        font_size = self.config_handler.schedule_size
        line_height_estimate = font_size + 10  # 估算每行文本的高度（包括padding）
        day_blocks = []

        if self.day_offset is not None:
            from datetime import datetime, timedelta
            target_date = datetime.now() + timedelta(days=self.day_offset)
            day_indices = [target_date.weekday()]
        else:
            day_indices = range(7)

        for i in day_indices:
            weekday_str = str(i)
            courses_for_day = sorted(schedule_data.get(weekday_str, []), key=lambda x: x['start_time'])
            # 估算高度：1行标题 + max(1, 课程数)行内容
            block_height = line_height_estimate * (1 + max(1, len(courses_for_day)))
            day_blocks.append({
                "day_index": i,
                "height": block_height,
                "courses": courses_for_day
            })

        # 2. 根据屏幕高度决定分多少列
        screen_height = self.winfo_screenheight()
        # 将内容限制在屏幕高度的中间约2/3区域内
        max_column_height = screen_height * (2 / 3)

        columns = []
        current_column = []
        current_height = 0
        for block in day_blocks:
            if current_height + block['height'] > max_column_height and current_column:
                columns.append(current_column)
                current_column = [block]
                current_height = block['height']
            else:
                current_column.append(block)
                current_height += block['height']
        if current_column:
            columns.append(current_column)

        # 3. 使用grid布局创建UI
        for col_idx, column_data in enumerate(columns):
            container.grid_columnconfigure(col_idx, weight=1)
            col_frame = tk.Frame(container, bg="white")
            col_frame.grid(row=0, column=col_idx, sticky='nw', padx=10)

            for block in column_data:
                day_index = block['day_index']
                day_name = WEEKDAYS[day_index]
                courses_for_day = block['courses']

                day_frame = tk.Frame(col_frame, bg="white")
                day_frame.pack(anchor="w", fill="x", pady=5)

                # Day label
                day_label = tk.Label(
                    day_frame, text=f"星期{day_name}",
                    font=("微软雅黑", font_size + 1, "bold"),
                    fg=self.config_handler.font_color, bg="white", anchor='w'
                )
                day_label.pack(fill="x")

                # Course labels
                if not courses_for_day:
                    no_course_label = tk.Label(
                        day_frame, text="  - 无课程 -",
                        font=("微软雅黑", font_size - 1, "italic"),
                        fg="gray", bg="white", anchor='w'
                    )
                    no_course_label.pack(fill="x", padx=10)
                else:
                    for course in courses_for_day:
                        # We'll create a frame to hold the time and name labels separately
                        course_frame = tk.Frame(day_frame, bg="white")
                        course_frame.pack(fill="x", padx=10)

                        time_label = tk.Label(
                            course_frame, text=f"{course['start_time']}",
                            font=("微软雅黑", font_size, "bold"), # Bold time
                            fg=self.config_handler.font_color, bg="white", anchor='w'
                        )
                        time_label.pack(side="left", padx=(2, 5)) # Add some padding

                        name_label = tk.Label(
                            course_frame, text=course['name'],
                            font=("微软雅黑", font_size), # Regular name
                            fg=self.config_handler.font_color, bg="white", anchor='w'
                        )
                        name_label.pack(side="left")

    def show(self):
        """显示窗口并启动自动关闭计时器。"""
        self.update_idletasks() # Ensure dimensions are calculated

        # --- Positioning ---
        main_win_x = self.app.root.winfo_x()
        preview_width = self.winfo_width()
        preview_height = self.winfo_height()
        screen_height = self.winfo_screenheight()

        # Position to the left of the main window
        new_x = main_win_x - preview_width - 10  # 10px padding
        
        # Fallback: If there's no space on the left, position it on the right
        if new_x < 0:
            new_x = self.app.root.winfo_x() + self.app.root.winfo_width() + 10

        # Center the window vertically on the screen
        new_y = (screen_height - preview_height) // 2
        
        # Ensure the window is not placed off-screen
        if new_y < 0:
            new_y = 0

        self.geometry(f"+{new_x}+{new_y}")
        self.deiconify()

        # Auto-hide after 5 seconds
        self.after(5000, self.destroy)

    def _on_destroy(self, event):
        """当窗口被销毁时，通知主应用。"""
        # Check if the event widget is this window itself to avoid handling child widget events
        if event.widget == self:
            self.app.week_preview_window = None
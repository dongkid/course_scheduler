from time import sleep
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import datetime
from logger import logger
import sys, os
import time
from PIL import Image, ImageTk

class MiniWeatherUI(tk.Toplevel):
    """迷你天气信息展示组件"""
    def __init__(self, api, master=None):
        super().__init__(master)
        self.overrideredirect(True)  # 无边框窗口
        self.attributes('-topmost', True)  # 保持窗口置顶
        self.configure(background='white')  # 设置背景颜色
        self.resizable(False, False)  # 禁止调整大小
        self.api = api
        self.current_data = {}
        self._pending_callbacks = []  # 跟踪所有待处理的回调
        
        # 延迟初始化确保主窗口已渲染
        self._pending_callbacks.append(self.after(100, self._initialize_position))
        self._load_icons()
        self._create_widgets()
        self._start_auto_refresh()
        # 15秒后自动关闭
        self._pending_callbacks.append(self.after(15000, self._safe_destroy))
        
        # 绑定主窗口移动事件
        if master:
            self._master_configure_id = master.bind('<Configure>', self._update_position)

    def _safe_destroy(self):
        """安全隐藏窗口并清理资源"""
        try:
            # 取消所有待处理的回调
            for cb in self._pending_callbacks:
                self.after_cancel(cb)
            
            # 停止所有线程和后台任务
            if hasattr(self, '_auto_refresh_thread'):
                self._auto_refresh_thread.join(timeout=1)
            
            # 隐藏窗口
            self.withdraw()
        except tk.TclError as e:
            if "can't invoke \"destroy\" command" not in str(e):
                logger.log_error(f"窗口操作时出错: {str(e)}")
        finally:
            # 确保所有资源释放
            self._pending_callbacks.clear()
            if hasattr(self, 'weather_icon'):
                self.weather_icon = None

    def _initialize_position(self):
        """初始化窗口位置（带重试机制）"""
        def try_calculate(retry_count=0):
            if self.master and retry_count < 3:  # 最多重试3次
                try:
                    self.master.update_idletasks()
                    if self.master.winfo_exists() and self.master.winfo_viewable():
                        self._calculate_position()
                    elif retry_count < 2:  # 前两次重试不报错
                        self.after(100, lambda: try_calculate(retry_count + 1))
                    else:
                        logger.log_warning("主窗口未就绪，使用默认位置")
                        self.geometry("300x100+10+10")
                except tk.TclError as e:
                    if "has been destroyed" in str(e) or "bad window path name" in str(e):
                        logger.log_warning("主窗口已销毁，终止位置初始化")
                    else:
                        logger.log_error(f"位置初始化异常: {str(e)}")
                        self.after(100, lambda: try_calculate(retry_count + 1))
        
        try_calculate()
            
    def _calculate_position(self):
        """计算并更新窗口位置（带调试日志）"""
        try:
            # 检查主窗口是否仍然存在
            if not self.master or not self.master.winfo_exists():
                logger.log_warning("主窗口已销毁，使用默认位置")
                self.geometry("440x120+10+10")
                return

            main_win_x = self.master.winfo_x()
            main_win_y = self.master.winfo_y()
            main_win_width = self.master.winfo_width()
            main_win_height = self.master.winfo_height()
            
            logger.log_debug(f"主窗口位置: X={main_win_x}, Y={main_win_y}, 尺寸: {main_win_width}x{main_win_height}")
            
            # 设置迷你窗口尺寸
            width, height = 440, 120
            
            # 计算位置：主窗口左侧垂直居中
            x = main_win_x - width - 10  # 左侧留10像素间隙
            y = main_win_y + (main_win_height - height) // 2
            
            # 获取屏幕尺寸
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            logger.log_debug(f"屏幕尺寸: {screen_width}x{screen_height}")
            
            # 水平边界检查
            if x < 0:
                x = 10
                logger.log_debug("水平位置超出左边界，已调整")
            elif x + width > screen_width:
                x = screen_width - width - 10
                logger.log_debug("水平位置超出右边界，已调整")
                
            # 垂直边界检查
            if y < 0:
                y = 10
                logger.log_debug("垂直位置超出上边界，已调整")
            elif y + height > screen_height:
                y = screen_height - height - 10
                logger.log_debug("垂直位置超出下边界，已调整")
            
            final_geometry = f"{width}x{height}+{int(x)}+{int(y)}"
            logger.log_debug(f"最终窗口位置: {final_geometry}")
            self.geometry(final_geometry)
            
        except Exception as e:
            logger.log_error(f"位置计算异常: {str(e)}")
            self.geometry("440x120+10+10")  # 回退到默认位置

    def _update_position(self, event=None):
        """当主窗口移动时更新位置（带防抖机制）"""
        if event and event.widget == self.master:
            # 忽略非位置变化事件（如尺寸变化）
            if not hasattr(self, '_last_pos') or (event.x, event.y) != self._last_pos:
                self._last_pos = (event.x, event.y)
                
                # 取消之前的延迟调用
                if hasattr(self, '_position_timer'):
                    self.after_cancel(self._position_timer)
                
                # 添加100ms延迟防抖
                self._position_timer = self.after(100, self._debounced_position_update)

    def _debounced_position_update(self):
        """防抖后的位置更新"""
        if self.master:
            # 检查主窗口是否可见
            try:
                if self.master.state() == 'normal' and self.master.winfo_viewable():
                    self._calculate_position()
            except tk.TclError:
                pass  # 主窗口已销毁

    def _load_icons(self):
        """加载天气图标"""
        from PIL import Image, ImageTk
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, 'res', 'weather_icon.png')
        
        try:
            self.weather_icon = ImageTk.PhotoImage(Image.open(icon_path).resize((32,32)))
        except:
            self.weather_icon = None

    def _create_widgets(self):
        # 设置组件最小宽度和高度
        self.geometry("440x120+10+10")  # 设置固定尺寸和初始位置
        
        # 创建标题行
        title_frame = tk.Frame(self, bg='white')
        title_frame.grid(row=0, column=0, columnspan=3, sticky='ew', padx=5, pady=(5,0))
        
        # 天气图标
        self.icon_label = tk.Label(title_frame, image=self.weather_icon, bg='white')
        self.icon_label.pack(side='left', padx=(0,10))
        
        # 城市名称标签
        self.city_label = tk.Label(
            title_frame,
            font=('微软雅黑', 8),
            foreground='#666666',
            anchor='w',
            text="城市: --",
            bg='white'
        )
        self.city_label.pack(side='left', padx=(0,10))
        
        # 标题和更新时间
        title_label = tk.Label(
            title_frame,
            text="天气预报",
            font=('微软雅黑', 10, 'bold'),
            bg='white'
        )
        title_label.pack(side='left', fill='x', expand=True)
        
        # 更新时间标签
        self.update_label = tk.Label(
            title_frame,
            font=('微软雅黑', 8),
            foreground='#666666',
            anchor='e',
            text="🕒 --:--",
            bg='white'
        )
        self.update_label.pack(side='right', padx=(0, 50))
        
        # 关闭按钮
        self.close_btn = tk.Label(
            self,
            text="×",
            font=('微软雅黑', 12, 'bold'),
            foreground='#999999',
            bg='white',
            cursor='hand2'
        )
        self.close_btn.place(relx=1.0, x=-25, y=5, anchor='ne')
        self.close_btn.bind('<Button-1>', lambda e: self._safe_destroy())
        
        # 创建分隔线（使用Frame代替Separator）
        separator = tk.Frame(self, height=1, bg='#cccccc')
        separator.grid(row=1, column=0, columnspan=3, sticky='ew', padx=5, pady=3)
        
        # 今天天气区域
        today_frame = tk.Frame(self, bg='white')
        today_frame.grid(row=2, column=0, columnspan=3, sticky='ew', padx=5)
        
        # 今天标签
        today_label = tk.Label(
            today_frame,
            text="今天",
            font=('微软雅黑', 9, 'bold'),
            bg='white'
        )
        today_label.grid(row=0, column=0, sticky='w')
        
        # 今天温度显示
        self.temp_label = tk.Label(
            today_frame, 
            font=('微软雅黑', 12, 'bold'),
            anchor='center',
            text="--°",
            bg='white'
        )
        self.temp_label.grid(row=0, column=1, padx=10, sticky='ew')
        
        # 今天天气状态
        self.status_label = tk.Label(
            today_frame,
            font=('微软雅黑', 9),
            anchor='e',
            text="加载中...",
            bg='white'
        )
        self.status_label.grid(row=0, column=2, sticky='e')
        
        # 明天天气区域
        tomorrow_frame = tk.Frame(self, bg='white')
        tomorrow_frame.grid(row=3, column=0, columnspan=3, sticky='ew', padx=5, pady=(5,5))
        
        # 明天标签
        tomorrow_label = tk.Label(
            tomorrow_frame,
            text="明天",
            font=('微软雅黑', 9, 'bold'),
            bg='white'
        )
        tomorrow_label.grid(row=0, column=0, sticky='w')
        
        # 明天温度显示
        self.tomorrow_temp_label = tk.Label(
            tomorrow_frame, 
            font=('微软雅黑', 12, 'bold'),
            anchor='center',
            text="--°",
            bg='white'
        )
        self.tomorrow_temp_label.grid(row=0, column=1, padx=10, sticky='ew')
        
        # 明天天气状态
        self.tomorrow_status_label = tk.Label(
            tomorrow_frame,
            font=('微软雅黑', 9),
            anchor='e',
            text="加载中...",
            bg='white'
        )
        self.tomorrow_status_label.grid(row=0, column=2, sticky='e')
        
        # 列配置
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)
        
        # 行配置
        today_frame.columnconfigure(1, weight=1)
        tomorrow_frame.columnconfigure(1, weight=1)

    def _start_auto_refresh(self):
        def refresh_loop():
            while True:
                self.refresh_weather()
                sleep(1800)  # 每30分钟刷新

        Thread(target=refresh_loop, daemon=True).start()

    def refresh_weather(self):
        location = self.api.config.last_weather_location or "北京"
        location_id = self.api.get_location_id(location)
        if location_id:
            data = self.api.get_3d_weather(location_id)
            if data and len(data) >= 2:
                self.current_data = data[0]  # 今天
                self.tomorrow_data = data[1]  # 明天
                if hasattr(self, 'city_label'):
                    self.city_label.config(text=f"城市: {location}")
                self._update_display()

    def _update_display(self):
        # 更新今天温度
        temp_text = f"{self.current_data.get('tempMax', '--')}° / {self.current_data.get('tempMin', '--')}°"
        self.temp_label.config(text=temp_text)
        
        # 更新今天天气状态
        day_status = self.current_data.get('textDay', '').replace("转", "/")
        night_status = self.current_data.get('textNight', '').replace("转", "/")
        status = f"☀ {day_status} | ☾ {night_status}"
        self.status_label.config(text=status)
        
        # 更新明天温度
        if hasattr(self, 'tomorrow_data'):
            tomorrow_temp = f"{self.tomorrow_data.get('tempMax', '--')}° / {self.tomorrow_data.get('tempMin', '--')}°"
            self.tomorrow_temp_label.config(text=tomorrow_temp)
            
            # 更新明天天气状态
            tomorrow_day = self.tomorrow_data.get('textDay', '').replace("转", "/")
            tomorrow_night = self.tomorrow_data.get('textNight', '').replace("转", "/")
            tomorrow_status = f"☀ {tomorrow_day} | ☾ {tomorrow_night}"
            self.tomorrow_status_label.config(text=tomorrow_status)
            
            # 根据明天温度调整颜色
            tomorrow_max = int(self.tomorrow_data.get('tempMax', 0))
            if tomorrow_max >= 30:
                self.tomorrow_temp_label.config(foreground='#e74c3c')  # 高温红色
            elif tomorrow_max <= 10:
                self.tomorrow_temp_label.config(foreground='#3498db')  # 低温蓝色
            else:
                self.tomorrow_temp_label.config(foreground='#2ecc71')  # 舒适绿色
        
        # 更新时间显示
        now = datetime.datetime.now().strftime("%H:%M")
        self.update_label.config(text=f"🕒 {now}")
        
        # 根据今天温度调整颜色
        temp_max = int(self.current_data.get('tempMax', 0))
        if temp_max >= 30:
            self.temp_label.config(foreground='#e74c3c')  # 高温红色
        elif temp_max <= 10:
            self.temp_label.config(foreground='#3498db')  # 低温蓝色
        else:
            self.temp_label.config(foreground='#2ecc71')  # 舒适绿色

class WeatherUI(tk.Toplevel):
    def __init__(self, api, master=None):
        super().__init__(master)
        self.api = api
        self.current_location = "北京"
        self.configure(background='white')  # 设置主窗口背景
        self.init_ui()
        self.load_default_location()

    def init_ui(self):
        self.title("天气预报")
        self.minsize(600, 500)  # 调整窗口最小尺寸以适应更多内容
        
        main_frame = tk.Frame(self, bg='white')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 地区选择
        location_frame = tk.Frame(main_frame, bg='white')
        location_frame.pack(fill='x', pady=5)
        
        self.location_combo = ttk.Combobox(location_frame)
        self.location_combo.pack(side='left', fill='x', expand=True, padx=(0,5))
        
        self.search_btn = tk.Button(location_frame, text="查询", command=self.search_weather, bg='#f0f0f0')
        self.search_btn.pack(side='left')

        # 天气信息展示
        self.weather_info = tk.Frame(main_frame, bg='white')
        self.weather_info.pack(fill='both', expand=True)
        
        # 初始化三天天气表格（使用ttk.Treeview - 保留，因为tk没有等效组件）
        self.weather_tables = {
            0: ttk.Treeview(self.weather_info, height=8, columns=('value'), show='tree'),
            1: ttk.Treeview(self.weather_info, height=8, columns=('value'), show='tree'),
            2: ttk.Treeview(self.weather_info, height=8, columns=('value'), show='tree')
        }

        # 调整网格布局
        self.weather_info.columnconfigure(1, weight=1)
        
        # 表头
        tk.Label(self.weather_info, text="日期", font=('Arial', 9, 'bold'), bg='white').grid(row=0, column=0, padx=5, pady=2)
        tk.Label(self.weather_info, text="天气详情", font=('Arial', 9, 'bold'), bg='white').grid(row=0, column=1, padx=5, pady=2)
        
        # 配置三天天气行
        for i in range(0, 3):
            tk.Label(self.weather_info, text=["今天", "明天", "后天"][i]+"：", bg='white').grid(row=i+1, column=0, sticky='ne', padx=5, pady=2)
            
            # 表格布局和配置
            self.weather_tables[i].grid(row=i+1, column=1, sticky='nsew', padx=5, pady=2)

    def load_default_location(self):
        """加载默认地区"""
        def fetch_ip_location():
            # 优先使用保存的位置
            try:
                # 等待配置加载完成（最多等待5秒）
                if not self.api.config.config_loaded.wait(timeout=5):
                    logger.log_warning("配置加载超时，使用默认配置")
                    self.api.config.last_weather_location = ""
                
                saved_location = self.api.config.last_weather_location
                if saved_location:
                    logger.log_debug(f"使用保存的地理位置: {saved_location}")
                    self.after(0, lambda: self.location_combo.set(saved_location))
                    self.after(0, self.search_weather)
                    return

                # 没有保存位置时进行网络定位
                location = self.api.get_location_by_ip()
            except Exception as e:
                logger.log_error(f"定位初始化失败: {str(e)}")
                self.after(0, lambda: self.location_combo.set("北京"))
            if location:
                logger.log_debug(f"自动定位结果: {location}")
                # 保存新定位结果
                self.api.config.last_weather_location = location
                self.api.config.save_config()
                self.after(0, lambda: self.location_combo.set(location))
                self.search_weather()
            else:
                logger.log_warning("IP定位失败，使用默认地址北京")
                self.after(0, lambda: self.location_combo.set("北京"))
                self.search_weather()

        Thread(target=fetch_ip_location).start()

    def search_weather(self):
        """执行天气查询"""
        location = self.location_combo.get().strip()
        
        # 处理提示框内容为空的情况（包括全空格情况）
        if not location or location.isspace():
            # 询问是否使用网络定位
            use_geo = messagebox.askyesno("定位确认", "是否使用网络定位当前位置？")
            if use_geo:
                ip_location = self.api.get_location_by_ip()
                if ip_location:
                    location = ip_location
                    self.location_combo.set(location)
                else:
                    messagebox.showwarning("警告", "定位失败，请手动输入地区名称")
                    return
            else:
                # messagebox.showwarning("提示", "请输入查询地区名称")
                # 保存空值并继续查询
                self.api.config.last_weather_location = ""
                self.api.config.save_config()
                return

        # 保存新的查询位置
        if location != self.api.config.last_weather_location:
            self.api.config.last_weather_location = location
            self.api.config.save_config()

        def fetch_weather():
            location_id = self.api.get_location_id(location)
            if not location_id:
                return
            
            weather_data = self.api.get_3d_weather(location_id)
            if weather_data:
                self.after(0, lambda: self.update_weather_display(weather_data))

        Thread(target=fetch_weather).start()

    def update_weather_display(self, data):
        """更新天气显示"""
        today = datetime.datetime.now().date()
        
        for i in range(0, 3):
            date = today + datetime.timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            for day_data in data:
                if day_data["fxDate"] == date_str:
                    text_content = (
                        f"📅 日期：{day_data['fxDate']}\n"
                        f"🌤 白天：{day_data['textDay']}｜🌙 夜间：{day_data['textNight']}\n"
                        f"🌡 温度：{day_data['tempMin']}℃ ~ {day_data['tempMax']}℃\n"
                        f"💨 风速：{day_data['windSpeedDay']}级\n"
                        f"💧 湿度：{day_data['humidity']}%\n\n"
                        f"🌅 日出：{day_data.get('sunrise', '--')}\n"
                        f"🌇 日落：{day_data.get('sunset', '--')}\n"
                        f"☔ 降水：{day_data.get('precip', '0.0')}mm\n"
                        f"☀ 紫外线：{day_data['uvIndex']}级\n"
                        f"📊 气压：{day_data['pressure']}hPa\n"
                        f"👁 能见度：{day_data['vis']}km"
                    )
                    
                    # 清空并更新表格数据
                    self.weather_tables[i].delete(*self.weather_tables[i].get_children())
                    entries = [
                        ("📅 日期", day_data['fxDate']),
                        ("🌤 白天/夜间", f"{day_data['textDay']}｜{day_data['textNight']}"),
                        ("🌡 温度", f"{day_data['tempMin']}℃ ~ {day_data['tempMax']}℃"),
                        ("💨 风速", f"{day_data['windSpeedDay']}级"),
                        ("💧 湿度", f"{day_data['humidity']}%"),
                        ("🌅 日出", day_data.get('sunrise', '--')),
                        ("🌇 日落", day_data.get('sunset', '--')),
                        ("☔ 降水", f"{day_data.get('precip', '0.0')}mm"),
                        ("☀ 紫外线", f"{day_data['uvIndex']}级"),
                        ("📊 气压", f"{day_data['pressure']}hPa"),
                        ("👁 能见度", f"{day_data['vis']}km")
                    ]
                    for item in entries:
                        self.weather_tables[i].insert('', 'end', text=item[0], values=(item[1],))
                    break

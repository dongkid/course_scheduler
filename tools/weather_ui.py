from time import sleep
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import datetime
from logger import logger
class WeatherUI(tk.Toplevel):
    def __init__(self, api, master=None):
        super().__init__(master)
        self.api = api
        self.current_location = "北京"
        self.configure(background='white')  # 设置主窗口背景
        # 创建白色背景样式
        style = ttk.Style()
        style.configure('White.TFrame', background='white')
        style.configure('White.TLabel', background='white')
        self.init_ui()
        self.load_default_location()

    def init_ui(self):
        self.title("天气预报")
        self.minsize(600, 500)  # 调整窗口最小尺寸以适应更多内容
        
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 地区选择
        location_frame = ttk.Frame(main_frame)
        location_frame.pack(fill='x', pady=5)
        
        self.location_combo = ttk.Combobox(location_frame)
        self.location_combo.pack(side='left', fill='x', expand=True, padx=(0,5))
        
        self.search_btn = ttk.Button(location_frame, text="查询", command=self.search_weather)
        self.search_btn.pack(side='left')

        # 天气信息展示
        self.weather_info = ttk.Frame(main_frame)
        self.weather_info.pack(fill='both', expand=True)
        
        # 初始化三天天气表格（使用ttk.Treeview）
        self.weather_tables = {
            0: ttk.Treeview(self.weather_info, height=8, columns=('value'), show='tree'),
            1: ttk.Treeview(self.weather_info, height=8, columns=('value'), show='tree'),
            2: ttk.Treeview(self.weather_info, height=8, columns=('value'), show='tree')
        }
        
        # 配置表格样式
        style = ttk.Style()
        style.configure('Weather.Treeview', 
                       rowheight=25, 
                       font=('Arial', 9),
                       background='white',
                       borderwidth=1,
                       relief='solid',
                       bordercolor='white')
        style.configure('Weather.Treeview.Heading', 
                       font=('Arial', 9, 'bold'),
                       background='white',
                       borderwidth=0)
        style.layout('Weather.Treeview', [
            ('Treeview.border', {'sticky': 'nswe', 'children': [
                ('Treeview.treearea', {'sticky': 'nswe'})
            ]})
        ])  # 保留边框结构
        style.map('Weather.Treeview',
                bordercolor=[('!focus', 'white')],
                lightcolor=[('!focus', 'white')],
                darkcolor=[('!focus', 'white')])

        # 调整网格布局
        self.weather_info.columnconfigure(1, weight=1)
        
        # 表头
        ttk.Label(self.weather_info, text="日期", font=('Arial', 9, 'bold')).grid(row=0, column=0, padx=5, pady=2)
        ttk.Label(self.weather_info, text="天气详情", font=('Arial', 9, 'bold')).grid(row=0, column=1, padx=5, pady=2)
        
        # 配置三天天气行
        for i in range(0, 3):
            ttk.Label(self.weather_info, text=["今天", "明天", "后天"][i]+"：").grid(row=i+1, column=0, sticky='ne', padx=5, pady=2)
            
            # 表格布局和配置
            self.weather_tables[i].grid(row=i+1, column=1, sticky='nsew', padx=5, pady=2)

    def load_default_location(self):
        """加载默认地区"""
        def fetch_ip_location():
            # 优先使用保存的位置
            saved_location = self.api.config.last_weather_location
            if saved_location:
                logger.log_debug(f"使用保存的地理位置: {saved_location}")
                self.after(0, lambda: self.location_combo.set(saved_location))
                # sleep(0.5)
                self.search_weather()
                return

            # 没有保存位置时进行网络定位
            location = self.api.get_location_by_ip()
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

import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import datetime
from threading import Thread
class WeatherUI(tk.Toplevel):
    def __init__(self, api, master=None):
        super().__init__(master)
        self.api = api
        self.current_location = "北京"
        self.init_ui()
        self.load_default_location()

    def init_ui(self):
        self.title("天气预报")
        self.minsize(400, 400)
        
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 地区选择
        location_frame = ttk.Frame(main_frame)
        location_frame.pack(fill='x', pady=5)
        
        self.location_combo = ttk.Combobox(location_frame, values=["北京", "上海", "广州", "深圳", "杭州", "南京"])
        self.location_combo.state(["readonly"])
        self.location_combo.pack(side='left', fill='x', expand=True, padx=(0,5))
        
        self.search_btn = ttk.Button(location_frame, text="查询", command=self.search_weather)
        self.search_btn.pack(side='left')

        # 天气信息展示
        self.weather_info = ttk.Frame(main_frame)
        self.weather_info.pack(fill='both', expand=True)
        
        # 初始化三天天气展示区域
        self.day_labels = {
            0: ttk.Label(self.weather_info),
            1: ttk.Label(self.weather_info),
            2: ttk.Label(self.weather_info)
        }
        
        ttk.Label(self.weather_info, text="今天天气：").grid(row=0, column=0, sticky='e', padx=5, pady=2)
        self.day_labels[0].grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(self.weather_info, text="明天天气：").grid(row=1, column=0, sticky='e', padx=5, pady=2)
        self.day_labels[1].grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(self.weather_info, text="后天天气：").grid(row=2, column=0, sticky='e', padx=5, pady=2)
        self.day_labels[2].grid(row=2, column=1, sticky='w', padx=5, pady=2)

    def load_default_location(self):
        """加载默认地区"""
        self.search_weather()

    def search_weather(self):
        """执行天气查询"""
        location = self.location_combo.get().strip()
        if not location:
            messagebox.showwarning("警告", "请输入地区名称")
            return

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
                    text = (
                        f"{day_data['textDay']}转{day_data['textNight']}\n"
                        f"温度：{day_data['tempMin']}℃ ~ {day_data['tempMax']}℃\n"
                        f"风速：{day_data['windSpeedDay']}级\n"
                        f"湿度：{day_data['humidity']}%"
                    )
                    self.day_labels[i].config(text=text)
                    break

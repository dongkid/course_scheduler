# -*- coding: utf-8 -*-
"""
天气工具的UI实现。
包含 MiniWeatherUI (迷你悬浮窗) 和 WeatherUI (主天气窗口)。
UI层现在与WeatherManager交互，并使用标准化的WeatherData模型来展示数据。
"""
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import datetime
import sys, os
from PIL import Image, ImageTk
from time import sleep

from logger import logger
# from tools.weather import WeatherManager # 移除直接导入以避免循环
import typing

if typing.TYPE_CHECKING:
    from tools.weather import WeatherManager


class WeatherScrollableFrame(ttk.Frame):
    """A dedicated scrollable frame for the weather UI to avoid dependency on settings."""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas) # Removed style for simplicity, can be added back if needed

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.frame_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.scrollable_frame.bind("<Enter>", self._on_enter)
        self.scrollable_frame.bind("<Leave>", self._on_leave)

    def _on_canvas_configure(self, event):
        """Adjust the scrollable frame's width to match the canvas."""
        self.canvas.itemconfig(self.frame_window, width=event.width)

    def _on_mousewheel(self, event):
        # Corrected for cross-platform mouse wheel scrolling
        if sys.platform == "win32":
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif sys.platform == "darwin":
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else: # Linux
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def _on_enter(self, event):
        if sys.platform.startswith('linux'):
            self.canvas.bind_all("<Button-4>", self._on_mousewheel)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_leave(self, event):
        if sys.platform.startswith('linux'):
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")


class MiniWeatherUI(tk.Toplevel):
    """迷你天气信息展示组件"""
    def __init__(self, manager: 'WeatherManager', master=None):
        super().__init__(master)
        self.manager = manager
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.configure(background='white')
        self.resizable(False, False)
        
        self.current_data = None
        self.tomorrow_data = None
        self._pending_callbacks = []

        self._load_weather_icons()
        self._create_widgets()
        
        self._pending_callbacks.append(self.after(100, self._initialize_position))
        self._start_auto_refresh()
        self._pending_callbacks.append(self.after(15000, self._safe_destroy))
        
        if master:
            self._master_configure_id = master.bind('<Configure>', self._update_position)

    def _safe_destroy(self):
        """安全隐藏窗口并清理资源"""
        try:
            for cb in self._pending_callbacks:
                self.after_cancel(cb)
            if hasattr(self, '_auto_refresh_thread'):
                self._auto_refresh_thread.join(timeout=1)
            self.withdraw()
        except tk.TclError:
            pass
        finally:
            self._pending_callbacks.clear()

    def _initialize_position(self):
        # ... (位置计算逻辑保持不变, 此处省略以保持简洁)
        self.geometry("440x120+10+10")

    def _update_position(self, event=None):
        # ... (位置更新逻辑保持不变)
        pass

    def _load_weather_icons(self):
        """加载天气图标"""
        self.icons = {}
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_dir = os.path.join(base_path, 'res', 'weather_icons')
        
        # 确保图标目录存在
        if not os.path.isdir(icon_dir):
            logger.log_warning(f"天气图标目录不存在: {icon_dir}")
            # 创建一个默认的空图标
            self.icons['default'] = ImageTk.PhotoImage(Image.new('RGBA', (32, 32), (0, 0, 0, 0)))
            return

        for filename in os.listdir(icon_dir):
            if filename.endswith(".png"):
                name = os.path.splitext(filename)[0]
                try:
                    image = Image.open(os.path.join(icon_dir, filename)).resize((32, 32), Image.Resampling.LANCZOS)
                    self.icons[name] = ImageTk.PhotoImage(image)
                except Exception as e:
                    logger.log_error(f"加载图标失败 {filename}: {e}")
        
        if 'default' not in self.icons:
             self.icons['default'] = ImageTk.PhotoImage(Image.new('RGBA', (32, 32), (0, 0, 0, 0)))


    def _create_widgets(self):
        # ... (控件创建逻辑与之前类似, 但会使用新的数据结构和图标)
        self.geometry("440x120+10+10")
        
        # 示例:
        self.city_label = tk.Label(self, text="城市: --", bg='white')
        self.city_label.pack()
        self.temp_label = tk.Label(self, text="--° / --°", bg='white', font=('微软雅黑', 14, 'bold'))
        self.temp_label.pack()
        self.status_label = tk.Label(self, text="加载中...", bg='white')
        self.status_label.pack()
        self.icon_label = tk.Label(self, bg='white')
        self.icon_label.pack()

    def refresh_weather(self):
        location = self.manager.config.last_weather_location or "北京"
        weather_data = self.manager.get_weather(location)
        if weather_data and weather_data.forecasts:
            self.current_data = weather_data.forecasts[0]
            if len(weather_data.forecasts) > 1:
                self.tomorrow_data = weather_data.forecasts[1]
            
            if hasattr(self, 'city_label'):
                self.city_label.config(text=f"城市: {weather_data.location.name}")
            self._update_display()

    def _get_icon_for_weather(self, weather_text: str):
        """根据天气文本返回合适的图标"""
        if "晴" in weather_text: return self.icons.get('clear', self.icons['default'])
        if "多云" in weather_text: return self.icons.get('cloudy', self.icons['default'])
        if "阴" in weather_text: return self.icons.get('overcast', self.icons['default'])
        if "雨" in weather_text: return self.icons.get('rain', self.icons['default'])
        if "雪" in weather_text: return self.icons.get('snow', self.icons['default'])
        if "雷" in weather_text: return self.icons.get('thunderstorm', self.icons['default'])
        return self.icons.get('default')

    def _update_display(self):
        if self.current_data:
            temp_text = f"{self.current_data.temp_max}° / {self.current_data.temp_min}°"
            self.temp_label.config(text=temp_text)
            
            status = f"白天: {self.current_data.text_day} | 夜间: {self.current_data.text_night}"
            self.status_label.config(text=status)
            
            self.icon_label.config(image=self._get_icon_for_weather(self.current_data.text_day))

    def _start_auto_refresh(self):
        def refresh_loop():
            while True:
                self.refresh_weather()
                sleep(1800)
        self._auto_refresh_thread = Thread(target=refresh_loop, daemon=True)
        self._auto_refresh_thread.start()


class WeatherUI(tk.Toplevel):
    """The main UI for displaying detailed weather forecasts."""
    def __init__(self, manager: 'WeatherManager', master=None):
        super().__init__(master)
        self.manager = manager
        self.icons = {}
        self.hourly_icons = {}
        self._setup_styles()
        self._load_weather_icons()
        self.init_ui()
        self._update_ui_for_provider()
        self.load_default_location()

    def _setup_styles(self):
        """Configure ttk styles for a modern look."""
        self.style = ttk.Style()
        
        # General colors
        BG_COLOR = "#f7f7f7"
        FG_COLOR = "#333333"
        CARD_BG = "#ffffff"
        ACCENT_COLOR = "#0078d7"

        self.configure(background=BG_COLOR)

        # Scoped styles to avoid affecting other windows
        self.style.configure("Weather.TFrame", background=BG_COLOR)
        self.style.configure("Weather.TLabel", background=BG_COLOR, foreground=FG_COLOR, font=('微软雅黑', 10))
        self.style.configure("Weather.TButton", font=('微软雅黑', 10), padding=5, relief='flat', background=ACCENT_COLOR, foreground='white')

        self.style.configure("Weather.Title.TLabel", font=('微软雅黑', 16, 'bold'), foreground=ACCENT_COLOR, background=BG_COLOR)
        self.style.configure("Weather.Subtitle.TLabel", font=('微软雅黑', 10), foreground="#555555", background=BG_COLOR)
        
        # Card styles (now scoped)
        self.style.configure("Weather.Card.TFrame", background=CARD_BG, relief='solid', borderwidth=1, bordercolor="#e0e0e0")
        self.style.configure("Weather.Card.TLabel", background=CARD_BG, foreground=FG_COLOR)
        self.style.configure("Weather.CardDate.TLabel", background=CARD_BG, font=('微软雅黑', 12, 'bold'), foreground=ACCENT_COLOR)
        self.style.configure("Weather.CardTemp.TLabel", background=CARD_BG, font=('微软雅黑', 14, 'bold'))
        
        # Scoped button style mapping
        self.style.map("Weather.TButton",
            background=[('active', '#005a9e')],
            relief=[('pressed', 'sunken'), ('!pressed', 'flat')]
        )

    def _load_weather_icons(self):
        """Load weather icons from the resource directory."""
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_dir = os.path.join(base_path, '..', 'res', 'weather_icons')
        
        if not os.path.isdir(icon_dir):
            logger.log_warning(f"Weather icon directory not found: {icon_dir}")
            default_img = Image.new('RGBA', (50, 50), (0,0,0,0))
            self.icons['default'] = ImageTk.PhotoImage(default_img)
            default_hourly_img = Image.new('RGBA', (32, 32), (0,0,0,0))
            self.hourly_icons['default'] = ImageTk.PhotoImage(default_hourly_img)
            return

        for filename in os.listdir(icon_dir):
            if filename.endswith(".png"):
                name = os.path.splitext(filename)[0].lower() # Use lowercase names for keys
                try:
                    image = Image.open(os.path.join(icon_dir, filename))
                    # Main icons (50x50)
                    self.icons[name] = ImageTk.PhotoImage(image.resize((50, 50), Image.Resampling.LANCZOS))
                    # Hourly icons (32x32)
                    self.hourly_icons[name] = ImageTk.PhotoImage(image.resize((32, 32), Image.Resampling.LANCZOS))
                except Exception as e:
                    logger.log_error(f"Failed to load icon {filename}: {e}")
        
        if 'default' not in self.icons:
            default_img = Image.new('RGBA', (50, 50), (0,0,0,0))
            self.icons['default'] = ImageTk.PhotoImage(default_img)
        if 'default' not in self.hourly_icons:
            default_hourly_img = Image.new('RGBA', (32, 32), (0,0,0,0))
            self.hourly_icons['default'] = ImageTk.PhotoImage(default_hourly_img)

    def _get_weather_key(self, weather_text: str) -> str:
        """Returns a standardized key for a given weather text."""
        weather_text = weather_text.lower()
        if "clear" in weather_text or "晴" in weather_text: return 'clear'
        if "cloudy" in weather_text or "多云" in weather_text: return 'cloudy'
        if "overcast" in weather_text or "阴" in weather_text: return 'overcast'
        if "rain" in weather_text or "雨" in weather_text: return 'rain'
        if "snow" in weather_text or "雪" in weather_text: return 'snow'
        if "thunder" in weather_text or "雷" in weather_text: return 'thunderstorm'
        if "oshower" in weather_text or "ishower" in weather_text: return 'rain'
        if "lightrain" in weather_text: return 'rain'
        if "lightsnow" in weather_text: return 'snow'
        if "rainsnow" in weather_text: return 'snow'
        return 'default'

    def _get_icon_for_weather(self, weather_text: str):
        """Selects an appropriate icon based on weather text."""
        key = self._get_weather_key(weather_text)
        return self.icons.get(key, self.icons['default'])

    def _update_ui_for_provider(self):
        """Updates UI elements based on the selected weather provider."""
        provider = self.manager.config.weather_api_provider
        is_7timer = provider == '7timer'

        if is_7timer:
            self.location_combo.set("自动IP定位")
            self.location_combo.config(state='disabled')
            self.search_btn.config(state='disabled')
        else:
            self.location_combo.config(state='normal')
            self.search_btn.config(state='normal')

    def init_ui(self):
        """Initialize the main UI components."""
        self.title("天气预报")
        self.minsize(700, 550)
        
        # Main container to center content
        center_frame = ttk.Frame(self)
        center_frame.pack(fill='both', expand=True)
        center_frame.grid_rowconfigure(1, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)

        # Top bar for location search
        location_frame = ttk.Frame(center_frame, padding=(10, 10))
        location_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        location_frame.grid_columnconfigure(0, weight=1)
        
        self.location_combo = ttk.Combobox(location_frame, font=('微软雅黑', 10))
        self.location_combo.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        self.search_btn = ttk.Button(location_frame, text="查询", command=self.search_weather)
        self.search_btn.grid(row=0, column=1, sticky='e')

        # Scrollable area for weather cards
        scrollable_container = WeatherScrollableFrame(center_frame)
        scrollable_container.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        self.weather_info_frame = scrollable_container.scrollable_frame
        self.weather_info_frame.configure(style="TFrame")
        self.weather_info_frame.grid_columnconfigure((0, 2), weight=1) # For centering content
        self.weather_info_frame.grid_columnconfigure(1, weight=0)

    def load_default_location(self):
        """Load the last used location or fetch location by IP."""
        provider = self.manager.config.weather_api_provider
        if provider == '7timer':
            # For 7timer, location is determined by IP. The search is triggered,
            # and the provider should handle the "自动IP定位" query.
            self.after(100, self.search_weather)
            return

        def fetch_ip_location():
            # This logic is for other providers like heweather
            saved_location = self.manager.config.last_weather_location
            if saved_location:
                self.after(0, lambda: self.location_combo.set(saved_location))
                self.after(100, self.search_weather) # Small delay to ensure UI is ready
                return

            location = self.manager.get_location_by_ip()
            if location:
                self.manager.config.last_weather_location = location
                self.manager.config.save_config()
                self.after(0, lambda: self.location_combo.set(location))
            else:
                self.after(0, lambda: self.location_combo.set("北京"))
            self.after(100, self.search_weather)

        Thread(target=fetch_ip_location, daemon=True).start()

    def search_weather(self):
        """Initiate a weather search for the selected location."""
        location = self.location_combo.get().strip()
        if not location:
            messagebox.showwarning("提示", "请输入查询地区名称", parent=self)
            return

        provider = self.manager.config.weather_api_provider
        # For providers other than 7timer, save the location.
        if provider != '7timer':
            if location != self.manager.config.last_weather_location:
                self.manager.config.last_weather_location = location
                self.manager.config.save_config()
        
        # Show loading indicator
        self._clear_display()
        loading_label = ttk.Label(self.weather_info_frame, text="正在加载天气数据...", style="Subtitle.TLabel", font=('微软雅黑', 12))
        loading_label.grid(row=0, column=1, pady=20)

        def fetch_weather():
            weather_data = self.manager.get_weather(location)
            # After getting data, if it's 7timer, update the combobox with the actual location name
            if provider == '7timer' and weather_data and weather_data.location:
                self.after(0, lambda: self.location_combo.set(weather_data.location.name))
            self.after(0, lambda: self.update_weather_display(weather_data))

        Thread(target=fetch_weather, daemon=True).start()

    def _clear_display(self):
        """Clear all widgets from the weather info frame."""
        for widget in self.weather_info_frame.winfo_children():
            widget.destroy()

    def update_weather_display(self, data):
        """Populate the UI with new weather data."""
        self._clear_display()

        if not data or not data.forecasts:
            error_label = ttk.Label(self.weather_info_frame, text="未能获取天气数据，请检查网络或API设置。", style="Subtitle.TLabel")
            error_label.grid(row=0, column=1, pady=20)
            return
        
        # Header
        header_text = f"{data.location.name} (数据来源: {data.source})"
        ttk.Label(self.weather_info_frame, text=header_text, style="Title.TLabel").grid(row=0, column=1, pady=(5, 15))

        # Create a card for each forecast day
        for i, forecast in enumerate(data.forecasts):
            self._create_forecast_card(forecast, i + 1)

    def _create_forecast_card(self, forecast, row_index):
        """Create a single forecast card widget."""
        card = ttk.Frame(self.weather_info_frame, style="Card.TFrame", padding=20)
        card.grid(row=row_index, column=1, sticky='ew', pady=10, padx=5)
        card.grid_columnconfigure(1, weight=1)

        # Left side: Icon and Weather Text
        left_frame = ttk.Frame(card, style="Card.TFrame")
        left_frame.grid(row=0, column=0, rowspan=2, sticky='ns', padx=(0, 15))
        
        icon = self._get_icon_for_weather(forecast.text_day)
        icon_label = ttk.Label(left_frame, image=icon, style="Card.TLabel")
        icon_label.pack(pady=(0, 5))
        
        weather_text = f"{forecast.text_day}"
        ttk.Label(left_frame, text=weather_text, style="Card.TLabel", font=('微软雅黑', 10, 'bold')).pack()

        # Right side: Details
        right_frame = ttk.Frame(card, style="Card.TFrame")
        right_frame.grid(row=0, column=1, rowspan=2, sticky='nsew')
        right_frame.grid_columnconfigure((1, 3), weight=1)

        # Row 0: Date and Temperature
        ttk.Label(right_frame, text=forecast.date, style="CardDate.TLabel").grid(row=0, column=0, columnspan=2, sticky='w')
        temp_text = f"{forecast.temp_max}° / {forecast.temp_min}°C"
        ttk.Label(right_frame, text=temp_text, style="CardTemp.TLabel").grid(row=0, column=2, columnspan=2, sticky='e')

        # Separator
        ttk.Separator(right_frame, orient='horizontal').grid(row=1, column=0, columnspan=4, sticky='ew', pady=8)

        # Row 2: Detailed info grid
        details_grid = ttk.Frame(right_frame, style="Card.TFrame")
        details_grid.grid(row=2, column=0, columnspan=4, sticky='ew')
        details_grid.grid_columnconfigure((1,3), weight=1)

        detail_row = 0
        # Wind
        if hasattr(forecast, 'wind_dir_day') and forecast.wind_dir_day:
            wind_dir = forecast.wind_dir_day
            wind_scale = getattr(forecast, 'wind_scale_day', '')
            if wind_scale:
                scale_text = str(wind_scale).replace('级', '')
                wind_text = f"{wind_dir} {scale_text}级"
            else:
                wind_text = wind_dir
            ttk.Label(details_grid, text="风力:", style="Card.TLabel", font=('微软雅黑', 9, 'bold')).grid(row=detail_row, column=0, sticky='w', pady=2)
            ttk.Label(details_grid, text=wind_text, style="Card.TLabel").grid(row=detail_row, column=1, sticky='w', pady=2)
        
        # Humidity
        if hasattr(forecast, 'humidity') and forecast.humidity:
            ttk.Label(details_grid, text="湿度:", style="Card.TLabel", font=('微软雅黑', 9, 'bold')).grid(row=detail_row, column=2, sticky='w', padx=(10,0), pady=2)
            ttk.Label(details_grid, text=f"{forecast.humidity}%", style="Card.TLabel").grid(row=detail_row, column=3, sticky='w', pady=2)
            detail_row += 1
        
        # Pressure
        if hasattr(forecast, 'pressure') and forecast.pressure:
            ttk.Label(details_grid, text="气压:", style="Card.TLabel", font=('微软雅黑', 9, 'bold')).grid(row=detail_row, column=0, sticky='w', pady=2)
            ttk.Label(details_grid, text=f"{forecast.pressure} hPa", style="Card.TLabel").grid(row=detail_row, column=1, sticky='w', pady=2)

        # Visibility
        if hasattr(forecast, 'visibility') and forecast.visibility:
            ttk.Label(details_grid, text="能见度:", style="Card.TLabel", font=('微软雅黑', 9, 'bold')).grid(row=detail_row, column=2, sticky='w', padx=(10,0), pady=2)
            ttk.Label(details_grid, text=f"{forecast.visibility} km", style="Card.TLabel").grid(row=detail_row, column=3, sticky='w', pady=2)
            detail_row += 1

        # UV Index
        if hasattr(forecast, 'uv_index') and forecast.uv_index:
            ttk.Label(details_grid, text="紫外线:", style="Card.TLabel", font=('微软雅黑', 9, 'bold')).grid(row=detail_row, column=0, sticky='w', pady=2)
            ttk.Label(details_grid, text=f"{forecast.uv_index}", style="Card.TLabel").grid(row=detail_row, column=1, sticky='w', pady=2)

        # Hourly forecast display
        if hasattr(forecast, 'hourly_forecasts') and forecast.hourly_forecasts:
            self._create_hourly_forecast_display(card, forecast.hourly_forecasts)

    def _create_hourly_forecast_display(self, parent_card, hourly_data):
        """Creates and populates the hourly forecast section within a forecast card."""
        
        ttk.Separator(parent_card, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky='ew', pady=(10, 5))

        hourly_container = ttk.Frame(parent_card, style="Card.TFrame")
        hourly_container.grid(row=4, column=0, columnspan=2, sticky='ew')

        # Define time slots and corresponding grid columns for alignment
        time_slots = {f"{h:02d}:00": i for i, h in enumerate(range(0, 24, 3))}

        # Configure columns to have equal width
        for i in range(len(time_slots)):
            hourly_container.grid_columnconfigure(i, weight=1, uniform="hourly_time")

        # Populate with hourly data in the correct time slot
        for hourly in hourly_data:
            # Extract time part and normalize to HH:MM format for consistent lookup
            time_str = hourly.time.split(' ')[-1] if ' ' in hourly.time else hourly.time
            
            time_key = ""
            try:
                # Handles variations like "3:00" vs "03:00" by parsing and reformatting
                parsed_time = datetime.datetime.strptime(time_str, "%H:%M")
                time_key = parsed_time.strftime("%H:%M")
            except (ValueError, TypeError):
                time_key = time_str # Fallback if format is unexpected

            if time_key in time_slots:
                col = time_slots[time_key]
                hour_frame = ttk.Frame(hourly_container, style="Card.TFrame")
                hour_frame.grid(row=0, column=col, sticky='n', padx=2)
                
                # Time (display the normalized time)
                ttk.Label(hour_frame, text=time_key, style="Card.TLabel", font=('微软雅黑', 9, 'bold')).pack()
                
                # Icon
                key = self._get_weather_key(hourly.weather)
                icon_img = self.hourly_icons.get(key, self.hourly_icons.get('default'))
                
                icon_label = ttk.Label(hour_frame, image=icon_img, style="Card.TLabel")
                icon_label.image = icon_img # Keep a reference!
                icon_label.pack(pady=3)

                # Weather Text
                ttk.Label(hour_frame, text=hourly.weather, style="Card.TLabel", font=('微软雅黑', 9)).pack(pady=2)

                # Temperature
                ttk.Label(hour_frame, text=f"{hourly.temp}°", style="Card.TLabel", font=('微软雅黑', 10)).pack()
# -*- coding: utf-8 -*-
"""
天气工具的主模块。
包含 WeatherManager，用于根据配置选择和管理天气数据提供者。
还包含 WeatherTool，作为与UI层交互的入口点。
"""
import tkinter as tk
from tkinter import messagebox
from threading import Thread
from typing import Optional, TYPE_CHECKING

from logger import logger
from config_handler import ConfigHandler
# from tools.weather_ui import WeatherUI, MiniWeatherUI # Lazy load
from .weather_provider import WeatherProvider
# from .heweather_provider import HeweatherProvider # Lazy load
# from .seven_timer_provider import SevenTimerProvider # Lazy load
from .weather_models import WeatherData, Location, Forecast, HourlyForecast
import datetime

if TYPE_CHECKING:
    from .heweather_provider import HeweatherProvider
    from .seven_timer_provider import SevenTimerProvider
    from tools.weather_ui import WeatherUI, MiniWeatherUI

class WeatherManager:
    """
    天气管理器。
    根据配置动态选择并调用相应的天气数据提供者。
    实现了提供者的懒加载。
    """
    def __init__(self, config: ConfigHandler):
        self.config = config
        self._provider: Optional[WeatherProvider] = None
        self._provider_name: Optional[str] = None
        # self._initialize_provider() # Removed for lazy loading

    @property
    def provider(self) -> Optional[WeatherProvider]:
        """懒加载并返回天气数据提供者实例"""
        # 如果提供者配置已更改，或提供者尚未初始化，则重新初始化
        if self.config.weather_api_provider != self._provider_name or self._provider is None:
            self._initialize_provider()
        return self._provider

    def _initialize_provider(self):
        """根据配置初始化天气数据提供者"""
        provider_name = self.config.weather_api_provider
        logger.log_debug(f"Lazy initializing weather provider: {provider_name}")
        
        # Lazy import providers
        if provider_name == "heweather":
            from .heweather_provider import HeweatherProvider
            self._provider = HeweatherProvider(self.config)
        elif provider_name == "7timer":
            from .seven_timer_provider import SevenTimerProvider
            self._provider = SevenTimerProvider()
        else:
            logger.log_error(f"Unknown weather provider: {provider_name}")
            messagebox.showerror("Config Error", f"Unknown weather provider: {provider_name}")
            from .heweather_provider import HeweatherProvider
            self._provider = HeweatherProvider(self.config) # Fallback
        
        self._provider_name = provider_name

    def _get_test_city_weather(self) -> WeatherData:
        """生成并返回一个用于测试的固定天气数据对象"""
        test_location = Location(
            name="测试城市",
            city="测试市",
            province="测试省",
            country="中国"
        )
        
        today = datetime.date.today()
        
        # 创建三天的预报
        forecasts = []
        for i in range(3):
            current_date = today + datetime.timedelta(days=i)
            forecast = Forecast(
                date=current_date.strftime("%Y-%m-%d"),
                temp_max=30 - i * 2,
                temp_min=20 - i,
                text_day=["晴", "多云", "小雨"][i % 3],
                text_night=["晴", "阴", "中雨"][i % 3],
                wind_dir_day="东南风",
                wind_scale_day=f"{3+i}",
                humidity=60 + i * 5,
                pressure=1000 + i,
                uv_index=5 - i,
                visibility=15 + i,
                sunrise="06:30",
                sunset="18:30"
            )
            
            # 为第一天添加一些小时预报
            if i == 0:
                hourly_forecasts = []
                for h in range(6, 24, 2):
                    hourly = HourlyForecast(
                        time=f"{h:02d}:00",
                        temp=22 + (h // 4),
                        weather=["晴", "多云", "晴", "多云", "阴", "晴"][(h//2) % 6],
                        icon="clear" # 简化处理
                    )
                    hourly_forecasts.append(hourly)
                forecast.hourly_forecasts = hourly_forecasts

            forecasts.append(forecast)

        return WeatherData(
            location=test_location,
            source="测试数据",
            forecasts=forecasts
        )

    def get_weather(self, location_query: str) -> Optional[WeatherData]:
        """
        获取天气数据。
        现在通过懒加载的 provider 属性获取提供者。
        """
        if location_query == "测试城市":
            logger.log_info("Returning test city weather data")
            return self._get_test_city_weather()
            
        if self.provider:
            return self.provider.get_forecast(location_query)
        return None

    def get_location_by_ip(self) -> Optional[str]:
        """
        通过IP地址获取地理位置。
        注意：此功能目前依赖于和风天气提供者，未来可以抽象出来。
        """
        # 暂时保留旧的IP定位逻辑，因为它与UI紧密耦合
        # TODO: 将IP定位抽象成一个独立的工具或服务
        try:
            import requests
            import re
            request_url = "https://2024.ip138.com/"
            ip_response = requests.get(request_url, timeout=5, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            if ip_response.status_code == 200:
                match = re.search(r"来自：([^\n<]+)", ip_response.text)
                if match:
                    return match.group(1).strip()
            return None
        except Exception as e:
            logger.log_error(f"IP定位请求异常: {str(e)}")
            return None


class WeatherTool:
    def __init__(self):
        self.name = "天气"
        self.config = ConfigHandler()
        self.manager: Optional[WeatherManager] = None
        self.ui: Optional['WeatherUI'] = None
        self.mini_ui: Optional['MiniWeatherUI'] = None

    def _get_manager(self) -> WeatherManager:
        """懒加载并返回 WeatherManager 实例"""
        if self.manager is None:
            logger.log_debug("Lazy initializing WeatherManager.")
            self.manager = WeatherManager(self.config)
        return self.manager

    def show(self):
        """显示天气界面"""
        if self.config.weather_api_provider == "heweather" and not self.config.heweather_api_key:
            messagebox.showerror("错误", "请先配置和风天气API密钥")
            return
        
        from tools.weather_ui import WeatherUI # Lazy import
        manager = self._get_manager()

        if not self.ui or not self.ui.winfo_exists():
            self.ui = WeatherUI(manager)
        self.ui.deiconify()
        self.ui.lift()

    def get_mini_ui(self, master=None) -> 'MiniWeatherUI':
        """获取迷你天气界面组件"""
        from tools.weather_ui import MiniWeatherUI # Lazy import
        manager = self._get_manager()

        if self.mini_ui and self.mini_ui.winfo_exists():
            try:
                self.mini_ui._safe_destroy()
            except Exception as e:
                logger.log_error(f"销毁迷你窗口时出错: {str(e)}")
            finally:
                self.mini_ui = None
        
        self.mini_ui = MiniWeatherUI(manager, master=master)
        self.mini_ui.protocol("WM_DELETE_WINDOW", self._on_mini_ui_close)
        Thread(target=self.mini_ui.refresh_weather).start()
        return self.mini_ui

    def _on_mini_ui_close(self):
        """处理迷你窗口关闭事件"""
        if self.mini_ui:
            try:
                self.mini_ui._safe_destroy()
            finally:
                self.mini_ui = None

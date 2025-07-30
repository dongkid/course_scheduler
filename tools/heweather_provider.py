# -*- coding: utf-8 -*-
"""
和风天气 API 提供者。
负责与和风天气API交互，并将返回数据转换为标准化的WeatherData格式。
"""
import requests
from tkinter import messagebox
from typing import Optional, List, Dict, Any

from logger import logger
from config_handler import ConfigHandler
from .weather_provider import WeatherProvider
from .weather_models import WeatherData, Forecast, Location

class HeweatherProvider(WeatherProvider):
    """和风天气 API 服务提供者"""

    def __init__(self, config: ConfigHandler):
        self.config = config
        self.base_url = "https://devapi.qweather.com/v7/"
        self.geo_url = "https://geoapi.qweather.com/v2/city/lookup"

    def get_location(self, location_query: str) -> Optional[Location]:
        """通过和风天气GeoAPI获取地理位置信息"""
        if not self.config.heweather_api_key:
            messagebox.showerror("错误", "请先在设置中配置和风天气API密钥")
            return None

        params = {
            "location": location_query,
            "key": self.config.heweather_api_key,
            "range": "cn",
            "number": 1
        }
        try:
            response = requests.get(self.geo_url, params=params, timeout=10)
            response.raise_for_status()  # 检查HTTP错误
            data = response.json()

            if data.get("code") == "200" and data.get("location"):
                loc_data = data["location"][0]
                return Location(
                    name=loc_data.get("name", ""),
                    city=loc_data.get("adm2", ""),
                    province=loc_data.get("adm1", ""),
                    country=loc_data.get("country", ""),
                    lat=float(loc_data.get("lat", 0.0)),
                    lon=float(loc_data.get("lon", 0.0)),
                    id=loc_data.get("id")
                )
            else:
                error_msg = f"地区查询失败: {data.get('code')}"
                logger.log_error(error_msg)
                messagebox.showerror("API错误", error_msg)
                return None
        except requests.exceptions.RequestException as e:
            logger.log_error(f"和风天气地理API请求失败: {e}")
            messagebox.showerror("网络错误", f"无法连接到和风天气地理服务: {e}")
            return None

    def get_forecast(self, location_query: str) -> Optional[WeatherData]:
        """获取3天天气预报"""
        location = self.get_location(location_query)
        if not location or not location.id:
            return None

        if not self.config.heweather_api_key:
            messagebox.showerror("错误", "请先在设置中配置和风天气API密钥")
            return None

        url = f"{self.base_url}weather/3d"
        params = {
            "location": location.id,
            "key": self.config.heweather_api_key
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == "200":
                forecasts = self._parse_forecast_data(data["daily"])
                return WeatherData(
                    location=location,
                    forecasts=forecasts,
                    source="Heweather"
                )
            else:
                error_msg = f"天气查询失败: {data.get('code')}"
                logger.log_error(error_msg)
                messagebox.showerror("API错误", error_msg)
                return None
        except requests.exceptions.RequestException as e:
            logger.log_error(f"和风天气API请求失败: {e}")
            messagebox.showerror("网络错误", f"无法连接到和风天气服务: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.log_error(f"解析和风天气数据失败: {e}")
            messagebox.showerror("数据错误", "无法解析返回的天气数据")
            return None

    def _parse_forecast_data(self, daily_data: List[Dict[str, Any]]) -> List[Forecast]:
        """将API返回的每日预报数据转换为标准格式"""
        parsed_forecasts = []
        for day_data in daily_data:
            forecast = Forecast(
                date=day_data.get("fxDate", ""),
                temp_max=int(day_data.get("tempMax", 0)),
                temp_min=int(day_data.get("tempMin", 0)),
                text_day=day_data.get("textDay", "N/A"),
                text_night=day_data.get("textNight", "N/A"),
                wind_dir_day=day_data.get("windDirDay", ""),
                wind_scale_day=day_data.get("windScaleDay", ""),
                wind_dir_night=day_data.get("windDirNight", ""),
                wind_scale_night=day_data.get("windScaleNight", ""),
                humidity=int(day_data.get("humidity", 0)),
                precip=float(day_data.get("precip", 0.0)),
                pressure=int(day_data.get("pressure", 0)),
                uv_index=int(day_data.get("uvIndex", 0)),
                visibility=int(day_data.get("vis", 0)),
                sunrise=day_data.get("sunrise", "--:--"),
                sunset=day_data.get("sunset", "--:--")
            )
            parsed_forecasts.append(forecast)
        return parsed_forecasts
# -*- coding: utf-8 -*-
"""
7Timer! API 提供者。
负责与7Timer! API交互，并处理地理编码。
"""
import requests
import datetime
import re
import json
from tkinter import messagebox
from typing import Optional, List, Dict, Any

from logger import logger
from .weather_provider import WeatherProvider
from .weather_models import WeatherData, Forecast, Location, HourlyForecast

class SevenTimerProvider(WeatherProvider):
    """7Timer! API 服务提供者"""

    def __init__(self):
        self.base_url = "http://www.7timer.info/bin/api.pl"

    def get_location(self, location_query: str) -> Optional[Location]:
        """
        通过腾讯API获取公网IP，再使用 ip-api.com 进行地理编码。
        `location_query` 参数在此实现中被忽略。
        """
        try:
            # 步骤1: 获取公网IP地址
            ip_check_url = "https://vv.video.qq.com/checktime?otype=ojson"
            ip_response = requests.get(ip_check_url, timeout=5)
            ip_response.raise_for_status()
            ip_data = ip_response.json()
            public_ip = ip_data.get("ip")
            if not public_ip:
                logger.log_error("无法从腾讯API获取IP地址")
                messagebox.showerror("IP获取错误", "无法获取公网IP地址")
                return None

            # 步骤2: 使用IP地址获取地理位置
            geo_url = f"http://ip-api.com/json/{public_ip}"
            params = {
                "fields": "status,message,country,regionName,city,lat,lon,query",
                "lang": "zh-CN"
            }
            geo_response = requests.get(geo_url, params=params, timeout=10)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            if geo_data.get("status") == "success":
                # 使用ip-api返回的城市名作为地名
                city_name = geo_data.get('city', '未知地区')
                return Location(
                    name=city_name,
                    city=city_name,
                    province=geo_data.get('regionName'),
                    country=geo_data.get('country'),
                    lat=geo_data.get('lat'),
                    lon=geo_data.get('lon')
                )
            else:
                error_message = geo_data.get("message", "未知错误")
                logger.log_error(f"ip-api.com 地理编码失败: {error_message}")
                messagebox.showerror("地理编码错误", f"查找IP地址 '{public_ip}' 时出错: {error_message}")
                return None

        except requests.exceptions.RequestException as e:
            logger.log_error(f"地理编码请求失败: {e}")
            messagebox.showerror("网络错误", f"无法连接到地理编码服务: {e}")
            return None
        except (KeyError, ValueError) as e: # ValueError for JSONDecodeError
            logger.log_error(f"解析地理编码数据失败: {e}")
            messagebox.showerror("数据错误", f"解析地理编码数据时出错: {e}")
            return None
        except Exception as e:
            logger.log_error(f"获取地理位置时发生未知错误: {e}")
            messagebox.showerror("未知错误", f"获取地理位置时出错: {e}")
            return None

    def get_forecast(self, location_query: str) -> Optional[WeatherData]:
        """获取7天天气预报"""
        location = self.get_location(location_query)
        if not location or location.lat is None or location.lon is None:
            return None

        params = {
            "lon": location.lon,
            "lat": location.lat,
            "product": "civil",  # 使用civil产品获取7天预报
            "output": "json"
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            # Pre-process the text to fix potential JSON errors from the API
            raw_text = response.text
            # Fix empty values like "key": , by replacing with "key": null,
            # This regex looks for a quoted key, a colon, and a comma, with nothing in between.
            fixed_text = re.sub(r'("[\w\d]+")\s*:\s*,', r'\1: null,', raw_text)
            
            data = json.loads(fixed_text)

            if data and "dataseries" in data and "init" in data:
                logger.log_debug(f"7Timer! API Response (fixed): {data}")
                init_time_str = data.get('init')
                forecasts = self._parse_forecast_data(data["dataseries"], init_time_str)
                return WeatherData(
                    location=location,
                    forecasts=forecasts,
                    source="7Timer!"
                )
            else:
                logger.log_error("7Timer! API未返回有效数据")
                messagebox.showerror("API错误", "7Timer! 服务未返回有效数据")
                return None
        except (requests.exceptions.JSONDecodeError, json.JSONDecodeError) as e:
            logger.log_error(f"7Timer! API JSON Decode Error: {e}")
            # Log the original raw text for debugging
            logger.log_error(f"Raw response text: {response.text}")
            messagebox.showerror("API 数据错误", "7Timer! 服务返回了无效的数据格式。")
            return None
        except requests.exceptions.RequestException as e:
            logger.log_error(f"7Timer! API请求失败: {e}")
            messagebox.showerror("网络错误", f"无法连接到7Timer!服务: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.log_error(f"解析7Timer!数据失败: {e}")
            messagebox.showerror("数据错误", "无法解析返回的天气数据")
            return None

    def _parse_forecast_data(self, dataseries: List[Dict[str, Any]], init_time_str: str) -> List[Forecast]:
        """将API返回的每日预报数据转换为包含分时段预报的标准格式"""
        parsed_forecasts = []
        daily_data = {}  # 使用字典按日期聚合

        try:
            init_time = datetime.datetime.strptime(init_time_str, '%Y%m%d%H')
        except (ValueError, TypeError):
            logger.log_error(f"无效的init时间格式: {init_time_str}, 将使用当前时间")
            init_time = datetime.datetime.now()

        # 步骤1: 遍历API数据，按天分组，并创建分时段预报
        for item in dataseries:
            current_time = init_time + datetime.timedelta(hours=item.get('timepoint', 0))
            date_str = current_time.strftime("%Y-%m-%d")
            time_str = current_time.strftime("%H:%M")

            if date_str not in daily_data:
                daily_data[date_str] = {
                    'temps': [],
                    'weather_codes': [],
                    'humidities': [],
                    'hourly_forecasts': []
                }
            
            # 收集每日聚合所需数据
            temp = item.get('temp2m')
            if temp is not None:
                daily_data[date_str]['temps'].append(temp)

            weather_code = item.get('weather')
            if weather_code:
                daily_data[date_str]['weather_codes'].append(weather_code)
            
            rh_str = item.get('rh2m')
            humidity = None
            if isinstance(rh_str, str) and rh_str.endswith('%'):
                try:
                    humidity = int(rh_str.strip('%'))
                except (ValueError, TypeError):
                    pass
            elif isinstance(rh_str, (int, float)):
                humidity = int(rh_str)
            
            if humidity is not None:
                daily_data[date_str]['humidities'].append(humidity)

            # 创建分时段预报实例
            wind_info = item.get('wind10m', {})
            hourly = HourlyForecast(
                time=time_str,
                temp=temp,
                weather=self._translate_weather(weather_code),
                icon=weather_code,
                humidity=humidity,
                wind_speed=wind_info.get('speed'),
                wind_direction=wind_info.get('direction')
            )
            daily_data[date_str]['hourly_forecasts'].append(hourly)

        # 步骤2: 聚合每日数据并创建最终的Forecast对象
        for date, data in sorted(daily_data.items()):
            if not data['temps']:
                continue

            # 聚合每日数据
            temp_max = max(data['temps'])
            temp_min = min(data['temps'])
            # 找到最频繁出现的天气状况作为当天天气
            day_weather_code = max(set(data['weather_codes']), key=data['weather_codes'].count) if data['weather_codes'] else "N/A"
            avg_humidity = int(sum(data['humidities']) / len(data['humidities'])) if data['humidities'] else None
            
            # 从分时段数据中提取风力信息 (这里简化处理，取第一个)
            first_hourly = data['hourly_forecasts'][0] if data['hourly_forecasts'] else None
            wind_dir_day = first_hourly.wind_direction if first_hourly else "未知"
            wind_scale_day = f"{first_hourly.wind_speed}级" if first_hourly and first_hourly.wind_speed is not None else ""

            forecast = Forecast(
                date=date,
                temp_max=temp_max,
                temp_min=temp_min,
                text_day=self._translate_weather(day_weather_code),
                text_night=self._translate_weather(day_weather_code),  # 7timer不区分日夜
                humidity=avg_humidity,
                wind_dir_day=wind_dir_day,
                wind_scale_day=wind_scale_day,
                wind_dir_night=wind_dir_day,
                wind_scale_night=wind_scale_day,
                hourly_forecasts=data['hourly_forecasts']
            )
            parsed_forecasts.append(forecast)
            
        return parsed_forecasts

    def _wind_speed_to_level(self, speed_ms: float) -> int:
        """将m/s风速转换为风力等级"""
        if speed_ms < 0.3: return 0
        if speed_ms < 1.6: return 1
        if speed_ms < 3.4: return 2
        if speed_ms < 5.5: return 3
        if speed_ms < 8.0: return 4
        if speed_ms < 10.8: return 5
        if speed_ms < 13.9: return 6
        if speed_ms < 17.2: return 7
        if speed_ms < 20.8: return 8
        if speed_ms < 24.5: return 9
        if speed_ms < 28.5: return 10
        if speed_ms < 32.7: return 11
        return 12

    def _wind_direction_to_text(self, degree: float) -> str:
        """将风向角度转换为文本描述"""
        if 337.5 <= degree or degree < 22.5: return "北风"
        if 22.5 <= degree < 67.5: return "东北风"
        if 67.5 <= degree < 112.5: return "东风"
        if 112.5 <= degree < 157.5: return "东南风"
        if 157.5 <= degree < 202.5: return "南风"
        if 202.5 <= degree < 247.5: return "西南风"
        if 247.5 <= degree < 292.5: return "西风"
        if 292.5 <= degree < 337.5: return "西北风"
        return "未知"

    def _translate_weather(self, weather: str) -> str:
        """将7Timer!的天气代码翻译成中文"""
        mapping = {
            "clearday": "晴",
            "clearnight": "晴",
            "pcloudyday": "多云",
            "pcloudynight": "多云",
            "mcloudyday": "阴",
            "mcloudynight": "阴",
            "cloudyday": "阴",
            "cloudynight": "阴",
            "humidday": "潮湿",
            "humidnight": "潮湿",
            "lightrainday": "小雨",
            "lightrainnight": "小雨",
            "oshowerday": "阵雨",
            "oshowernight": "阵雨",
            "ishowerday": "偶有阵雨",
            "ishowernight": "偶有阵雨",
            "lightsnowday": "小雪",
            "lightsnownight": "小雪",
            "rainday": "雨",
            "rainnight": "雨",
            "snowday": "雪",
            "snownight": "雪",
            "rainsnowday": "雨夹雪",
            "rainsnownight": "雨夹雪",
            "tsday": "雷暴",
            "tsnight": "雷暴",
            "tsrainday": "雷阵雨",
            "tsrainnight": "雷阵雨",
        }
        return mapping.get(weather, weather)
# -*- coding: utf-8 -*-
"""
定义天气数据的标准化模型，确保所有天气API提供者返回统一格式的数据。
"""
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class HourlyForecast:
    """标准化的分时段天气预报数据模型"""
    time: str  # 时间, 格式: "HH:MM"
    temp: int  # 温度 (摄氏度)
    weather: str # 天气现象文字
    icon: str # 天气代码 (用于图标匹配), e.g., "pcloudyday"
    humidity: Optional[int] = None # 相对湿度 (%)
    wind_speed: Optional[int] = None # 风力等级
    wind_direction: Optional[str] = None # 风向

@dataclass
class Forecast:
    """标准化的单日天气预报数据模型"""
    date: str  # 日期, 格式: "YYYY-MM-DD"
    temp_max: Optional[int] = None  # 最高温度 (摄氏度)
    temp_min: Optional[int] = None  # 最低温度 (摄氏度)
    
    text_day: str = "N/A"  # 白天天气现象文字
    text_night: str = "N/A" # 夜间天气现象文字
    
    wind_dir_day: Optional[str] = None   # 白天风向
    wind_scale_day: Optional[str] = None # 白天风力等级
    wind_dir_night: Optional[str] = None  # 夜间风向
    wind_scale_night: Optional[str] = None# 夜间风力等级
    
    humidity: Optional[int] = None # 相对湿度 (%)
    precip: Optional[float] = None # 降水量 (mm)
    pressure: Optional[int] = None # 大气压 (hPa)
    uv_index: Optional[int] = None # 紫外线指数
    visibility: Optional[int] = None # 能见度 (km)

    # 天文相关 (可选)
    sunrise: Optional[str] = None # 日出时间, 格式: "HH:MM"
    sunset: Optional[str] = None # 日落时间, 格式: "HH:MM"

    hourly_forecasts: List['HourlyForecast'] = field(default_factory=list)

@dataclass
class Location:
    """标准化的地理位置数据模型"""
    name: str  # 显示名称, e.g., "北京"
    city: str  # 城市
    province: str # 省份
    country: str # 国家
    lat: Optional[float] = None # 纬度
    lon: Optional[float] = None # 经度
    id: Optional[str] = None # API特定的ID, e.g., 和风天气的Location ID

@dataclass
class WeatherData:
    """API返回的完整天气数据封装"""
    location: Location
    source: str  # 数据源, e.g., "Heweather", "7Timer"
    forecasts: List[Forecast] = field(default_factory=list)
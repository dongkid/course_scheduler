# -*- coding: utf-8 -*-
"""
定义天气数据提供者的抽象基类 (ABC)，确保所有提供者都遵循统一的接口。
"""
from abc import ABC, abstractmethod
from typing import Optional
from .weather_models import WeatherData, Location

class WeatherProvider(ABC):
    """天气数据提供者的抽象基类"""

    @abstractmethod
    def get_forecast(self, location_query: str) -> Optional[WeatherData]:
        """
        根据地理位置查询字符串获取天气数据。

        Args:
            location_query (str): 用户输入的地理位置, 如 "北京", "London", "23.09,113.17"。

        Returns:
            Optional[WeatherData]: 包含天气预报的标准化数据对象，失败则返回 None。
        """
        pass

    @abstractmethod
    def get_location(self, location_query: str) -> Optional[Location]:
        """
        根据查询字符串获取标准化的地理位置信息。
        此方法可能涉及地理编码。

        Args:
            location_query (str): 用户输入的地理位置。

        Returns:
            Optional[Location]: 标准化的地理位置对象，失败则返回 None。
        """
        pass
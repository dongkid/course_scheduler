import requests
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.simpledialog import Dialog
from config_handler import ConfigHandler
from tools.weather_ui import WeatherUI
from threading import Thread
import datetime
from logger import logger
class WeatherAPI:
    def __init__(self):
        self.config = ConfigHandler()
        self.config.initialize_config()  # 确保配置加载
        logger.log_debug(f"WeatherAPI初始化 - API Key: {self.config.heweather_api_key}")
        # 直接访问已加载的配置
        self.base_url = "https://devapi.qweather.com/v7/"
        self.geo_url = "https://geoapi.qweather.com/v2/city/lookup"
    
    def get_location_id(self, location_name):
        """获取地区Location ID"""
        headers = {
            "X-QW-Api-Key": f"{self.config.heweather_api_key}"
        }
        params = {
            "location": location_name,
            "range": "cn",
            "number": 1
        }
        try:
            logger.log_debug(f"请求地理API: {self.geo_url}")
            logger.log_debug(f"请求头: {headers}")
            logger.log_debug(f"参数: {params}")
            response = requests.get(self.geo_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Invalid API response format")
            if data.get("code") == "200" and data.get("location"):
                return data["location"][0]["id"]
                
            error_msg = f"地区查询失败: code={data.get('code')}, message={data.get('message')}"
            logger.log_error(error_msg)
            messagebox.showerror("错误", "地区查询失败，请检查地区名称是否正确\n错误信息: " + error_msg)
            return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror("错误", f"网络请求失败：{e}")
            logger.log_error(f"WeatherAPI请求异常：{str(e)}")
            return None
    
    def get_3d_weather(self, location_id):
        """获取三天天气预报"""
        headers = {
            "Authorization": f"Bearer {self.config.heweather_api_key}"
        }
        params = {
            "location": location_id,
            "key": self.config.heweather_api_key
        }
        try:
            # 添加调试信息并修正请求参数
            url = f"{self.base_url}weather/3d"
            logger.log_debug(f"请求天气API: {url}")
            
            # 和风天气要求API key作为查询参数
            params = {
                "location": location_id,
                "key": self.config.heweather_api_key
            }
            logger.log_debug(f"最终请求参数: {params}")
            
            response = requests.get(url, params=params, timeout=10)
            logger.log_debug(f"响应状态码: {response.status_code}")
            logger.log_debug(f"原始响应内容: {response.text[:500]}")  # 截取前500字符避免日志过大
            
            response.raise_for_status()
            data = response.json()
            logger.log_debug(f"解析后的数据: {data}")
            
            if data["code"] == "200":
                return data["daily"]
            messagebox.showwarning("警告", "天气数据获取失败")
            return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror("错误", f"天气请求失败：{e}")
            logger.log_error(f"WeatherAPI请求异常：{str(e)}")
            # 记录响应内容（如果存在）
            if 'response' in locals():
                logger.log_error(f"错误响应内容: {response.text[:1000]}")
        except KeyError as e:
            messagebox.showerror("错误", "天气数据解析失败")
            logger.log_error(f"API响应格式错误：{str(e)}")
            return None

class WeatherTool:
    def __init__(self):
        self.name = "天气"
        self.api = WeatherAPI()
        self.ui = None
        
    def show(self):
        """显示天气界面"""
        if not self.api.config.heweather_api_key:
            messagebox.showerror("错误", "请先配置和风天气API密钥")
            return
            
        if not self.ui:
            self.ui = WeatherUI(self.api)
        self.ui.deiconify()

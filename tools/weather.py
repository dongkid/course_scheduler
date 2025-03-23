import requests
import tkinter as tk
import threading
import time
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
            http_status = response.status_code
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Invalid API response format")
                
            # 添加HTTP状态码处理
            # 地理API特定HTTP错误映射
            HTTP_ERROR_MAP = {
                400: "请求参数错误（请检查地区名称格式）",
                401: "API密钥无效或未经授权",
                403: "访问权限受限（请检查套餐类型）",
                404: "指定的地区不存在",
                429: "请求次数超过限制",
                500: "和风天气服务器内部错误"
            }
            if http_status != 200:
                error_msg = HTTP_ERROR_MAP.get(http_status, f"未知HTTP错误({http_status})")
                logger.log_error(f"HTTP错误 [{http_status}]: {error_msg}")
                messagebox.showerror("HTTP错误", f"{error_msg}\n请检查API地址或网络连接")
                return None
                
            error_code = data.get("code")
            if error_code == "200" and data.get("location"):
                return data["location"][0]["id"]
            
            # 错误码映射表
            ERROR_CODES = {
                "400": "请求参数错误，请检查地区名称格式",
                "401": "API密钥无效或过期，请检查配置",
                "402": "账户余额不足，请及时充值",
                "403": "访问权限受限，请检查套餐权限",
                "404": "指定的地区不存在",
                "429": "请求过于频繁，请稍后重试",
                "500": "服务器内部错误，请稍后再试"
            }
            
            # 优先使用v2错误信息
            if "error" in data:
                error_detail = f"{data['error'].get('title', '')}: {data['error'].get('detail', '')}"
                invalid_params = ", ".join(data['error'].get('invalidParams', []))
                if invalid_params:
                    error_detail += f"\n无效参数: {invalid_params}"
            else:
                error_detail = ERROR_CODES.get(error_code, "未知错误")
            
            error_msg = f"API请求失败 [代码:{error_code}]\n{error_detail}"
            logger.log_error(f"地区查询失败: {error_msg}")
            messagebox.showerror("请求错误", error_msg)
            return None
        except requests.exceptions.RequestException as e:
            http_status = getattr(e.response, 'status_code', '未知')
            error_msg = f"网络请求失败 [HTTP:{http_status}]\n{str(e)}"
            messagebox.showerror("网络错误", error_msg)
            logger.log_error(f"WeatherAPI请求异常: {error_msg}")
            return None
    
    def get_location_by_ip(self):
        """通过IP地址获取地理位置"""
        try:
            request_url = "https://2024.ip138.com/"
            logger.log_debug(f"开始IP定位请求: {request_url}")
            
            ip_response = requests.get(request_url, timeout=5, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            logger.log_debug(f"IP定位响应状态码: {ip_response.status_code}")
            
            if ip_response.status_code == 200:
                # 使用正则表达式提取地理位置信息
                import re
                match = re.search(r"来自：([^\n<]+)", ip_response.text)
                if match:
                    location_str = match.group(1).strip()
                    # 解析格式
                    parts = location_str.split()
                    if len(parts) >= 2:
                        # 提取省份、城市、区县信息
                        area = parts[0][2:]
                        operator = parts[1]  # 运营商信息
                        
                        # 解析省市区（示例：广东深圳福田）
                        province = area[:2] + "省"
                        city = area[2:4] + "市"
                        district = area[4:] if len(area) > 4 else ""
                        
                        detailed_location = f"{province} {city} {district}".strip()
                        
                        logger.log_debug(f"IP定位成功详情: {location_str}")
                        logger.log_debug(f"解析结果: 省份={province} 城市={city} 区/县={district}")
                        logger.log_debug(f"网络运营商: {operator}")
                        
                        return detailed_location
                    
            logger.log_warning(f"IP定位失败: HTTP {ip_response.status_code}")
            return None
        except Exception as e:
            logger.log_error(f"IP定位请求异常: {str(e)}", exc_info=True)
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
            http_status = response.status_code
            logger.log_debug(f"响应状态码: {http_status}")
            logger.log_debug(f"原始响应内容: {response.text[:500]}")  # 截取前500字符避免日志过大
            
            # 预处理HTTP错误
            HTTP_ERROR_MAP = {
                400: "请求参数错误",
                401: "未经授权",
                403: "访问被拒绝",
                404: "API端点不存在",
                429: "请求次数超限",
                500: "服务器内部错误"
            }
            if http_status != 200:
                error_msg = HTTP_ERROR_MAP.get(http_status, f"未知HTTP错误({http_status})")
                logger.error(f"天气API HTTP错误 [{http_status}]: {error_msg}")
                messagebox.showerror("HTTP错误", f"{error_msg}\n请检查API配置")
                return None
                
            data = response.json()
            logger.log_debug(f"解析后的数据: {data}")
            
            error_code = data.get("code")
            if error_code == "200":
                return data["daily"]
            
            # 天气API错误码处理
            WEATHER_ERRORS = {
                "204": "该地区暂无天气数据",
                "400": "请求参数错误，请检查位置ID",
                "401": "API密钥验证失败",
                "402": "账户额度不足，请续费",
                "403": "无权限访问此数据（可能包含：额度用尽/套餐权限不足/安全限制）",
                "404": "天气数据不存在",
                "429": "请求超限（每分钟/每日/每月），请降低频率",
                "500": "服务器内部错误，请稍后重试",
                # v2错误码处理
                "NO_CREDIT": "账户额度不足，请续费（错误码v2）",
                "SECURITY_RESTRICTION": "安全限制，请检查请求频率和权限（错误码v2）",
                "DATA_NOT_AVAILABLE": "该地区数据不可用（错误码v2）"
            }
            
            # 处理v2错误格式
            error_detail = ""
            if "error" in data:
                error_obj = data["error"]
                error_detail = f"{error_obj.get('title', '')}\n{error_obj.get('detail', '')}"
                if error_obj.get('type'):
                    error_detail += f"\n参考文档: {error_obj['type']}"
                if error_obj.get('invalidParams'):
                    error_detail += f"\n无效参数: {', '.join(error_obj['invalidParams'])}"
            else:
                error_detail = WEATHER_ERRORS.get(str(error_code), "未知错误，请检查API响应")
            
            # 添加HTTP状态码信息
            http_status = getattr(response, 'status_code', '未知')
            full_error_msg = f"天气请求失败 [HTTP:{http_status} 代码:{error_code}]\n{error_detail}"
            
            logger.log_error(full_error_msg)
            messagebox.showerror("请求错误", full_error_msg)
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
        self.mini_ui = None
        
    def show(self):
        """显示天气界面"""
        if not self.api.config.heweather_api_key:
            messagebox.showerror("错误", "请先配置和风天气API密钥")
            return
            
        if not self.ui:
            self.ui = WeatherUI(self.api)
        self.ui.deiconify()

    def get_mini_ui(self, master=None):
        """获取迷你天气界面组件"""
        if not self.mini_ui:
            from tools.weather_ui import MiniWeatherUI
            self.mini_ui = MiniWeatherUI(self.api, master=master)
            # 初始加载数据
            Thread(target=self.mini_ui.refresh_weather).start()
        return self.mini_ui

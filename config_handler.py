import json
import os
import threading
from datetime import datetime
from constants import DEFAULT_GEOMETRY, CONFIG_FILE, CONFIG_VERSION

class ConfigHandler:
    def __init__(self):
        self.config = {}
        self.config_loaded = threading.Event()  # 新增配置加载完成事件
        self.initialize_config()  # 确保初始化时加载配置
        self.countdown_name = "高考"
        self.heweather_api_key = ""
        self.countdown_date = datetime(datetime.now().year + 1, 6, 7)
        self.course_duration = 40
        self.auto_start = False
        self.auto_complete_end_time = True
        self.auto_calculate_next_course = True
        self.break_duration = 10
        self.default_courses = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
        self.font_size = 12
        self.font_color = "#000000"
        self.horizontal_padding = 10
        self.vertical_padding = 5
        self.time_display_size = 16
        self.countdown_size = 14
        self.schedule_size = 12
        self.transparent_background = False
        self.fullscreen_subtitle = "祝考生考试顺利"
        self.debug_mode = False
        self.auto_update_check_enabled = False  # 新增：自动更新检查
        self.log_retention_days = 7  # 新增：日志保留天数
        self.geometry = None

    def check_registry_auto_start(self):
        """检查注册表中是否存在开机自启动项"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            value, _ = winreg.QueryValueEx(key, "CourseScheduler")
            winreg.CloseKey(key)
            return value.endswith("course_scheduler.exe")
        except FileNotFoundError:
            return False
        except Exception as e:
            from logger import logger
            logger.log_error(f"注册表检查错误: {str(e)}")
            return False

    def initialize_config(self):
        """加载或初始化配置文件"""
        # 先检查注册表实际状态
        self.auto_start = self.check_registry_auto_start()
        
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                # 加载所有配置项
                self.geometry = self.config.get("geometry", DEFAULT_GEOMETRY)
                self.countdown_name = self.config.get("countdown_name", "高考")
                self.countdown_date = datetime.strptime(
                    self.config.get("countdown_date", f"{datetime.now().year + 1}-06-07"),
                    "%Y-%m-%d"
                )
                self.heweather_api_key = self.config.get("heweather_api_key", "")
                self.course_duration = self.config.get("course_duration", 40)
                self.auto_start = self.config.get("auto_start", False)
                self.auto_complete_end_time = self.config.get("auto_complete_end_time", True)
                self.auto_calculate_next_course = self.config.get("auto_calculate_next_course", True)
                self.break_duration = self.config.get("break_duration", 10)
                self.default_courses = self.config.get("default_courses", ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"])
                self.font_size = int(self.config.get("font_size", 12))
                self.font_color = self.config.get("font_color", "#000000")
                self.time_display_size = self.config.get("time_display_size", 16)
                self.countdown_size = self.config.get("countdown_size", 14)
                self.schedule_size = self.config.get("schedule_size", 12)
                self.fullscreen_subtitle = self.config.get("fullscreen_subtitle", "祝考生考试顺利")
                self.debug_mode = self.config.get("debug_mode", False)
                self.auto_update_check_enabled = self.config.get("auto_update_check_enabled", False)
                self.schedule_rotation_enabled = self.config.get("schedule_rotation_enabled", False)
                self.rotation_schedule1 = self.config.get("rotation_schedule1", "")
                self.rotation_schedule2 = self.config.get("rotation_schedule2", "")
                self.last_weather_location = self.config.get("last_weather_location", "")
                self.countdown_name = self.config.get("countdown_name", "高考")
                self.countdown_date = datetime.strptime(
                    self.config.get("countdown_date", f"{datetime.now().year + 1}-06-07"),
                    "%Y-%m-%d"
                )
                self.heweather_api_key = self.config.get("heweather_api_key", "")
                self.course_duration = self.config.get("course_duration", 40)
                self.auto_start = self.config.get("auto_start", False)
                self.auto_complete_end_time = self.config.get("auto_complete_end_time", True)
                self.auto_calculate_next_course = self.config.get("auto_calculate_next_course", True)
                self.break_duration = self.config.get("break_duration", 10)
                self.default_courses = self.config.get("default_courses", ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"])
                self.font_size = int(self.config.get("font_size", 12))
                self.font_color = self.config.get("font_color", "#000000")
                self.horizontal_padding = self.config.get("horizontal_padding", 5)
                self.vertical_padding = self.config.get("vertical_padding", 5)
                self.time_display_size = self.config.get("time_display_size", 20)
                self.countdown_size = self.config.get("countdown_size", 18)
                self.schedule_size = self.config.get("schedule_size", 18)
                self.transparent_background = self.config.get("transparent_background", True)
        self.fullscreen_subtitle = self.config.get("fullscreen_subtitle", "祝考生考试顺利")
        # 优先读取debug_mode，兼容旧配置debug_enabled
        self.debug_mode = self.config.get("debug_mode", self.config.get("debug_enabled", False))
        self.auto_update_check_enabled = self.config.get("auto_update_check_enabled", False)
        self.log_retention_days = self.config.get("log_retention_days", 7)
        
        # 新增轮换配置
        self.schedule_rotation_enabled = self.config.get("schedule_rotation_enabled", False)
        self.rotation_schedule1 = self.config.get("rotation_schedule1", "")
        self.rotation_schedule2 = self.config.get("rotation_schedule2", "")
        rotation_start_str = self.config.get("rotation_start_date", datetime.now().strftime("%Y-%m-%d"))
        try:
            self.rotation_start_date = datetime.strptime(rotation_start_str, "%Y-%m-%d")
        except ValueError:
            self.rotation_start_date = datetime.now()
        self.last_weather_location = self.config.get("last_weather_location", "")  # 新增天气位置记忆
        
        # 确保所有情况都触发配置加载事件
        self.config_loaded.set()
        
        if not os.path.exists(CONFIG_FILE):
            # 直接创建默认配置文件
            default_config = {
                "geometry": DEFAULT_GEOMETRY,
                "countdown_name": "高考",
                "countdown_date": datetime(datetime.now().year + 1, 6, 7).strftime("%Y-%m-%d"),
                "course_duration": 40,
                "rotation_start_date": datetime.now().strftime("%Y-%m-%d")
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            
            # 重新加载配置
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.geometry = self.config.get("geometry", DEFAULT_GEOMETRY)
            self.gaokao_year = self.config.get("gaokao_year", datetime.now().year + 1)
        else:
            self.config = {"geometry": DEFAULT_GEOMETRY}
            self.geometry = DEFAULT_GEOMETRY
            self.gaokao_year = datetime.now().year + 1
            self.save_config()
    
    def save_config(self):
        """保存当前配置到文件"""
        from logger import logger
        from constants import CONFIG_FILE
        
        # 确保配置目录存在（使用绝对路径）
        config_dir = os.path.abspath(os.path.dirname(CONFIG_FILE))
        os.makedirs(config_dir, exist_ok=True)
        logger.log_debug(f"配置文件目录: {config_dir} 权限: {'可写' if os.access(config_dir, os.W_OK) else '只读'}")
            
        logger.log_debug(f"开始保存配置，最后天气位置: {self.last_weather_location}")
        
        # 准备配置数据（添加窗口位置和缺失的配置项）
        config_data = {
            "config_version": CONFIG_VERSION,
            "geometry": self.geometry if self.geometry else DEFAULT_GEOMETRY,
            "countdown_name": self.countdown_name,
            "countdown_date": self.countdown_date.strftime("%Y-%m-%d"),
            "course_duration": self.course_duration,
            "heweather_api_key": self.heweather_api_key,
            "auto_start": self.auto_start,
            "auto_complete_end_time": self.auto_complete_end_time,
            "auto_calculate_next_course": self.auto_calculate_next_course,
            "break_duration": self.break_duration,
            "default_courses": self.default_courses,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "horizontal_padding": self.horizontal_padding,
            "vertical_padding": self.vertical_padding,
            "time_display_size": self.time_display_size,
            "countdown_size": self.countdown_size,
            "schedule_size": self.schedule_size,
            "transparent_background": self.transparent_background,
            "fullscreen_subtitle": self.fullscreen_subtitle,
            "debug_mode": self.debug_mode,
            "auto_update_check_enabled": self.auto_update_check_enabled,
            "schedule_rotation_enabled": self.schedule_rotation_enabled,
            "rotation_schedule1": self.rotation_schedule1,
            "rotation_schedule2": self.rotation_schedule2,
            "rotation_start_date": self.rotation_start_date.strftime("%Y-%m-%d"),
            "last_weather_location": self.last_weather_location,
            "log_retention_days": self.log_retention_days
        }
        
        try:
            # 使用临时文件写入，避免写入过程中断导致文件损坏
            temp_file = CONFIG_FILE + ".tmp"
            logger.log_debug(f"正在写入临时配置文件: {temp_file}")
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
            # 原子操作替换文件
            if os.path.exists(CONFIG_FILE):
                os.replace(temp_file, CONFIG_FILE)
            else:
                os.rename(temp_file, CONFIG_FILE)
                
            logger.log_debug(f"配置保存成功，文件大小: {os.path.getsize(CONFIG_FILE)} bytes")
            
            # 保存后立即重新加载验证（先清除已加载配置）
            self.config = {}
            self.initialize_config()
        except PermissionError as e:
            logger.log_error(f"配置文件写入权限被拒绝: {str(e)}，请检查文件权限或是否被其他程序占用")
        except json.JSONEncodeError as e:
            logger.log_error(f"配置数据序列化失败: {str(e)}，配置内容: {config_data}")
        except OSError as e:
            logger.log_error(f"文件系统错误: {str(e)}，错误代码: {e.errno}")
        except Exception as e:
            logger.log_error(f"保存配置失败: {str(e)}", exc_info=True)
            raise  # 重新抛出异常让上层处理

import json
import os
import threading
from datetime import datetime
from constants import DEFAULT_GEOMETRY, CONFIG_FILE

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
        self.geometry = None

    def initialize_config(self):
        """加载或初始化配置文件"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
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
                self.horizontal_padding = self.config.get("horizontal_padding", 10)
                self.vertical_padding = self.config.get("vertical_padding", 5)
                self.time_display_size = self.config.get("time_display_size", 20)
                self.countdown_size = self.config.get("countdown_size", 18)
                self.schedule_size = self.config.get("schedule_size", 16)
                self.transparent_background = self.config.get("transparent_background", False)
        self.fullscreen_subtitle = self.config.get("fullscreen_subtitle", "祝考生考试顺利")
        # 优先读取debug_mode，兼容旧配置debug_enabled
        self.debug_mode = self.config.get("debug_mode", self.config.get("debug_enabled", False))
        
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
        
        if os.path.exists(CONFIG_FILE):
            pass
        else:
            self.config = {"geometry": DEFAULT_GEOMETRY}
            self.geometry = DEFAULT_GEOMETRY
            self.countdown_name = "高考"
            self.countdown_date = datetime(datetime.now().year + 1, 6, 7)
            self.course_duration = 40
            self.save_config()

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
        logger.log_debug(f"开始保存配置，最后天气位置: {self.last_weather_location}")
        
        self.config["geometry"] = self.geometry
        self.config["countdown_name"] = self.countdown_name
        self.config["countdown_date"] = self.countdown_date.strftime("%Y-%m-%d")
        self.config["course_duration"] = self.course_duration
        self.config["heweather_api_key"] = self.heweather_api_key
        self.config["auto_complete_end_time"] = self.auto_complete_end_time
        self.config["auto_calculate_next_course"] = self.auto_calculate_next_course
        self.config["break_duration"] = self.break_duration
        self.config["default_courses"] = self.default_courses
        self.config["font_size"] = self.font_size
        self.config["font_color"] = self.font_color
        self.config["horizontal_padding"] = self.horizontal_padding
        self.config["vertical_padding"] = self.vertical_padding
        self.config["time_display_size"] = self.time_display_size
        self.config["countdown_size"] = self.countdown_size
        self.config["schedule_size"] = self.schedule_size
        self.config["transparent_background"] = self.transparent_background
        self.config["fullscreen_subtitle"] = self.fullscreen_subtitle
        self.config["debug_mode"] = self.debug_mode
        # 新增轮换配置保存
        self.config["schedule_rotation_enabled"] = self.schedule_rotation_enabled
        self.config["rotation_schedule1"] = self.rotation_schedule1
        self.config["rotation_schedule2"] = self.rotation_schedule2
        self.config["rotation_start_date"] = self.rotation_start_date.strftime("%Y-%m-%d")
        self.config["last_weather_location"] = self.last_weather_location
        
        try:
            logger.log_debug(f"正在写入配置文件: {CONFIG_FILE}")
            logger.log_debug(f"完整配置内容: {self.config}")
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.log_debug("配置保存成功")
        except Exception as e:
            logger.log_error(f"保存配置失败: {str(e)}", exc_info=True)

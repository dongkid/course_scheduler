import json
import os
import threading
from datetime import datetime
from constants import DEFAULT_GEOMETRY, CONFIG_FILE, CONFIG_VERSION
from tools.config_converter import convert_v1_to_v2

class ConfigHandler:
    def __init__(self):
        self.config = {}
        self.config_loaded = threading.Event()
        self.initialize_config()

    def _set_default_attributes(self):
        """设置所有配置属性的默认值"""
        self.geometry = DEFAULT_GEOMETRY
        self.countdown_name = "高考"
        self.countdown_date = datetime(datetime.now().year + 1, 6, 7)
        self.heweather_api_key = ""
        self.course_duration = 40
        self.auto_start = self.check_registry_auto_start()
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
        self.auto_update_check_enabled = False
        self.log_retention_days = 7
        self.check_prerelease = False
        self.auto_preview_tomorrow_enabled = False
        self.schedule_rotation_enabled = False
        self.rotation_schedule1 = ""
        self.rotation_schedule2 = ""
        self.rotation_start_date = datetime.now()
        self.last_weather_location = ""

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
        """加载或初始化配置文件，并处理版本迁移"""
        self._set_default_attributes()

        if not os.path.exists(CONFIG_FILE):
            self._create_default_config_file()
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                loaded_config = json.load(f)
            except json.JSONDecodeError:
                self._create_default_config_file()
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f_retry:
                    loaded_config = json.load(f_retry)

        # 检查并转换旧版本配置
        if "config_version" not in loaded_config or loaded_config.get("config_version") != CONFIG_VERSION:
            # 转换旧配置，此时 self.config 拥有了完整的 v2 结构和合并后的数据
            self.config = convert_v1_to_v2(loaded_config)
            # 关键修复：先加载属性，再统一保存
        else:
            self.config = loaded_config

        self._load_attributes_from_config()
        self.save_config() # 确保无论初始化路径如何，最终配置都保存一次
        self.config_loaded.set()

    def _create_default_config_file(self):
        """创建一个全新的默认v2配置文件"""
        default_settings = {
            "geometry": DEFAULT_GEOMETRY,
            "countdown_name": "高考",
            "countdown_date": datetime(datetime.now().year + 1, 6, 7).strftime("%Y-%m-%d"),
            "course_duration": 40,
            "auto_start": False,
            "auto_complete_end_time": True,
            "auto_calculate_next_course": True,
            "break_duration": 10,
            "default_courses": ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"],
            "font_size": 12,
            "font_color": "#000000",
            "horizontal_padding": 10,
            "vertical_padding": 5,
            "time_display_size": 16,
            "countdown_size": 14,
            "schedule_size": 12,
            "transparent_background": False,
            "fullscreen_subtitle": "祝考生考试顺利",
            "debug_mode": False,
            "auto_update_check_enabled": False,
            "log_retention_days": 7,
            "check_prerelease": False,
            "auto_preview_tomorrow_enabled": False,
            "schedule_rotation_enabled": False,
            "rotation_schedule1": "",
            "rotation_schedule2": "",
            "rotation_start_date": datetime.now().strftime("%Y-%m-%d"),
            "last_weather_location": ""
        }
        self.config = {
            "config_version": CONFIG_VERSION,
            "current_config": "默认配置",
            "configs": {
                "默认配置": default_settings
            }
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def _load_attributes_from_config(self):
        """
        从加载的配置中安全地提取属性值。
        对每个可能出错的字段进行try-except处理，以防止因单个字段的
        类型或格式错误导致整个应用程序崩溃。
        """
        from logger import logger
        current_config_name = self.config.get("current_config", "默认配置")
        if current_config_name not in self.config.get("configs", {}):
            current_config_name = "默认配置" # 回退
        
        active_config = self.config.get("configs", {}).get(current_config_name, {})

        def get_int(key, default):
            try:
                return int(active_config.get(key, default))
            except (ValueError, TypeError):
                logger.log_warning(f"配置项 '{key}' 的值 '{active_config.get(key)}' 无效，已重置为默认值 '{default}'。")
                return default

        def get_str(key, default):
            return str(active_config.get(key, default))

        def get_bool(key, default):
            return bool(active_config.get(key, default))

        def get_date(key, default_date_str):
            date_str = active_config.get(key, default_date_str)
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                logger.log_warning(f"日期配置项 '{key}' 的值 '{date_str}' 格式无效，已重置为默认。")
                return datetime.strptime(default_date_str, "%Y-%m-%d")

        self.geometry = get_str("geometry", DEFAULT_GEOMETRY)
        self.countdown_name = get_str("countdown_name", "高考")
        self.countdown_date = get_date("countdown_date", f"{datetime.now().year + 1}-06-07")
        self.heweather_api_key = get_str("heweather_api_key", "")
        self.course_duration = get_int("course_duration", 40)
        self.auto_start = get_bool("auto_start", self.check_registry_auto_start())
        self.auto_complete_end_time = get_bool("auto_complete_end_time", True)
        self.auto_calculate_next_course = get_bool("auto_calculate_next_course", True)
        self.break_duration = get_int("break_duration", 10)
        self.default_courses = active_config.get("default_courses", ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"])
        self.font_size = get_int("font_size", 12)
        self.font_color = get_str("font_color", "#000000")
        self.horizontal_padding = get_int("horizontal_padding", 5)
        self.vertical_padding = get_int("vertical_padding", 5)
        self.time_display_size = get_int("time_display_size", 20)
        self.countdown_size = get_int("countdown_size", 18)
        self.schedule_size = get_int("schedule_size", 18)
        self.transparent_background = get_bool("transparent_background", True)
        self.fullscreen_subtitle = get_str("fullscreen_subtitle", "祝考生考试顺利")
        self.debug_mode = get_bool("debug_mode", active_config.get("debug_enabled", False))
        self.auto_update_check_enabled = get_bool("auto_update_check_enabled", False)
        self.log_retention_days = get_int("log_retention_days", 7)
        self.check_prerelease = get_bool("check_prerelease", False)
        self.auto_preview_tomorrow_enabled = get_bool("auto_preview_tomorrow_enabled", False)
        self.schedule_rotation_enabled = get_bool("schedule_rotation_enabled", False)
        self.rotation_schedule1 = get_str("rotation_schedule1", "")
        self.rotation_schedule2 = get_str("rotation_schedule2", "")
        self.rotation_start_date = get_date("rotation_start_date", datetime.now().strftime("%Y-%m-%d"))
        self.last_weather_location = get_str("last_weather_location", "")

    def save_config(self):
        """将当前实例属性保存到文件中对应的配置方案下"""
        from logger import logger
        
        current_config_name = self.config.get("current_config", "默认配置")

        # 对抗性修复：如果当前配置在configs中不存在，则回退到第一个可用的配置
        if current_config_name not in self.config.get("configs", {}):
            if self.get_config_names():
                current_config_name = self.get_config_names()[0]
                self.config["current_config"] = current_config_name
            else: # 极度异常情况，连一个配置都没有了
                self._create_default_config_file()
                current_config_name = "默认配置"
        
        # 优化：获取当前配置的引用，然后更新它，而不是完全替换
        # 这可以保留任何未被代码直接管理的未知字段
        active_config_data = self.config["configs"].get(current_config_name, {})

        # 将当前实例的属性更新到字典中
        active_config_data.update({
            "geometry": self.geometry if self.geometry else DEFAULT_GEOMETRY,
            "countdown_name": self.countdown_name,
            "countdown_date": self.countdown_date.strftime("%Y-%m-%d"),
            "heweather_api_key": self.heweather_api_key,
            "course_duration": self.course_duration,
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
            "log_retention_days": self.log_retention_days,
            "check_prerelease": self.check_prerelease,
            "auto_preview_tomorrow_enabled": self.auto_preview_tomorrow_enabled,
            "schedule_rotation_enabled": self.schedule_rotation_enabled,
            "rotation_schedule1": self.rotation_schedule1,
            "rotation_schedule2": self.rotation_schedule2,
            "rotation_start_date": self.rotation_start_date.strftime("%Y-%m-%d"),
            "last_weather_location": self.last_weather_location
        })
        
        # 更新到主配置字典中
        self.config["configs"][current_config_name] = active_config_data
        
        try:
            temp_file = CONFIG_FILE + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            if os.path.exists(CONFIG_FILE):
                os.replace(temp_file, CONFIG_FILE)
            else:
                os.rename(temp_file, CONFIG_FILE)
            
            logger.log_debug(f"配置 '{current_config_name}' 保存成功。")
        except Exception as e:
            logger.log_error(f"保存配置失败: {str(e)}", exc_info=True)
            raise

    def get_config_names(self):
        """获取所有配置方案的名称列表"""
        return list(self.config.get("configs", {}).keys())

    def switch_config(self, name: str):
        """切换到指定的配置方案"""
        if name in self.config.get("configs", {}):
            self.config["current_config"] = name
            self._load_attributes_from_config()
            self.save_config() # 切换后保存当前选择
            return True
        return False

    def add_config(self, name: str):
        """添加一个新的空配置方案，基于当前配置"""
        if name in self.config.get("configs", {}):
            return False # 名称已存在
        
        current_config_name = self.config.get("current_config", "默认配置")
        new_config_data = self.config["configs"].get(current_config_name, {}).copy()
        self.config["configs"][name] = new_config_data
        self.save_config()
        return True

    def copy_config(self, original_name: str, new_name: str):
        """复制一个现有的配置方案"""
        if new_name in self.config.get("configs", {}) or original_name not in self.config.get("configs", {}):
            return False
        
        self.config["configs"][new_name] = self.config["configs"][original_name].copy()
        self.save_config()
        return True

    def rename_config(self, old_name: str, new_name: str):
        """重命名一个配置方案"""
        if new_name in self.config.get("configs", {}) or old_name not in self.config.get("configs", {}):
            return False
        
        self.config["configs"][new_name] = self.config["configs"].pop(old_name)
        if self.config["current_config"] == old_name:
            self.config["current_config"] = new_name
        self.save_config()
        return True

    def delete_config(self, name: str):
        """删除一个配置方案"""
        configs = self.config.get("configs", {})
        if name not in configs or len(configs) <= 1:
            return False # 不允许删除最后一个
        
        del configs[name]
        if self.config["current_config"] == name:
            # 如果删除的是当前配置，切换到第一个可用的配置
            self.config["current_config"] = next(iter(configs))
            self._load_attributes_from_config()
        
        self.save_config()
        return True

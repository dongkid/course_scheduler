import json
import os
from datetime import datetime
from constants import DEFAULT_GEOMETRY, CONFIG_FILE

class ConfigHandler:
    def __init__(self, root_window):
        self.root = root_window
        self.config = {}
        self.gaokao_year = datetime.now().year + 1
        self.course_duration = 40
        self.auto_start = False
        self.auto_complete_end_time = True
        self.auto_calculate_next_course = True
        self.break_duration = 10
        self.default_courses = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
        self.font_size = 12
        self.font_color = "#000000"

    def initialize_config(self):
        """加载或初始化配置文件"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                self.root.geometry(self.config["geometry"])
                self.gaokao_year = self.config.get("gaokao_year", datetime.now().year + 1)
                self.course_duration = self.config.get("course_duration", 40)
                self.auto_start = self.config.get("auto_start", False)
                self.auto_complete_end_time = self.config.get("auto_complete_end_time", True)
                self.auto_calculate_next_course = self.config.get("auto_calculate_next_course", True)
                self.break_duration = self.config.get("break_duration", 10)
                self.default_courses = self.config.get("default_courses", ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"])
                self.font_size = self.config.get("font_size", 12)
                self.font_color = self.config.get("font_color", "#000000")
        else:
            self.config = {"geometry": DEFAULT_GEOMETRY}
            self.gaokao_year = datetime.now().year + 1
            self.course_duration = 40
            self.save_config()

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.root.geometry(self.config["geometry"])
            self.gaokao_year = self.config.get("gaokao_year", datetime.now().year + 1)
        else:
            self.config = {"geometry": DEFAULT_GEOMETRY}
            self.gaokao_year = datetime.now().year + 1
            self.save_config()
    
    def save_config(self):
        """保存当前配置到文件"""
        self.config["geometry"] = self.root.geometry()
        self.config["gaokao_year"] = self.gaokao_year
        self.config["course_duration"] = self.course_duration
        self.config["auto_start"] = self.auto_start
        self.config["auto_complete_end_time"] = self.auto_complete_end_time
        self.config["auto_calculate_next_course"] = self.auto_calculate_next_course
        self.config["break_duration"] = self.break_duration
        self.config["default_courses"] = self.default_courses
        self.config["font_size"] = self.font_size
        self.config["font_color"] = self.font_color
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

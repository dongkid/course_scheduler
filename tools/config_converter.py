from typing import Dict, Any

def convert_v1_to_v2(v1_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    将 v1 版本的配置文件数据转换为 v2 版本。
    此函数通过将旧配置与一套完整的默认值合并来确保数据的完整性，
    从而防止在转换过程中因缺少字段而导致数据丢失。

    v1 格式 (扁平):
    {
        "geometry": "...",
        "countdown_name": "...",
        ...
    }

    v2 格式 (嵌套，支持多配置):
    {
        "config_version": "2",
        "current_config": "默认配置",
        "configs": {
            "默认配置": {
                "geometry": "...",
                "countdown_name": "...",
                ... // 所有字段都存在
            }
        }
    }

    Args:
        v1_config: 旧版本的配置字典。

    Returns:
        转换后的新版本配置字典。
    """
    from constants import DEFAULT_GEOMETRY
    from datetime import datetime

    # 定义一个完整的 v2 配置默认值集合
    default_settings = {
        "geometry": DEFAULT_GEOMETRY,
        "countdown_name": "高考",
        "countdown_date": datetime(datetime.now().year + 1, 6, 7).strftime("%Y-%m-%d"),
        "heweather_api_key": "",
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

    # 移除旧的 "config_version" 和其他可能冲突的键
    v1_config.pop("config_version", None)
    
    # 兼容旧的 debug_enabled 字段
    if "debug_enabled" in v1_config:
        v1_config["debug_mode"] = v1_config.pop("debug_enabled")

    # 将旧配置的值覆盖到默认设置上，这会保留所有旧的用户设置，
    # 并为旧配置中没有的新增字段补充默认值。
    merged_config = default_settings.copy()
    merged_config.update(v1_config)

    # 创建新的 v2 结构
    v2_config = {
        "config_version": "2",
        "current_config": "默认配置",
        "configs": {
            "默认配置": merged_config
        }
    }
    return v2_config
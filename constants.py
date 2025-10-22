# 常量定义
DEFAULT_GEOMETRY = "180x800+1497+117"
CONFIG_FILE = "config.json"
SCHEDULE_FILE = "schedule.json"
ASPECT_RATIO = 0.5
WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]

# GitHub相关配置
GITHUB_DOMAIN = "github.com/"
VERSION_PATTERN = r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$"

# 程序信息
APP_NAME = "桌面课程表 - Course Scheduler"
AUTHOR = "dong"
VERSION = "1.0.0-preview3"
# VERSION = "0.1.1"
CONFIG_VERSION = "2"
PROJECT_URL = "https://github.com/dongkid/course_scheduler"

# 分辨率预设
# 格式: (屏幕宽度, 屏幕高度): {缩放比例: "窗口宽度x窗口高度+x偏移+y偏移"}
RESOLUTION_PRESETS = {
    # 1080p (Full HD)
    (1920, 1080): {
        100: "210x1030+1710+0",  # 100% 缩放
        125: "260x1030+1660+0",  # 125% 缩放
        150: "315x1030+1605+0",  # 150% 缩放
    },
    # 2K / 1440p
    (2560, 1440): {
        100: "215x1400+2345+0",   # 100% 缩放
        125: "215x1100+1833+0",   # 125% 缩放
        150: "215x900+1492+0",   # 150% 缩放
    },
    # 4K / 2160p
    (3840, 2160): {
        100: "400x2100+3440+0",   # 100% 缩放
        125: "350x1600+2500+0",   # 125% 缩放
        150: "300x1400+2260+0",   # 150% 缩放
        175: "240x1200+1954+0",   # 175% 缩放
    },
    # 默认预设，用于未匹配的分辨率
    "default": "180x800+1497+117"
}

# 字符串预设到分辨率元组的映射
STRING_TO_RESOLUTION_KEY = {
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}


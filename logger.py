import logging
from datetime import datetime
from pathlib import Path
from constants import CONFIG_FILE

class AppLogger:
    def __init__(self):
        self.log_dir = Path("logs")
        self._env_logged = False  # 添加环境信息记录标记
        try:
            # 尝试创建日志目录
            self.log_dir.mkdir(exist_ok=True)
        except PermissionError:
            # 如果权限不足，尝试在当前用户目录下创建日志目录
            self.log_dir = Path.home() / "CourseScheduler_logs"
            self.log_dir.mkdir(exist_ok=True)
        except Exception as e:
            # 如果其他错误，使用临时目录
            import tempfile
            self.log_dir = Path(tempfile.gettempdir()) / "CourseScheduler_logs"
            self.log_dir.mkdir(exist_ok=True)
        
        # 清理空日志文件
        self._clean_empty_logs()
        
        self._setup_logger()

    def _clean_empty_logs(self):
        """清理日志目录中的空日志文件"""
        try:
            for log_file in self.log_dir.glob("*.log"):
                if log_file.stat().st_size == 0:
                    log_file.unlink()
                    self.logger.debug(f"Deleted empty log file: {log_file}") if hasattr(self, 'logger') else None
        except Exception as e:
            self.logger.error(f"Failed to clean empty logs: {str(e)}") if hasattr(self, 'logger') else None

    def _setup_logger(self):
        from config_handler import ConfigHandler
        config = ConfigHandler()
        config.initialize_config()
        
        # 确保日志目录存在
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志记录器
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # 创建文件处理器
        log_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG if config.debug_mode else logging.ERROR)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if config.debug_mode else logging.ERROR)
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 记录日志系统初始化信息
        self.logger.debug("Logger initialized")
        self.logger.debug(f"Debug mode: {config.debug_mode}")
        self.logger.debug(f"Log directory: {self.log_dir}")
        
        # 记录配置信息
        if config.debug_mode:
            self.logger.debug("Configuration details:")
            self.logger.debug(f"Config file: {CONFIG_FILE}")
            self.logger.debug(f"Countdown: {config.countdown_name} on {config.countdown_date.strftime('%Y-%m-%d')}")
            self.logger.debug(f"Course settings: duration={config.course_duration}min, break={config.break_duration}min")
            self.logger.debug(f"Auto settings: start={config.auto_start}, complete={config.auto_complete_end_time}, next={config.auto_calculate_next_course}")
            self.logger.debug(f"Display settings: font_size={config.font_size}, time_size={config.time_display_size}")
            self.logger.debug(f"Font color: {config.font_color}")
            self.logger.debug(f"Padding: horizontal={config.horizontal_padding}, vertical={config.vertical_padding}")
            self.logger.debug(f"Countdown size: {config.countdown_size}")
            self.logger.debug(f"Schedule size: {config.schedule_size}")
            self.logger.debug(f"Transparent background: {config.transparent_background}")
            self.logger.debug(f"Fullscreen subtitle: {config.fullscreen_subtitle}")

    def log_error(self, error):
        self.logger.error(f"Error occurred: {str(error)}", exc_info=True)

    def log_warning(self, warning):
        self.logger.warning(f"Warning: {str(warning)}")

    def log_info(self, info):
        self.logger.info(f"Info: {str(info)}")

    def log_debug(self, debug):
        import platform
        import os
        import sys
        
        debug_info = str(debug)
        
        if not self._env_logged:
            debug_info += f"\nSystem: {platform.system()} {platform.release()}\n"
            debug_info += f"Python: {sys.version}\n"
            debug_info += f"Working Directory: {os.getcwd()}\n"
            debug_info += f"Environment Variables: {dict(os.environ)}"
            self._env_logged = True
        
        self.logger.debug(debug_info)

logger = AppLogger()

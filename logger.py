import logging
import threading
from logging.handlers import QueueHandler
from queue import Queue
from datetime import datetime
from pathlib import Path
from constants import CONFIG_FILE
from concurrent.futures import ThreadPoolExecutor

class AppLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
        with self._lock:
            if hasattr(self, '_initialized') and self._initialized:
                return
            
            self.logger = None
            self._env_logged = False
            self.log_queue = Queue(-1)
            self.queue_listener = None
            self.executor = None
            self._initialized = True

    def setup(self, config=None):
        """
        显式初始化日志记录器。
        这次初始化是幂等的，可以安全地多次调用。
        """
        if self.logger is not None:
            return  # 已经初始化

        # 从配置或默认值中获取设置
        debug_mode = getattr(config, 'debug_mode', False)
        log_retention_days = getattr(config, 'log_retention_days', 7)

        # 初始化线程池
        self.executor = ThreadPoolExecutor(max_workers=2)

        # 设置日志目录
        self.log_dir = Path("logs")
        try:
            self.log_dir.mkdir(exist_ok=True)
        except PermissionError:
            self.log_dir = Path.home() / "CourseScheduler_logs"
            self.log_dir.mkdir(exist_ok=True)
        except Exception:
            import tempfile
            self.log_dir = Path(tempfile.gettempdir()) / "CourseScheduler_logs"
            self.log_dir.mkdir(exist_ok=True)

        self._clean_logs(log_retention_days)

        # 创建和配置日志记录器
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        log_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 设置队列监听器
        self.queue_listener = logging.handlers.QueueListener(
            self.log_queue, file_handler, console_handler, respect_handler_level=True
        )
        self.queue_listener.start()

        self.logger.addHandler(QueueHandler(self.log_queue))
        
        self.log_debug("Logger initialized")
        self.log_debug(f"Log level set to {'DEBUG' if debug_mode else 'INFO'}.")
        self.log_debug(f"Log directory: {self.log_dir}")

        # 如果在调试模式下，记录详细的配置信息
        if debug_mode and config:
            self.log_debug("Configuration details:")
            self.log_debug(f"  Config file: {CONFIG_FILE}")
            self.log_debug(f"  Countdown: {config.countdown_name} on {config.countdown_date.strftime('%Y-%m-%d')}")
            self.log_debug(f"  Course settings: duration={config.course_duration}min, break={config.break_duration}min")
            self.log_debug(f"  Auto settings: start={config.auto_start}, complete={config.auto_complete_end_time}, next={config.auto_calculate_next_course}")
            self.log_debug(f"  Display settings: font_size={config.font_size}, time_size={config.time_display_size}")
            self.log_debug(f"  Font color: {config.font_color}")
            self.log_debug(f"  Padding: horizontal={config.horizontal_padding}, vertical={config.vertical_padding}")
            self.log_debug(f"  Countdown size: {config.countdown_size}")
            self.log_debug(f"  Schedule size: {config.schedule_size}")
            self.log_debug(f"  Transparent background: {config.transparent_background}")
            self.log_debug(f"  Fullscreen subtitle: {config.fullscreen_subtitle}")
            self.log_debug(f"  Auto update check: {config.auto_update_check_enabled}")
            self.log_debug(f"  Log retention days: {config.log_retention_days}")

    def _clean_logs(self, retention_days):
        """异步清理过期和空的日志文件"""
        def cleanup_task():
            try:
                now = datetime.now()
                cleaned_files = []
                for log_file in self.log_dir.glob("*.log"):
                    is_empty = log_file.stat().st_size == 0
                    if is_empty:
                        log_file.unlink()
                        cleaned_files.append(f"Deleted empty log file: {log_file.name}")
                        continue

                    file_mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if (now - file_mod_time).days > retention_days:
                        log_file.unlink()
                        cleaned_files.append(f"Deleted expired log file: {log_file.name}")
                
                if cleaned_files:
                    self.log_debug("Log cleanup task completed.")
                    for msg in cleaned_files:
                        self.log_debug(f"  - {msg}")

            except Exception as e:
                self.log_error(f"Failed to clean logs: {str(e)}")
        
        # 提交异步清理任务
        if self.executor:
            self.executor.submit(cleanup_task)

    def log_error(self, error):
        if self.logger:
            self.logger.error(f"Error occurred: {str(error)}", exc_info=True)

    def log_warning(self, warning):
        if self.logger:
            self.logger.warning(f"Warning: {str(warning)}")

    def log_info(self, info):
        if self.logger:
            self.logger.info(f"Info: {str(info)}")

    def shutdown(self):
        if self.queue_listener:
            self.queue_listener.stop()
        if self.executor:
            self.executor.shutdown(wait=True)

    def log_debug(self, debug):
        if self.logger:
            if not self._env_logged:
                self._log_environment()
            self.logger.debug(str(debug))

    def _log_environment(self):
        import platform, os, sys
        env_info = [
            f"System: {platform.system()} {platform.release()}",
            f"Python: {sys.version}",
            f"Working Directory: {os.getcwd()}",
        ]
        for line in env_info:
            self.logger.debug(line)
        self._env_logged = True

# 全局单例
logger = AppLogger()

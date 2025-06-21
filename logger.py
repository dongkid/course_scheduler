import logging
import threading
from logging.handlers import QueueHandler
from queue import Queue
from datetime import datetime
from pathlib import Path
from constants import CONFIG_FILE
from concurrent.futures import ThreadPoolExecutor

class AppLogger:
    def __init__(self):
        # 初始化线程池用于异步任务
        self.log_dir = Path("logs")
        self._env_logged = False
        # 创建异步日志队列和监听器
        self.log_queue = Queue(-1)  # 无限容量队列
        self.queue_listener = None
        self.executor = ThreadPoolExecutor(max_workers=2)
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
        
        # 清理日志文件
        self._clean_logs()
        
        self._setup_logger()

    def _clean_logs(self):
        """异步清理过期和空的日志文件"""
        from config_handler import ConfigHandler
        config = ConfigHandler()
        
        def cleanup_task():
            try:
                retention_days = config.log_retention_days
                now = datetime.now()
                
                for log_file in self.log_dir.glob("*.log"):
                    if log_file.stat().st_size == 0:
                        log_file.unlink()
                        self.logger.debug(f"Deleted empty log file: {log_file}")
                        continue

                    file_mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if (now - file_mod_time).days > retention_days:
                        log_file.unlink()
                        self.logger.debug(f"Deleted expired log file: {log_file}")
            except Exception as e:
                self.logger.error(f"Failed to clean logs: {str(e)}")
        
        # 提交异步清理任务
        self.executor.submit(cleanup_task)

    def _setup_logger(self):
        from config_handler import ConfigHandler
        config = ConfigHandler()
        config.initialize_config()
        
        # 确保日志目录存在
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志记录器
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # 创建实际处理器
        log_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG if config.debug_mode else logging.ERROR)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if config.debug_mode else logging.ERROR)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 设置队列监听器
        self.queue_listener = logging.handlers.QueueListener(
            self.log_queue, file_handler, console_handler, respect_handler_level=True
        )
        self.queue_listener.start()

        # 添加队列处理器
        self.logger.addHandler(QueueHandler(self.log_queue))
        
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

    def shutdown(self):
        """安全关闭日志系统"""
        if self.queue_listener:
            # 异步停止监听器并关闭线程池
            def stop_listener():
                self.queue_listener.stop()
                if hasattr(self, 'executor') and self.executor:
                    self.executor.shutdown(wait=False)
            threading.Thread(target=stop_listener, daemon=True).start()

    def log_debug(self, debug):
        # 分离环境信息记录
        if not self._env_logged:
            self._log_environment()
        
        # 直接记录调试信息
        self.logger.debug(str(debug))

    def _log_environment(self):
        """记录环境信息（只执行一次）"""
        import platform
        import os
        import sys
        
        env_info = [
            f"System: {platform.system()} {platform.release()}",
            f"Python: {sys.version}",
            f"Working Directory: {os.getcwd()}",
            f"Environment Variables: {dict(os.environ)}"
        ]
        
        for line in env_info:
            self.logger.debug(line)
        
        self._env_logged = True

logger = AppLogger()

import logging
from datetime import datetime
from pathlib import Path

class AppLogger:
    def __init__(self):
        self.log_dir = Path("logs")
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
        
        self._setup_logger()

    def _setup_logger(self):
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / "app.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_error(self, error):
        self.logger.error(f"Error occurred: {str(error)}", exc_info=True)

    def log_warning(self, warning):
        self.logger.warning(f"Warning: {str(warning)}")

    def log_info(self, info):
        self.logger.info(f"Info: {str(info)}")

logger = AppLogger()

import tkinter as tk

class DpiManager:
    """
    一个单例类，用于管理DPI缩放，将设计单位（DU）转换为实际像素。
    """
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DpiManager, cls).__new__(cls)
        return cls._instance

    def initialize(self, root: tk.Tk):
        """
        使用主Tkinter窗口初始化DPI管理器。
        此方法应在主窗口创建后立即调用。
        """
        if self._initialized:
            return
            
        self.root = root
        self._scaling_factor = 1.0
        self._calculate_scaling_factor()
        self._initialized = True

    def _calculate_scaling_factor(self):
        """
        计算系统的DPI缩放因子。
        1英寸在逻辑上等于96个像素（在100%缩放下）。
        通过获取1英寸对应的实际像素数，我们可以推导出缩放比例。
        """
        try:
            # winfo_pixels可以转换各种单位到像素
            pixels_per_inch = self.root.winfo_pixels('1i')
            # 基准DPI是96
            self._scaling_factor = pixels_per_inch / 96.0
        except tk.TclError:
            # 在某些环境下（如测试期间或非Windows系统），这可能会失败
            # 在这种情况下，我们回退到1.0
            self._scaling_factor = 1.0
        
        # 为极端情况设置一个合理的上下限
        if not (0.5 <= self._scaling_factor <= 5.0):
            self._scaling_factor = 1.0

    def scale(self, value: int) -> int:
        """
        将设计单位（DU）值按比例缩放为实际像素值。
        
        Args:
            value: 以设计单位表示的尺寸值。
            
        Returns:
            根据当前DPI缩放后的像素值（整数）。
        """
        if not self._initialized:
            # 如果在初始化之前调用，返回原始值以避免崩溃
            return value
        return int(value * self._scaling_factor)

    @property
    def scaling_factor(self) -> float:
        """获取当前的缩放因子。"""
        return self._scaling_factor

# 创建一个全局实例供方便访问
dpi_manager = DpiManager()

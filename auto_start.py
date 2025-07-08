import os
import sys
from tkinter import messagebox
import winreg
import json
from datetime import datetime
import multiprocessing
import time
try:
    import screeninfo
except ImportError:
    screeninfo = None
from constants import DEFAULT_GEOMETRY, CONFIG_FILE, RESOLUTION_PRESETS
from logger import logger

# 在子进程中运行分辨率读取函数
def get_screen_resolution_worker(queue):
    """获取主显示器分辨率并放入队列"""
    try:
        if screeninfo:
            monitors = screeninfo.get_monitors()
            if not monitors:
                raise Exception("No monitors found")
            primary_monitor = next((m for m in monitors if m.is_primary), monitors[0])
            queue.put((primary_monitor.width, primary_monitor.height))
        else:
            queue.put(None)
    except Exception as e:
        # 将异常信息放入队列，以便主进程记录
        queue.put(f"Worker Error: {e}")

# 主进程调用函数
def get_windows_scaling_factor():
    """获取 Windows 显示缩放比例，非 Windows 系统或获取失败时返回 100%"""
    try:
        # 仅在 Windows 上执行
        if sys.platform == "win32":
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics")
            # 96 DPI 是 100% 缩放
            applied_dpi = winreg.QueryValueEx(key, "AppliedDPI")[0]
            winreg.CloseKey(key)
            return int(applied_dpi / 96 * 100)
        else:
            return 100  # 非 Windows 系统默认为 100%
    except Exception as e:
        logger.log_warning(f"Failed to get Windows scaling factor: {e}. Defaulting to 100%.")
        return 100

def get_optimal_geometry():
    """
    尝试获取最佳窗口几何位置，考虑屏幕分辨率和Windows缩放。
    如果在2秒内无法获取，则返回后备默认值。
    返回一个元组 (geometry, match_type)，其中 match_type 指示匹配的类型。
    """
    default_geometry = RESOLUTION_PRESETS.get("default", DEFAULT_GEOMETRY)

    if not screeninfo:
        logger.log_warning("screeninfo module not found, using default geometry.")
        return default_geometry, "default"

    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=get_screen_resolution_worker, args=(queue,))
    process.daemon = True
    
    try:
        process.start()
        resolution = queue.get(timeout=2)
        process.join()

        if not isinstance(resolution, tuple):
            logger.log_warning(f"Failed to get resolution from worker: {resolution}. Using default.")
            return default_geometry, "default"

        logger.log_info(f"Detected screen resolution: {resolution}")
        scaling_factor = get_windows_scaling_factor()
        logger.log_info(f"Detected Windows scaling factor: {scaling_factor}%")

        # 过滤出元组键（即分辨率预设）
        numeric_presets = {k: v for k, v in RESOLUTION_PRESETS.items() if isinstance(k, tuple)}
        if not numeric_presets:
            logger.log_warning("No numeric resolution presets found. Using default geometry.")
            return default_geometry, "default"

        # 1. 尝试完全匹配分辨率和缩放比例
        if resolution in numeric_presets and scaling_factor in numeric_presets[resolution]:
            logger.log_info(f"Found exact match for {resolution} at {scaling_factor}% scaling.")
            return numeric_presets[resolution][scaling_factor], "exact"

        # 2. 尝试匹配分辨率，但缩放比例不匹配时，回退到100%
        if resolution in numeric_presets and 100 in numeric_presets[resolution]:
            logger.log_warning(f"Scaling {scaling_factor}% not found for {resolution}. Falling back to 100% scaling for the same resolution.")
            return numeric_presets[resolution][100], "fallback"

        # 3. 如果分辨率不匹配，则使用向下匹配逻辑
        screen_width, _ = resolution
        suitable_presets = {k: v for k, v in numeric_presets.items() if k[0] <= screen_width}
        
        if suitable_presets:
            best_match_key = max(suitable_presets.keys(), key=lambda p: p[0])
            logger.log_info(f"Resolution {resolution} not in presets. Downward matched to best preset: {best_match_key}.")
            
            # 在向下匹配的分辨率中，优先使用原始缩放比例
            if scaling_factor in suitable_presets[best_match_key]:
                logger.log_info(f"Found matching scaling {scaling_factor}% for downward matched preset {best_match_key}.")
                return suitable_presets[best_match_key][scaling_factor], "fallback"
            
            # 如果原始缩放比例不存在，则回退到100%
            if 100 in suitable_presets[best_match_key]:
                logger.log_warning(f"Scaling {scaling_factor}% not found for preset {best_match_key}. Falling back to 100%.")
                return suitable_presets[best_match_key][100], "fallback"

        # 4. 如果所有匹配都失败，返回全局默认值
        logger.log_warning("No suitable preset found after all checks. Using default geometry.")
        return default_geometry, "default"
            
    except (multiprocessing.TimeoutError, queue.Empty, Exception) as e:
        logger.log_error(f"Failed to get screen resolution: {e}")
        if process.is_alive():
            process.terminate()
        return default_geometry, "default"


def check_and_generate_files():
    """检查并生成配置文件和课表文件"""
    # 检查并生成配置文件
    if not os.path.exists(CONFIG_FILE):
        # 尝试获取最佳窗口位置，否则使用后备默认值
        optimal_geometry, match_type = get_optimal_geometry()
        logger.log_info(f"Setting initial geometry to: {optimal_geometry} (match type: {match_type})")

        if match_type == "exact":
            messagebox.showinfo(
                "布局提示",
                "首次启动，已为您自动匹配预设的窗口布局。\n"
                "如果布局不符合您的习惯，请在“设置”中进行调整。"
            )
        else:  # 'fallback' or 'default'
            messagebox.showwarning(
                "布局警告",
                "首次启动，未能找到完全匹配您屏幕的预设布局。\n"
                "当前使用的是一个近似或默认的方案，可能不准确。\n"
                "请务必在“设置”中根据您的偏好进行调整！"
            )

        default_config = {
            "geometry": optimal_geometry,
            "gaokao_year": datetime.now().year + 1,
            "course_duration": 40,
            "auto_start": False,
            "font_size": 20,
            "font_color": "#000000"
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    # 检查并生成课表文件
    if not os.path.exists('schedule.json'):
        default_schedule = {
            "0": [],
            "1": [],
            "2": [],
            "3": [],
            "4": [],
            "5": [],
            "6": []
        }
        with open('schedule.json', 'w', encoding='utf-8') as f:
            json.dump(default_schedule, f, ensure_ascii=False, indent=2)

def enable_auto_start(app_name, app_path=None):
    check_and_generate_files()
    """启用开机自启动"""
    try:
        # 获取真实可执行文件路径（处理PyInstaller打包情况）
        if getattr(sys, 'frozen', False):
            # 使用sys.argv[0]获取原始exe路径
            exe_path = os.path.abspath(sys.argv[0])
            # 验证路径是否存在（排除临时解压目录）
            if not os.path.exists(exe_path):
                raise FileNotFoundError(f"Invalid executable path: {exe_path}")
        else:
            exe_path = app_path or sys.executable
            
        # 用双引号包裹路径并添加start命令（防止UAC拦截）
        # 添加工作目录切换命令（使用项目根目录绝对路径）
        # formatted_path = f'cmd /c cd /d "d:/projects/course_scheduler" && start "" "{exe_path}"'
        # 不使用项目根目录绝对路径，要编译为exe发布使用的，要求该方法能动态检测相关路径
        exe_dir = os.path.dirname(exe_path)
        formatted_path = f'cmd /c cd /d "{exe_dir}" && start "" "{exe_path}"'
        
        # 打开注册表项
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
            
        # 设置注册表值
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, formatted_path)
        winreg.CloseKey(key)
        
        # 验证注册表项
        if not is_auto_start_enabled(app_name):
            raise WindowsError("Registry entry not created")
            
        return True
    except WindowsError as e:
        print(f"自启动设置失败: {str(e)}")
        messagebox.showerror("错误", f"自启动设置失败: {str(e)}")
        logger.log_error(f"自启动设置失败: {str(e)}")
        return False

def disable_auto_start(app_name):
    """禁用开机自启动"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, app_name)
        winreg.CloseKey(key)
        return True
    except WindowsError:
        return False

def is_auto_start_enabled(app_name):
    """检查是否已启用开机自启动"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run")
        winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except WindowsError:
        return False

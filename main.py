from app import CourseScheduler
from auto_start import check_and_generate_files
from logger import logger
from restart_manager import RestartManager
from constants import RESOLUTION_PRESETS, STRING_TO_RESOLUTION_KEY
from config_handler import ConfigHandler
import socket
import tkinter as tk
import sys
import multiprocessing
import ctypes

if __name__ == "__main__":
    
    # 支持打包后的多进程
    multiprocessing.freeze_support()
    
    # 安装检查（必须在最前面）
    from installer import check_installation
    check_installation()
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='课程表程序')
    parser.add_argument('--open-settings', action='store_true',
                       help='启动时打开设置窗口')
    parser.add_argument('--open-menu', action='store_true',
                       help='启动时打开主菜单')
    parser.add_argument('--geometry', type=str, default=None,
                       help='设置窗口的几何属性 (例如 "1080p" 或 "宽x高+X+Y")')
    parser.add_argument('--force-dpi', action='store_true',
                       help='强制使用DPI感知模式启动')
    parser.add_argument('help', nargs='?', default=False,
                       help='显示帮助信息')
    args = parser.parse_args()

    # 处理 help 参数
    if args.help:
        parser.print_help()
        sys.exit(0)

    # 单实例检查
    try:
        s = socket.socket()
        s.bind(('127.0.0.1', 49152))
    except OSError:
        tk.messagebox.showwarning("警告", "程序已经在运行中")
        sys.exit(1)
        
    #初始化文件
    check_and_generate_files()
    
    startup_action = None
    if args.open_settings:
        startup_action = 'open_settings'
    elif args.open_menu:
        startup_action = 'open_menu'

    geometry_override = None
    if args.geometry:
        parts = args.geometry.lower().split('-')
        if len(parts) == 2:
            res_str, dpi_str = parts
            preset_key = STRING_TO_RESOLUTION_KEY.get(res_str)
            if preset_key:
                try:
                    dpi = int(dpi_str)
                    presets = RESOLUTION_PRESETS.get(preset_key)
                    if isinstance(presets, dict):
                        geometry_override = presets.get(dpi)
                        if not geometry_override:
                             logger.warning(f"在预设 '{res_str}' 中未找到DPI为 {dpi}% 的配置")
                             # 回退到直接使用输入作为几何字符串
                             geometry_override = args.geometry
                    else:
                        geometry_override = presets # 处理 "default" 等情况
                except ValueError:
                    logger.warning(f"无效的DPI值: '{dpi_str}'")
                    geometry_override = args.geometry # DPI不是数字，直接使用
            else:
                # 分辨率字符串无效，直接使用
                geometry_override = args.geometry
        else:
            # 格式不匹配，尝试旧的逻辑或直接使用
            preset_key = STRING_TO_RESOLUTION_KEY.get(args.geometry.lower())
            if preset_key:
                presets = RESOLUTION_PRESETS.get(preset_key)
                if isinstance(presets, dict):
                    # 默认使用100%
                    geometry_override = presets.get(100, next(iter(presets.values())))
                else:
                    geometry_override = presets
            else:
                geometry_override = args.geometry
            
    # 提前初始化配置处理器
    config_handler = ConfigHandler()

    # 根据配置或命令行参数启用DPI感知 (在创建任何窗口之前)
    if sys.platform == "win32" and (config_handler.experimental_dpi_awareness or args.force_dpi):
        try:
            # 适用于 Windows 8.1 及以上版本
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            if args.force_dpi:
                logger.log_info("已通过命令行参数强制启用DPI感知功能。")
            else:
                logger.log_info("已启用实验性DPI感知功能。")
        except (AttributeError, OSError):
            try:
                # 适用于 Windows Vista 及以上版本
                ctypes.windll.user32.SetProcessDPIAware()
                if args.force_dpi:
                    logger.log_info("已通过命令行参数强制启用DPI感知功能 (兼容模式)。")
                else:
                    logger.log_info("已启用实验性DPI感知功能 (兼容模式)。")
            except (AttributeError, OSError):
                logger.log_warning("无法设置DPI感知，可能在高分屏上显示模糊。")

    app = CourseScheduler(
        config_handler=config_handler,
        startup_action=startup_action,
        geometry_override=geometry_override
    )
    
    # 清理可能存在的临时重启资源
    RestartManager.cleanup_restart_manager_resources()
    try:
        app.root.mainloop()
    finally:
        s.close()
        logger.shutdown()


from app import CourseScheduler
from auto_start import check_and_generate_files
from logger import logger
from restart_manager import RestartManager
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

    # 提前初始化配置处理器
    config_handler = ConfigHandler()

    # 默认启用DPI感知 (在创建任何窗口之前)
    if sys.platform == "win32":
        try:
            # 适用于 Windows 8.1 及以上版本
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            logger.log_info("已启用DPI感知功能 (Per-Monitor DPI Aware)。")
        except (AttributeError, OSError):
            try:
                # 适用于 Windows Vista 及以上版本
                ctypes.windll.user32.SetProcessDPIAware()
                logger.log_info("已启用DPI感知功能 (System DPI Aware)。")
            except (AttributeError, OSError):
                logger.log_warning("无法设置DPI感知，在高分屏上可能显示模糊。")

    app = CourseScheduler(
        config_handler=config_handler,
        startup_action=startup_action
    )
    
    # 清理可能存在的临时重启资源
    RestartManager.cleanup_restart_manager_resources()
    try:
        app.root.mainloop()
    finally:
        s.close()
        logger.shutdown()


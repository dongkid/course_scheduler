from app import CourseScheduler
from auto_start import check_and_generate_files
from logger import logger
from restart_manager import RestartManager
import socket
import tkinter as tk
import sys

if __name__ == "__main__":
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
    args = parser.parse_args()

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
    app = CourseScheduler(startup_action=startup_action)
    
    # 清理可能存在的临时重启资源
    RestartManager.cleanup_restart_manager_resources()
    try:
        app.root.mainloop()
    finally:
        s.close()
        logger.shutdown()

import os
import sys
import shutil
import tkinter as tk
from tkinter import messagebox
import logging
import subprocess
import atexit
from logger import logger

def is_compiled():
    """判断是否已打包为exe"""
    return hasattr(sys, 'frozen')

def get_executable_path():
    """获取可执行文件路径"""
    if is_compiled():
        return sys.executable
    return os.path.abspath(sys.argv[0])

def get_target_dir():
    """获取推荐安装目录"""
    appdata = os.getenv('APPDATA')
    return os.path.join(appdata, 'CourseScheduler')

def is_desktop_path(path):
    """检查是否在桌面目录"""
    desktop = os.path.expanduser('~/Desktop')
    return os.path.normpath(path).lower() == os.path.normpath(desktop).lower()

def create_shortcut(target, shortcut_path):
    """创建快捷方式（需要pywin32）"""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.save()
    except Exception as e:
        logger.log_error(f"快捷方式创建失败: {str(e)}")
        messagebox.showerror("错误", "无法创建快捷方式，请手动创建")

def check_installation():
    """主安装检查逻辑"""
    if not is_compiled():
        return  # 开发模式不处理
    
    # 检查必要文件是否存在
    config_files_exist = all(
        os.path.exists(f) 
        for f in ['config.json', 'schedule.json']
    )
    
    if config_files_exist:
        return  # 非首次运行
    
    current_path = os.path.dirname(get_executable_path())
    if not is_desktop_path(current_path):
        return  # 已经在正确目录
    
    # 弹出安装提示
    choice = messagebox.askyesno(
        "安装提示",
        "检测到程序运行在桌面目录，这可能导致数据丢失！\n"
        "是否要安装到推荐目录并创建快捷方式？",
        icon='warning'
    )
    
    if not choice:
        return
    
    # 开始安装流程
    target_dir = get_target_dir()
    exe_name = os.path.basename(get_executable_path())
    target_path = os.path.join(target_dir, exe_name)
    
    try:
        # 创建目标目录
        os.makedirs(target_dir, exist_ok=True)
        
        # 复制文件
        shutil.copy2(get_executable_path(), target_path)
        logger.log_info(f"程序已复制到: {target_path}")
        
        # 创建快捷方式
        desktop = os.path.expanduser('~/Desktop')
        shortcut_path = os.path.join(desktop, "桌面课程表.lnk")
        create_shortcut(target_path, shortcut_path)
        
        # 启动新实例并删除旧文件
        subprocess.Popen([target_path])
        
        # 注册退出时删除原文件
        def cleanup():
            try:
                # 删除原程序文件
                os.remove(get_executable_path())
                # 清理临时配置文件
                temp_dir = os.path.join(os.path.dirname(get_executable_path()), 'temp')
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                logger.log_info("原文件及临时目录已清理")
            except Exception as e:
                logger.log_error(f"清理失败: {str(e)}")
        
        atexit.register(cleanup)
        sys.exit(0)
        
    except Exception as e:
        logger.log_error(f"安装失败: {str(e)}")
        messagebox.showerror("安装错误", f"安装过程中发生错误: {str(e)}")
        sys.exit(1)

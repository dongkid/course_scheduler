import os
import sys
from tkinter import messagebox
import winreg
import json
from datetime import datetime
from constants import DEFAULT_GEOMETRY, CONFIG_FILE
from logger import logger

def check_and_generate_files():
    """检查并生成配置文件和课表文件"""
    # 检查并生成配置文件
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "geometry": DEFAULT_GEOMETRY,
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

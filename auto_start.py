import os
import sys
import winreg
import json
from datetime import datetime
from constants import DEFAULT_GEOMETRY, CONFIG_FILE

def check_and_generate_files():
    """检查并生成配置文件和课表文件"""
    # 检查并生成配置文件
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "geometry": DEFAULT_GEOMETRY,
            "gaokao_year": datetime.now().year + 1,
            "course_duration": 40,
            "auto_start": False
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

def enable_auto_start(app_name, app_path):
    check_and_generate_files()
    """启用开机自启动"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(key)
        return True
    except WindowsError:
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

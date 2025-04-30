import os
import sys
import shutil
import tkinter as tk
from tkinter import messagebox
import logging
import subprocess
#import atexit
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
    return os.path.join(os.environ['APPDATA'], 'CourseScheduler')

def is_desktop_path(path):
    """检查是否在桌面目录(支持系统默认和自定义路径)"""
    try:
        import ctypes
        from ctypes import wintypes
        
        # 获取系统默认桌面路径
        CSIDL_DESKTOP = 0x0000
        SHGFP_TYPE_CURRENT = 0
        
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(
            None, CSIDL_DESKTOP, None, SHGFP_TYPE_CURRENT, buf)
        system_desktop = buf.value
        
        # 常见自定义桌面路径
        custom_desktops = [
            os.path.expanduser('~/Desktop'),  # 默认
            system_desktop,                   # 系统
            'D:\\Desktop',                    # 常见自定义
            'E:\\Desktop',
            'F:\\Desktop'
        ]
        
        # 规范化比较路径
        norm_path = os.path.normpath(path).lower()
        return any(
            os.path.normpath(d).lower() == norm_path
            for d in custom_desktops
            if d  # 过滤空路径
        )
    except Exception:
        # 回退方案
        desktop = os.path.expanduser('~/Desktop')
        return os.path.normpath(path).lower() == os.path.normpath(desktop).lower()

def create_shortcut(target, shortcut_path):
    """使用VBScript创建快捷方式"""
    try:
        # 图标路径指向AppData目录下的res/icon.ico
        target_dir = os.path.dirname(target)
        icon_path = os.path.join(os.environ['APPDATA'], 'CourseScheduler', "res", "icon.ico")
        
        # 检查图标文件是否存在
        icon_location = ""
        if os.path.exists(icon_path):
            icon_location = f'oLink.IconLocation = "{icon_path}"\n        '
        else:
            logger.log_warning(f"图标文件不存在: {icon_path}")
        
        vbs_script = f"""
        Set oWS = WScript.CreateObject("WScript.Shell")
        Set oLink = oWS.CreateShortcut("{shortcut_path}")
        oLink.TargetPath = "{target}"
        oLink.WorkingDirectory = "{os.path.dirname(target)}"
        oLink.Description = "课程表快捷方式"
        {icon_location}oLink.Save
        """
        
        # 创建临时VBS文件
        temp_vbs = os.path.join(os.environ['TEMP'], 'create_shortcut.vbs')
        with open(temp_vbs, 'w', encoding='gbk') as f:
            f.write(vbs_script)
            
        # 执行VBS脚本
        result = subprocess.run(
            ['cscript.exe', temp_vbs],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"VBScript执行失败: {result.stderr}")
            
        # 删除临时文件
        os.remove(temp_vbs)
        
    except Exception as e:
        logger.log_error(f"快捷方式创建失败: {str(e)}")
        messagebox.showerror("错误", f"无法创建快捷方式: {str(e)}")
        
        # 创建临时VBS文件
        temp_vbs = os.path.join(os.environ['TEMP'], 'create_shortcut.vbs')
        with open(temp_vbs, 'w', encoding='utf-8') as f:
            f.write(vbs_script)
            
        # 执行VBS脚本
        subprocess.run(['cscript.exe', temp_vbs], check=True, shell=True)
        
        # 删除临时文件
        os.remove(temp_vbs)
        
    except Exception as e:
        logger.log_error(f"快捷方式创建失败: {str(e)}")
        messagebox.showerror("错误", "无法创建快捷方式，请手动创建")

def check_installation():
    """主安装检查逻辑"""
    # 程序启动时清理残留的计划任务
    def cleanup_scheduled_task():
        try:
            task_name = "CourseDelayedCleanup"
            bat_path = os.path.join(os.getcwd(), 'delayed_cleanup.bat')
            
            # 删除临时批处理文件
            if os.path.exists(bat_path):
                os.remove(bat_path)
                logger.log_debug(f"已清理临时批处理文件: {bat_path}")
            
            # 清理计划任务
            check_result = subprocess.run(
                f'schtasks /query /tn "{task_name}"',
                shell=True,
                capture_output=True,
                text=True
            )
            if check_result.returncode == 0:
                subprocess.run(
                    f'schtasks /delete /tn "{task_name}" /f',
                    shell=True,
                    check=True
                )
                logger.log_debug(f"已清理计划任务: {task_name}")
        except Exception as e:
            logger.log_error(f"启动清理失败: {str(e)}")
    
    cleanup_scheduled_task()

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
    
    # 检查管理员权限
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        is_admin = False
    
    if not is_admin:
        # 清理临时文件
        try:
            if os.path.exists('config.json'):
                os.remove('config.json')
            if os.path.exists('logs'):
                shutil.rmtree('logs')
        except Exception as e:
            logger.log_error(f"清理临时文件失败: {str(e)}")
        
        messagebox.showerror("权限错误", "需要管理员权限才能完成安装")
        sys.exit(1)

    
    # 开始安装流程
    target_dir = get_target_dir()
    exe_name = os.path.basename(get_executable_path())
    target_path = os.path.join(target_dir, exe_name)
    
    try:
        # 创建目标目录
        os.makedirs(target_dir, exist_ok=True)
        
        # 创建目标目录结构
        os.makedirs(os.path.join(target_dir, "res"), exist_ok=True)
        
        # 复制程序文件和资源文件
        shutil.copy2(get_executable_path(), target_path)
        
        # 复制图标文件
        src_icon = os.path.join(os.path.dirname(get_executable_path()), "res", "icon.ico")
        if hasattr(sys, '_MEIPASS'):
            src_icon = os.path.join(sys._MEIPASS, "res", "icon.ico")
        
        if os.path.exists(src_icon):
            shutil.copy2(src_icon, os.path.join(target_dir, "res", "icon.ico"))
        
        logger.log_info(f"程序已复制到: {target_path}")
        
        # 创建快捷方式
        desktop = os.path.expanduser('~/Desktop')
        shortcut_path = os.path.join(desktop, "桌面课表.lnk")
        create_shortcut(target_path, shortcut_path)
        
        # 创建批处理文件（启动新程序+清理桌面文件）
        bat_path = os.path.join(os.getcwd(), 'install_cleanup.bat')
        desktop_path = os.path.expanduser('~/Desktop')
        exe_path = get_executable_path()
        
        script_content = f"""@echo off
chcp 65001 >nul
:: 以管理员权限启动新程序

:: 清理桌面文件（重试机制）
:cleanup_loop
del /f /q "{desktop_path}\\config.json" >nul 2>&1
del /f /q "{desktop_path}\\schedule.json" >nul 2>&1
if exist "{desktop_path}\\logs" (
    rmdir /s /q "{desktop_path}\\logs" >nul 2>&1
)

:: 检查是否清理完成
if exist "{desktop_path}\\config.json" (
    timeout /t 1 /nobreak >nul
    goto cleanup_loop
)
if exist "{desktop_path}\\schedule.json" (
    timeout /t 1 /nobreak >nul
    goto cleanup_loop
)
if exist "{desktop_path}\\logs" (
    timeout /t 1 /nobreak >nul
    goto cleanup_loop
)

:: 直接启动程序并设置工作目录
start "" /D "%APPDATA%\CourseScheduler" "{target_path}"

:: 删除批处理脚本自身
del /f /q "%~f0" >nul 2>&1
exit
"""
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 创建并执行计划任务
        task_name = "CourseInstallerTask"
        try:
            # 检查批处理文件是否存在
            if not os.path.exists(bat_path):
                raise FileNotFoundError(f"批处理文件不存在: {bat_path}")

            # 创建计划任务（带详细日志）
            create_cmd = f'schtasks /create /tn "{task_name}" /tr "{bat_path}" /sc once /st 00:00 /f'
            logger.log_debug(f"执行命令: {create_cmd}")
            
            create_result = subprocess.run(
                create_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if create_result.returncode != 0:
                error_msg = f"计划任务创建失败(代码{create_result.returncode}): {create_result.stderr}"
                logger.log_error(error_msg)
                raise RuntimeError(error_msg)

            # 立即运行计划任务
            run_cmd = f'schtasks /run /tn "{task_name}"'
            logger.log_debug(f"执行命令: {run_cmd}")
            
            run_result = subprocess.run(
                run_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if run_result.returncode != 0:
                error_msg = f"计划任务启动失败(代码{run_result.returncode}): {run_result.stderr}"
                logger.log_error(error_msg)
                raise RuntimeError(error_msg)

            logger.log_info("计划任务创建并执行成功")
            sys.exit(0)
            
        except Exception as e:
            logger.log_error(f"安装过程中发生错误: {str(e)}")
            logger.log_debug(f"批处理文件路径: {bat_path}")
            logger.log_debug(f"目标程序路径: {target_path}")
            messagebox.showerror("安装错误",
                f"安装过程中发生错误:\n{str(e)}\n"
                f"请手动启动新程序: {target_path}")
            sys.exit(1)
        
    except Exception as e:
        logger.log_error(f"安装失败: {str(e)}")
        messagebox.showerror("安装错误", f"安装过程中发生错误: {str(e)}")
        sys.exit(1)

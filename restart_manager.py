import os
import sys
import subprocess
import tempfile
import logging
from tkinter import messagebox
from logger import logger

class RestartManager:
    @staticmethod
    def cleanup_restart_manager_resources():
        """清理残留的临时重启资源"""
        try:
            # 删除临时批处理文件
            bat_path = os.path.join(os.getcwd(), 'restart.bat')
            if os.path.exists(bat_path):
                os.remove(bat_path)
                logger.log_debug(f"已清理临时批处理文件: {bat_path}")
            
            # 清理计划任务
            task_name = "CourseDetachedTask"
            # 检查任务是否存在
            check_detachedtask_result = subprocess.run(
                f'schtasks /query /tn "{task_name}"',
                shell=True,
                capture_output=True,
                text=True
            )
            if check_detachedtask_result.returncode == 0:
                # 任务存在则删除
                del_result = subprocess.run(
                    f'schtasks /delete /tn "{task_name}" /f',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if del_result.returncode == 0:
                    logger.log_debug(f"已清理计划任务: {task_name}")
                else:
                    logger.log_error(f"计划任务删除失败: {del_result.stderr.strip()}")
            else:
                logger.log_debug(f"计划任务不存在，无需清理: {task_name}")
                
        except Exception as e:
            logger.log_error(f"资源清理失败: {str(e)}")

    @staticmethod
    def restart_application(main_app, app_path=None, open_settings=False):
        """执行进程级完全重启"""
        try:
            # 记录调试信息
            logger.log_debug(f"开始生成重启脚本 - 工作目录: {os.getcwd()}")
            logger.log_debug(f"原始执行路径: {sys.executable}")
            logger.log_debug(f"打包状态: {getattr(sys, 'frozen', False)}")

            if getattr(sys, 'frozen', False):
                # 生产环境使用批处理+计划任务
                bat_path = os.path.join(os.getcwd(), 'restart.bat')
                exe_path = f'"{sys.executable}"'
                logger.log_debug(f"打包环境可执行路径: {exe_path}")

                # 获取真实可执行文件路径（处理PyInstaller打包情况）
                exe_path = os.path.abspath(sys.argv[0])
                if not os.path.exists(exe_path):
                    raise FileNotFoundError(f"Invalid executable path: {exe_path}")
                
                exe_dir = os.path.dirname(exe_path)
                script_content = f"""@echo off
chcp 65001 >nul
echo stopping process...
taskkill /fi "IMAGENAME eq {os.path.basename(sys.executable)}" /fi "PID eq {os.getpid()}" /f /t >nul 2>&1
taskkill /fi "IMAGENAME eq {os.path.basename(sys.executable)}" /fi "PID eq {os.getppid()}" /f /t >nul 2>&1
echo starting process...
                cd /d "{exe_dir}" && start "" "{exe_path}" {"--open-settings" if open_settings else ""}
exit
"""
                with open(bat_path, 'w', encoding='gbk') as f:
                    f.write(script_content)
                logger.log_debug(f"生成的批处理脚本内容:\n{script_content}")

                # 创建并执行计划任务
                task_name = "CourseDetachedTask"
                subprocess.run(
                    f'schtasks /create /tn "{task_name}" /tr "{bat_path}" /sc once /st 00:00',
                    shell=True,
                    check=True
                )
                subprocess.run(f'schtasks /run /tn "{task_name}"', shell=True, check=True)
            else:
                # 开发环境直接内部重启
                logger.log_debug("开发环境直接重启应用")
                python_exe = sys.executable
                # 获取主程序入口文件路径
                main_script = os.path.abspath("main.py")
                if not os.path.exists(main_script):
                    raise FileNotFoundError(f"主程序入口文件不存在: {main_script}")
                
                args = [python_exe, main_script]
                if open_settings:
                    args.append("--open-settings")
                
                # 启动新进程
                subprocess.Popen(
                    args,
                    cwd=os.getcwd(),
                    close_fds=True,
                    shell=True
                )
            
            # subprocess.Popen(
            #      f'start "" /B cmd /c "{bat_path}"', 
            #      shell=True,
            #      creationflags=subprocess.DETACHED_PROCESS
            #  )
            
            # 通过PowerShell启动独立进程
            # command = [
            #     'powershell',
            #     '-Command',
            #     f'Start-Process cmd.exe -ArgumentList "/c {bat_path}" -WindowStyle Hidden -PassThru'
            # ]
            # subprocess.Popen(command, shell=True)
            

            main_app.root.destroy()
            
        except Exception as e:
            logger.log_error(f"重启失败: {str(e)}")
            messagebox.showerror("严重错误", 
                "无法执行重启操作，请手动重启程序。\n"
                f"错误信息: {str(e)}")

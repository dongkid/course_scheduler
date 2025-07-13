import json
import os
from datetime import datetime
from tkinter import filedialog, messagebox
from logger import logger
from constants import CONFIG_FILE, SCHEDULE_FILE, CONFIG_VERSION

class BackupRestoreManager:
    """处理应用程序数据的备份和还原"""

    def __init__(self, main_app):
        """
        初始化备份还原管理器。
        Args:
            main_app: CourseScheduler 主应用实例。
        """
        self.main_app = main_app
        self.config_handler = main_app.config_handler

    def export_data(self, selected_configs, include_schedule):
        """
        导出选定的配置和课表数据。
        Args:
            selected_configs (list): 要导出的配置名称列表。
            include_schedule (bool): 是否包含课表数据。
        """
        backup_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "config_version": CONFIG_VERSION,
                "current_config_in_backup": self.config_handler.config.get("current_config")
            },
            "configs": None,
            "schedule": None
        }

        # 1. 处理配置数据
        if selected_configs:
            all_configs = self.config_handler.config.get("configs", {})
            configs_to_export = {name: all_configs[name] for name in selected_configs if name in all_configs}
            if configs_to_export:
                backup_data["configs"] = configs_to_export

        # 2. 处理课表数据
        if include_schedule:
            if os.path.exists(SCHEDULE_FILE):
                with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                    backup_data["schedule"] = json.load(f)

        # 3. 检查是否有效数据被导出
        if not backup_data["configs"] and not backup_data["schedule"]:
            messagebox.showwarning("无数据", "没有选择任何要导出的数据。")
            return

        # 4. 弹出文件保存对话框
        file_path = filedialog.asksaveasfilename(
            title="保存备份文件",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"CourseScheduler_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if not file_path:
            return # 用户取消

        # 5. 写入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("成功", f"数据已成功导出到:\n{file_path}")
        except Exception as e:
            logger.log_error(f"导出数据失败: {e}")
            messagebox.showerror("错误", f"导出失败: {e}")

    def import_data(self, mode):
        """
        导入数据。
        Args:
            mode (str): 'incremental' 或 'overwrite'。
        """
        file_path = filedialog.askopenfilename(
            title="选择备份文件进行导入",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not file_path:
            return # 用户取消

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
        except Exception as e:
            logger.log_error(f"读取备份文件失败: {e}")
            messagebox.showerror("错误", f"无法读取或解析备份文件: {e}")
            return

        # 验证备份文件
        if "metadata" not in backup_data or "configs" not in backup_data or "schedule" not in backup_data:
            messagebox.showerror("文件无效", "选择的文件不是一个有效的备份文件。")
            return

        # 版本兼容性检查
        backup_version = backup_data.get("metadata", {}).get("config_version")
        if backup_version and backup_version > CONFIG_VERSION:
            if not messagebox.askyesno("版本不兼容警告",
                                     f"备份文件版本 ({backup_version}) 高于当前应用版本 ({CONFIG_VERSION})。\n"
                                     "导入可能会导致未知问题。\n\n"
                                     "您确定要继续吗？"):
                return

        # 确认操作
        if not messagebox.askyesno("确认导入", f"确定要以 '{mode}' 模式导入数据吗？\n这将修改您当前的配置和课表，建议操作前先进行备份。"):
            return

        # 根据模式执行导入
        try:
            if mode == 'overwrite':
                self._overwrite_import(backup_data)
            elif mode == 'incremental':
                self._incremental_import(backup_data)
            
            # 刷新运行时状态
            self.config_handler._load_attributes_from_config()

            # 如果编辑器窗口是打开的，警告并关闭它以防止数据冲突
            if self.main_app.editor_window and self.main_app.editor_window.window.winfo_exists():
                messagebox.showwarning("编辑器已关闭", "为防止数据冲突，课表编辑器窗口已关闭。请重新打开以查看更新后的课表。")
                self.main_app.editor_window.window.destroy()

            # 提示重启
            messagebox.showinfo("成功", "数据导入成功！\n为了使所有更改完全生效，建议您重启应用程序。")

        except Exception as e:
            logger.log_error(f"导入数据时发生错误: {e}")
            messagebox.showerror("导入失败", f"处理导入数据时发生错误: {e}")

    def _overwrite_import(self, backup_data):
        """执行覆盖导入（使用临时文件保证原子性）"""
        config_to_write = None
        schedule_to_write = None

        # 准备要写入的数据
        if backup_data.get("configs"):
            new_config_data = self.config_handler.config.copy()
            new_config_data["configs"] = backup_data["configs"]
            backup_current = backup_data.get("metadata", {}).get("current_config_in_backup")
            if backup_current and backup_current in backup_data["configs"]:
                new_config_data["current_config"] = backup_current
            else:
                new_config_data["current_config"] = next(iter(backup_data["configs"]))
            config_to_write = new_config_data

        if backup_data.get("schedule"):
            schedule_to_write = backup_data["schedule"]

        # 原子化写入
        self._atomic_write(config_to_write, schedule_to_write)

        # 更新内存状态
        if config_to_write:
            self.config_handler.config = config_to_write
        if schedule_to_write:
            self.main_app.schedule = schedule_to_write

    def _incremental_import(self, backup_data):
        """执行增量导入"""
        """执行增量导入（使用临时文件保证原子性）"""
        config_to_write = None
        schedule_to_write = None

        # 准备要写入的配置数据
        if backup_data.get("configs"):
            new_config_data = self.config_handler.config.copy()
            for name, config_data in backup_data["configs"].items():
                new_config_data["configs"][name] = config_data
            config_to_write = new_config_data

        # 准备要写入的课表数据
        if backup_data.get("schedule"):
            if os.path.exists(SCHEDULE_FILE):
                with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                    current_schedule = json.load(f)
            else:
                current_schedule = {"schedules": {}}
            
            for name, schedule_data in backup_data["schedule"]["schedules"].items():
                current_schedule["schedules"][name] = schedule_data
            schedule_to_write = current_schedule

        # 原子化写入
        self._atomic_write(config_to_write, schedule_to_write)

        # 更新内存状态
        if config_to_write:
            self.config_handler.config = config_to_write
        if schedule_to_write:
            self.main_app.schedule = schedule_to_write

    def _atomic_write(self, config_data, schedule_data):
        """
        将数据原子化地写入配置文件。
        先写入.tmp文件，成功后再替换原文件。
        """
        config_tmp_file = CONFIG_FILE + ".tmp"
        schedule_tmp_file = SCHEDULE_FILE + ".tmp"

        try:
            # 写入临时文件
            if config_data:
                with open(config_tmp_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=4)
            if schedule_data:
                with open(schedule_tmp_file, 'w', encoding='utf-8') as f:
                    json.dump(schedule_data, f, ensure_ascii=False, indent=4)

            # 替换原文件
            if config_data:
                os.replace(config_tmp_file, CONFIG_FILE)
            if schedule_data:
                os.replace(schedule_tmp_file, SCHEDULE_FILE)

        except Exception as e:
            # 如果出错，清理临时文件
            if os.path.exists(config_tmp_file):
                os.remove(config_tmp_file)
            if os.path.exists(schedule_tmp_file):
                os.remove(schedule_tmp_file)
            raise e # 将异常向上抛出，由调用者处理
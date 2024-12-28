# 桌面课程表应用 - Course Scheduler

一个简单的桌面课程表管理工具。

## 优势
- 超快运行速度，完全使用python原生库构建
- 极低占用
- 开箱即用，单文件即可运行
- 良好的json支持

## 主要功能

### 课程管理
- 添加、编辑、删除每日课程
- 课程时间自动计算
- 课程状态实时显示（未开始、进行中、已结束）
- 支持自定义课程名称

### 高考倒计时
- 实时显示距离高考的天数
- 可自定义高考年份

### 个性化设置
- 调整窗口大小和位置
- 设置课程时长和课间时间
- 启用/禁用自动计算功能
- 开机自启动选项

### 数据管理
- 自动保存课程表和配置
- 数据存储在本地JSON文件中
- 提供默认课程模板

## 安装与使用

### 运行源码
```bash
# 克隆仓库
git clone https://github.com/your-repo/course_scheduler.git
cd course_scheduler

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

### 构建
```bash
# 安装PyInstaller
pip install pyinstaller

# 构建可执行文件
pyinstaller --onefile --name=course_scheduler --icon=icon.ico --clean --noconfirm main.py

# 构建完成后，可执行文件位于dist目录下
```

### GitHub Action构建
本项目配置了GitHub Action自动构建，每次推送代码到main分支或创建tag时，会自动构建可执行文件并发布到Release页面。

## 贡献指南

欢迎提交Pull Request或Issue。

## 鸣谢

本软件在编写过程中大量使用了ai编写的代码，极大的加快了编写速度。
感谢Desktop-Lesson-List项目为本项目提供设计灵感。

## 许可证

本项目采用 [GNU GPLv3 许可证](LICENSE)。

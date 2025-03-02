from app import CourseScheduler
from auto_start import check_and_generate_files
from logger import logger
import socket
import tkinter as tk
import sys

if __name__ == "__main__":
    check_and_generate_files()
    
    # 单实例检查
    try:
        s = socket.socket()
        s.bind(('127.0.0.1', 49152))
    except OSError:
        tk.messagebox.showwarning("警告", "程序已经在运行中")
        sys.exit(1)
    
    app = CourseScheduler()
    try:
        app.root.mainloop()
    finally:
        s.close()
        logger.shutdown()

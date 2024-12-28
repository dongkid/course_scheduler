from app import CourseScheduler
from auto_start import check_and_generate_files

if __name__ == "__main__":
    check_and_generate_files()
    app = CourseScheduler()
    app.root.mainloop()

import tkinter as tk
from tkinter import ttk
import time

class SudokuApp(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("数独游戏")
        self.geometry("550x650")
        self.configure(bg="#F5F5F5")

        # --- Modern UI Colors and Fonts ---
        self.COLORS = {
            "bg": "#F5F5F5",
            "grid_bg": "#FFFFFF",
            "grid_alt_bg": "#E8E8E8",
            "text": "#212121",
            "preset_text": "#333333",
            "user_text": "#00529B",
            "highlight": "#BBDEFB",
            "border": "#CCCCCC",
            "status_bg": "#EEEEEE",
        }
        self.FONTS = {
            "cell": ("Segoe UI", 20, "bold"),
            "status": ("Segoe UI", 10),
            "label": ("Segoe UI", 11, "bold"),
        }

        try:
            self.iconbitmap("res/icon.ico")
        except tk.TclError:
            pass

        from .sudoku import Sudoku
        self.sudoku = Sudoku()
        self.original_puzzle = None
        self.current_focus_cell = None
        self.last_reset_click_time = 0

        self._create_widgets()
        self._setup_layout()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.generate_sudoku(self.difficulty_var.get())

    def on_close(self):
        self.destroy()

    def _create_widgets(self):
        self._create_grid_and_controls()
        self._create_status_bar()

    def _create_grid_and_controls(self):
        self.main_frame = tk.Frame(self, bg=self.COLORS["bg"])

        # --- Grid Frame ---
        self.grid_container = tk.Frame(self.main_frame, bg=self.COLORS["bg"])
        self.grid_frame = tk.Frame(self.grid_container, bg=self.COLORS["border"], bd=1)
        self.cells = []

        for row in range(9):
            row_cells = []
            for col in range(9):
                frame = tk.Frame(self.grid_frame, bg=self.COLORS["grid_bg"])
                if (row // 3 + col // 3) % 2 == 1:
                    frame.config(bg=self.COLORS["grid_alt_bg"])

                vcmd = (self.register(self._validate_input), '%P')
                cell = tk.Entry(
                    frame,
                    font=self.FONTS["cell"],
                    justify='center',
                    validate='key',
                    validatecommand=vcmd,
                    bd=0,
                    relief='flat',
                    highlightthickness=0,
                    bg=frame['bg'],
                    fg=self.COLORS["user_text"],
                    insertbackground=self.COLORS["user_text"],
                    disabledbackground=frame['bg'],
                    disabledforeground=self.COLORS["preset_text"],
                )
                cell.bind("<FocusIn>", self._on_cell_focus)
                cell.bind("<FocusOut>", self._on_cell_blur)

                frame.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
                cell.pack(expand=True, fill="both", ipady=4)
                row_cells.append(cell)
            self.cells.append(row_cells)

        for i in range(9):
            self.grid_frame.grid_rowconfigure(i, weight=1, minsize=45, uniform="cell")
            self.grid_frame.grid_columnconfigure(i, weight=1, minsize=45, uniform="cell")

        # --- Controls Frame ---
        self.control_frame = tk.Frame(self.main_frame, bg=self.COLORS["bg"])
        self.difficulty_var = tk.StringVar(value="中等")
        difficulties = ["入门", "简单", "中等", "困难", "专家", "地狱"]

        self.difficulty_menu = ttk.Combobox(
            self.control_frame,
            textvariable=self.difficulty_var,
            values=difficulties,
            state="readonly",
            justify="center",
        )
        self.generate_btn = ttk.Button(
            self.control_frame, text="生成",
            command=lambda: self.generate_sudoku(self.difficulty_var.get())
        )
        self.solve_btn = ttk.Button(
            self.control_frame, text="求解",
            command=self.solve_sudoku
        )
        self.reset_btn = ttk.Button(
            self.control_frame, text="重置",
            command=self._on_reset_click
        )

        self.difficulty_menu.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        self.generate_btn.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.solve_btn.grid(row=0, column=2, padx=5, pady=10, sticky="ew")
        self.reset_btn.grid(row=0, column=3, padx=5, pady=10, sticky="ew")

        for i in range(4):
            self.control_frame.grid_columnconfigure(i, weight=1)

        # --- Number Selector ---
        self.number_selector_frame = tk.Frame(self.main_frame, bg=self.COLORS["bg"])
        for i in range(1, 10):
            btn = ttk.Button(
                self.number_selector_frame,
                text=str(i),
                command=lambda num=i: self._on_number_select(num)
            )
            btn.grid(row=0, column=i-1, padx=2, pady=5, sticky="nsew")
        for i in range(9):
            self.number_selector_frame.grid_columnconfigure(i, weight=1)

    def _on_number_select(self, num):
        if self.current_focus_cell and self.current_focus_cell['state'] == 'normal':
            self.current_focus_cell.delete(0, tk.END)
            self.current_focus_cell.insert(0, str(num))

    def _on_cell_focus(self, event):
        widget = event.widget
        self.current_focus_cell = widget
        if widget['state'] == 'normal':
            widget.master.config(bg=self.COLORS["highlight"])
            widget.config(bg=self.COLORS["highlight"])

    def _on_cell_blur(self, event):
        widget = event.widget
        original_bg = self.COLORS["grid_bg"]
        row, col = self._find_cell_coords(widget)
        if (row // 3 + col // 3) % 2 == 1:
            original_bg = self.COLORS["grid_alt_bg"]
        widget.master.config(bg=original_bg)
        widget.config(bg=original_bg)

    def _find_cell_coords(self, widget):
        for r, row_cells in enumerate(self.cells):
            try:
                c = row_cells.index(widget)
                return r, c
            except ValueError:
                continue
        return -1, -1

    def _validate_input(self, new_value):
        if new_value == "": return True
        if len(new_value) > 1: return False
        return new_value in "123456789"

    def _create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self, textvariable=self.status_var,
                                   font=self.FONTS["status"],
                                   bg=self.COLORS["status_bg"],
                                   fg=self.COLORS["text"],
                                   relief=tk.FLAT, anchor=tk.W, padx=10)
        self.status_var.set("准备就绪")

    def _setup_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.grid_container.grid(row=0, column=0, sticky="nsew")
        self.grid_frame.pack(expand=True, fill="both")

        self.number_selector_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.control_frame.grid(row=2, column=0, sticky="ew", pady=10)

        self.grid_container.grid_rowconfigure(0, weight=1)
        self.grid_container.grid_columnconfigure(0, weight=1)

        self.status_bar.grid(row=1, column=0, sticky="ew")

    def generate_sudoku(self, difficulty):
        self.status_var.set(f"正在生成 {difficulty} 难度数独...")
        self.update_idletasks()

        puzzle, elapsed, remaining, solution_count = self.sudoku.generate(difficulty)
        
        self.original_puzzle = [row[:] for row in puzzle]
        self.update_grid(puzzle)

        self.status_var.set(
            f"难度: {difficulty} | "
            f"剩余数字: {remaining} | "
            f"解的数量: {solution_count} | "
            f"耗时: {elapsed:.2f}秒"
        )

    def solve_sudoku(self):
        self.status_var.set("正在求解...")
        self.update_idletasks()

        original_board = self.get_current_board()
        self.sudoku.board = [row[:] for row in original_board]

        solved, elapsed = self.sudoku.solve()

        if solved:
            self.update_grid(self.sudoku.board)
            self.status_var.set(f"求解成功, 耗时: {elapsed:.4f} 秒")
        else:
            self.update_grid(original_board)
            self.status_var.set(f"求解失败, 耗时: {elapsed:.4f} 秒. 请检查输入.")
            import tkinter.messagebox as msgbox
            msgbox.showerror("求解失败", "无法求解该数独谜题，请检查输入是否正确或存在冲突。")

    def _on_reset_click(self):
        current_time = time.time()
        if current_time - self.last_reset_click_time < 0.4:
            self.clear_board()
            self.last_reset_click_time = 0
        else:
            self.reset_sudoku()
            self.last_reset_click_time = current_time

    def clear_board(self):
        self.original_puzzle = None
        for r in range(9):
            for c in range(9):
                self.cells[r][c].config(state='normal')
                self.cells[r][c].delete(0, "end")
        self.status_var.set("棋盘已清空")

    def reset_sudoku(self):
        if self.original_puzzle:
            self.update_grid(self.original_puzzle)
            self.status_var.set("棋盘已重置为初始状态")
        else:
            self.clear_board()

    def update_grid(self, board):
        for row in range(9):
            for col in range(9):
                value = board[row][col]
                cell = self.cells[row][col]
                cell.config(state='normal')
                cell.delete(0, "end")
                if value is not None:
                    cell.insert(0, str(value))
                    cell.config(state='disabled')

    def get_current_board(self):
        board = []
        for row in range(9):
            row_vals = []
            for col in range(9):
                text = self.cells[row][col].get()
                row_vals.append(int(text) if text else None)
            board.append(row_vals)
        return board

# 独立运行入口
if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuApp(root)
    root.mainloop()
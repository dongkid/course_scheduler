import random
import time

class DLXNode:
    """舞蹈链节点"""
    def __init__(self, row=0, col=0):
        self.left = self
        self.right = self
        self.up = self
        self.down = self
        self.column = None  # 指向列头节点
        self.row = row      # 行索引（用于回溯）
        self.col = col      # 列索引（用于回溯）
        self.size = 0       # 列节点数（仅列头节点使用）

class DLXSolver:
    """
    使用 Dancing Links X (Algorithm X) 的通用精确覆盖问题求解器。
    """
    def __init__(self, num_cols):
        """初始化求解器和精确覆盖矩阵"""
        self.header = DLXNode()
        self.columns = []
        self._build_matrix(num_cols)
        self.solution = []
        self.solutions_count = 0

    def _build_matrix(self, num_cols):
        """构建列头节点的环形链表"""
        self.columns = [DLXNode(col=i) for i in range(num_cols)]
        prev = self.header
        for col_node in self.columns:
            col_node.left = prev
            col_node.right = self.header
            prev.right = col_node
            self.header.left = col_node
            prev = col_node

    def add_row(self, row_data, row_idx):
        """向矩阵中添加一行，代表一个可能的选择"""
        first_node = None
        prev_node = None
        for col_idx in row_data:
            if not (0 <= col_idx < len(self.columns)):
                continue
            
            col_node = self.columns[col_idx]
            node = DLXNode(row_idx, col_idx)
            
            # 垂直链接
            node.column = col_node
            node.up = col_node.up
            node.down = col_node
            col_node.up.down = node
            col_node.up = node
            col_node.size += 1
            
            # 水平链接
            if prev_node:
                node.left = prev_node
                node.right = first_node
                prev_node.right = node
                first_node.left = node
            else:
                first_node = node
            prev_node = node

    def _cover(self, col_node):
        """覆盖一列及其关联的所有行"""
        col_node.right.left = col_node.left
        col_node.left.right = col_node.right
        
        row_node = col_node.down
        while row_node != col_node:
            right_node = row_node.right
            while right_node != row_node:
                right_node.up.down = right_node.down
                right_node.down.up = right_node.up
                if right_node.column:
                    right_node.column.size -= 1
                right_node = right_node.right
            row_node = row_node.down

    def _uncover(self, col_node):
        """取消覆盖一列，恢复其关联的所有行"""
        row_node = col_node.up
        while row_node != col_node:
            left_node = row_node.left
            while left_node != row_node:
                if left_node.column:
                    left_node.column.size += 1
                left_node.up.down = left_node
                left_node.down.up = left_node
                left_node = left_node.left
            row_node = row_node.up
            
        col_node.right.left = col_node
        col_node.left.right = col_node

    def solve(self):
        """寻找第一个解，并返回解中行的索引列表"""
        self._solution_nodes = []
        self._solutions_count = 0
        self._search(limit=1)
        if self._solutions_count > 0:
            return [node.row for node in self._solution_nodes]
        return None

    def count_solutions(self, limit=2):
        """计算解的数量，直到达到上限"""
        self._solution_nodes = []
        self._solutions_count = 0
        self._search(limit=limit)
        return self._solutions_count

    def _search(self, limit):
        """Algorithm X 递归搜索实现"""
        if self.header.right == self.header:
            self._solutions_count += 1
            return

        # 选择最小列（启发式优化）
        min_col = self.header.right
        current = min_col.right
        while current != self.header:
            if current.size < min_col.size:
                min_col = current
            current = current.right
        
        self._cover(min_col)
        
        row_node = min_col.down
        while row_node != min_col:
            self._solution_nodes.append(row_node)
            
            current_node = row_node.right
            while current_node != row_node:
                self._cover(current_node.column)
                current_node = current_node.right
            
            self._search(limit)
            
            if self._solutions_count >= limit:
                # 恢复现场并提前返回
                current_node = row_node.left
                while current_node != row_node:
                    self._uncover(current_node.column)
                    current_node = current_node.left
                self._uncover(min_col)
                return

            # 回溯
            self._solution_nodes.pop()
            current_node = row_node.left
            while current_node != row_node:
                self._uncover(current_node.column)
                current_node = current_node.left
            
            row_node = row_node.down
            
        self._uncover(min_col)


class Sudoku:
    def __init__(self):
        """初始化数独实例"""
        self.board = [[None]*9 for _ in range(9)]  # 9x9 数独矩阵 (None 表示空格)
        self.solution = None  # 存储完整解
        self.difficulty = "Easy"  # 默认难度级别
    
    def generate(self, difficulty="简单"):
        """生成指定难度的数独谜题
        
        参数:
            difficulty: 难度级别 ('入门', '简单', '中等', '困难', '专家', '地狱')
        
        返回:
            (puzzle, elapsed, remaining, solution_count): 包含谜题、耗时、剩余数字和解数量的元组
        """
        start_time = time.time()
        # 生成完整解
        self._backtrack_generate()
        # 保存完整解
        full_board = [row[:] for row in self.board]
        # 挖洞
        self._drill_holes(difficulty)
        # 返回谜题 (挖洞后的板)
        puzzle = [row[:] for row in self.board]
        # 恢复完整解到self.solution
        self.solution = full_board
        
        # 验证生成结果
        elapsed = time.time() - start_time
        remaining = sum(1 for row in puzzle for cell in row if cell is not None)
        
        # 使用新的方法验证唯一解
        board_copy = [row[:] for row in self.board]
        solution_count = self._count_solutions_dlx()
        self.board = board_copy

        if solution_count != 1:
            print(f"警告: 生成的数独不满足唯一解要求! (解的数量: {solution_count})")
            
        return puzzle, elapsed, remaining, solution_count
    
    def _backtrack_generate(self):
        """使用回溯生成一个完整的数独板"""
        # 初始化一个空板
        self.board = [[None]*9 for _ in range(9)]
        # 使用递归回溯填充
        def backtrack(pos):
            if pos == 81:
                return True
            row = pos // 9
            col = pos % 9
            # 随机打乱数字顺序
            numbers = list(range(1,10))
            random.shuffle(numbers)
            for num in numbers:
                if self._is_valid_placement(row, col, num):
                    self.board[row][col] = num
                    if backtrack(pos+1):
                        return True
                    self.board[row][col] = None
            return False
        
        backtrack(0)
    
    def _is_valid_placement(self, row, col, num):
        """检查在(row, col)放置num是否有效"""
        # 检查行
        for c in range(9):
            if self.board[row][c] == num:
                return False
        
        # 检查列
        for r in range(9):
            if self.board[r][col] == num:
                return False
        
        # 检查3x3宫格
        box_row = row // 3 * 3
        box_col = col // 3 * 3
        for r in range(box_row, box_row+3):
            for c in range(box_col, box_col+3):
                if self.board[r][c] == num:
                    return False
        
        return True
    
    def _drill_holes(self, difficulty):
        """根据难度挖洞，并确保唯一解"""
        # 难度 -> (最少保留, 最多保留)
        difficulty_map = {
            "入门": (51, 55),
            "简单": (41, 50), "Easy": (41, 50),
            "中等": (31, 40), "Medium": (31, 40),
            "困难": (26, 30), "Hard": (26, 30),
            "专家": (22, 25),
            "地狱": (17, 21),
        }
        
        if difficulty not in difficulty_map:
            raise ValueError(f"未知的难度级别: {difficulty}")
            
        min_remaining, max_remaining = difficulty_map[difficulty]
        
        # 计算需要挖掉的数量
        remaining = random.randint(min_remaining, max_remaining)
        to_remove = 81 - remaining
        
        # 获取所有位置的列表，并随机打乱
        positions = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(positions)
        
        # 依次尝试移除每个位置上的数字，并验证唯一解
        removed = 0
        for (row, col) in positions:
            if removed >= to_remove:
                break
            
            if self.board[row][col] is not None:
                num = self.board[row][col]
                self.board[row][col] = None
                
                # 使用DLX验证唯一解
                if self._count_solutions_dlx() == 1:
                    removed += 1
                else:
                    self.board[row][col] = num # 恢复
    
    def solve(self):
        """求解数独，返回是否成功和耗时（使用DLX算法）"""
        if not self.validate():
            print("错误：数独板无效，包含非法数字或冲突")
            return False, 0

        start_time = time.time()
        
        solver, mapping = self._convert_to_exact_cover()
        solution_rows = solver.solve()
        
        elapsed = time.time() - start_time
        
        if solution_rows:
            # 应用解到数独板
            for row_idx in solution_rows:
                if row_idx < len(mapping):
                    r, c, num = mapping[row_idx]
                    self.board[r][c] = num + 1
            return True, elapsed
        else:
            return False, elapsed
    
    def _count_solutions_dlx(self):
        """使用DLX计算解的数量"""
        solver, _ = self._convert_to_exact_cover()
        return solver.count_solutions(limit=2)

    def _solve_helper(self, pos):
        """递归回溯求解数独"""
        if pos == 81:
            return True
        
        row = pos // 9
        col = pos % 9
        
        # 如果当前位置已有数字，则跳过
        if self.board[row][col] is not None:
            return self._solve_helper(pos+1)
        
        # 尝试1-9的数字
        for num in range(1,10):
            if self._is_valid_placement(row, col, num):
                self.board[row][col] = num
                if self._solve_helper(pos+1):
                    return True
                self.board[row][col] = None
        
        return False

    def validate(self):
        """验证当前数独板是否符合规则"""
        # 验证所有行
        for row in self.board:
            if not self._is_valid_unit(row):
                return False
        
        # 验证所有列
        for col_index in range(9):
            column = [self.board[row][col_index] for row in range(9)]
            if not self._is_valid_unit(column):
                return False
        
        # 验证所有 3x3 宫格
        for box_row in range(0, 9, 3):
            for box_col in range(0, 9, 3):
                box = []
                for r in range(box_row, box_row+3):
                    for c in range(box_col, box_col+3):
                        box.append(self.board[r][c])
                if not self._is_valid_unit(box):
                    return False
        
        return True
    
    def _is_valid_unit(self, unit):
        """验证单个单元（行/列/宫格）的有效性"""
        numbers = [num for num in unit if num is not None]
        if len(numbers) != len(set(numbers)):
            return False
        if any(num < 1 or num > 9 for num in numbers):
            return False
        return True

    def _convert_to_exact_cover(self):
        """将数独转换为精确覆盖问题，并返回DLXSolver实例和行映射"""
        num_cols = 324  # 4 * 9 * 9
        solver = DLXSolver(num_cols)
        row_mapping = []
        
        for r in range(9):
            for c in range(9):
                if self.board[r][c] is not None:
                    num = self.board[r][c] - 1
                    row_data = self._get_constraint_indices(r, c, num)
                    solver.add_row(row_data, len(row_mapping))
                    row_mapping.append((r, c, num))
                else:
                    for num in range(9):
                        row_data = self._get_constraint_indices(r, c, num)
                        solver.add_row(row_data, len(row_mapping))
                        row_mapping.append((r, c, num))
                        
        return solver, row_mapping
    
    def _get_constraint_indices(self, row, col, num):
        """获取约束索引（行、列、宫、单元格）"""
        box = (row // 3) * 3 + (col // 3)
        return [
            row * 9 + num,
            81 + col * 9 + num,
            162 + box * 9 + num,
            243 + row * 9 + col
        ]
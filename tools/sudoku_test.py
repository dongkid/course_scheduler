from sudoku import Sudoku

def run_test():
    print("=== 数独求解功能测试 ===")
    
    # 创建一个已知可解的数独谜题
    puzzle = [
        [5, 3, None, None, 7, None, None, None, None],
        [6, None, None, 1, 9, 5, None, None, None],
        [None, 9, 8, None, None, None, None, 6, None],
        [8, None, None, None, 6, None, None, None, 3],
        [4, None, None, 8, None, 3, None, None, 1],
        [7, None, None, None, 2, None, None, None, 6],
        [None, 6, None, None, None, None, 2, 8, None],
        [None, None, None, 4, 1, 9, None, None, 5],
        [None, None, None, None, 8, None, None, 7, 9]
    ]
    
    sudoku = Sudoku()
    sudoku.board = puzzle
    
    print("测试数独谜题:")
    for row in puzzle:
        print(row)
    
    print("\n尝试求解...")
    if sudoku.solve():
        print("\n求解成功! 解为:")
        for row in sudoku.board:
            print(row)
    else:
        print("\n求解失败: 无解")

if __name__ == "__main__":
    run_test()
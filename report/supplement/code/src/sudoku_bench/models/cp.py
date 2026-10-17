"""IBM CP Optimizer Sudoku model using integer cells and all-different."""

from sudoku_bench.puzzle import Puzzle


def build_cp_model(puzzle: Puzzle):
    from docplex.cp.model import CpoModel, all_diff, integer_var

    size, box_size = puzzle.size, puzzle.box_size
    model = CpoModel(name=f"sudoku_{puzzle.puzzle_id or size}")
    cells = {(row, column): integer_var(min=1, max=size, name=f"x_{row}_{column}")
             for row in range(size) for column in range(size)}

    for row in range(size):
        model.add(all_diff([cells[row, column] for column in range(size)]))
    for column in range(size):
        model.add(all_diff([cells[row, column] for row in range(size)]))
    for top in range(0, size, box_size):
        for left in range(0, size, box_size):
            model.add(all_diff([cells[row, column]
                                for row in range(top, top + box_size)
                                for column in range(left, left + box_size)]))
    for row in range(size):
        for column in range(size):
            if puzzle.grid[row][column]:
                model.add(cells[row, column] == puzzle.grid[row][column])
    return model, cells

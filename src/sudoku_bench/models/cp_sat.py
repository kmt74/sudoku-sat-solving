"""OR-Tools CP-SAT Sudoku model using integer cells and all-different."""

from sudoku_bench.puzzle import Puzzle


def build_cp_sat_model(puzzle: Puzzle):
    from ortools.sat.python import cp_model

    size, box_size = puzzle.size, puzzle.box_size
    model = cp_model.CpModel()
    cells = {(row, column): model.NewIntVar(1, size, f"x_{row}_{column}")
             for row in range(size) for column in range(size)}

    for row in range(size):
        model.AddAllDifferent([cells[row, column] for column in range(size)])
    for column in range(size):
        model.AddAllDifferent([cells[row, column] for row in range(size)])
    for top in range(0, size, box_size):
        for left in range(0, size, box_size):
            model.AddAllDifferent([cells[row, column]
                                   for row in range(top, top + box_size)
                                   for column in range(left, left + box_size)])
    for row in range(size):
        for column in range(size):
            if puzzle.grid[row][column]:
                model.Add(cells[row, column] == puzzle.grid[row][column])
    return model, cells

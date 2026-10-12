"""Shared binary MIP formulation used by CPLEX and Gurobi adapters."""

from collections.abc import Iterator

from sudoku_bench.puzzle import Puzzle


Index = tuple[int, int, int]


def exactly_one_groups(puzzle: Puzzle) -> Iterator[tuple[Index, ...]]:
    """Yield cell, row-digit, column-digit and box-digit equality groups."""
    size, box_size = puzzle.size, puzzle.box_size
    for row in range(size):
        for column in range(size):
            yield tuple((row, column, digit) for digit in range(1, size + 1))
    for digit in range(1, size + 1):
        for row in range(size):
            yield tuple((row, column, digit) for column in range(size))
        for column in range(size):
            yield tuple((row, column, digit) for row in range(size))
        for top in range(0, size, box_size):
            for left in range(0, size, box_size):
                yield tuple((row, column, digit)
                            for row in range(top, top + box_size)
                            for column in range(left, left + box_size))


def clue_indices(puzzle: Puzzle) -> Iterator[Index]:
    for row in range(puzzle.size):
        for column in range(puzzle.size):
            digit = puzzle.grid[row][column]
            if digit:
                yield row, column, digit


def build_cplex_mip_model(puzzle: Puzzle):
    from docplex.mp.model import Model

    size = puzzle.size
    model = Model(name=f"sudoku_{puzzle.puzzle_id or size}")
    variables = {(row, column, digit): model.binary_var(name=f"x_{row}_{column}_{digit}")
                 for row in range(size) for column in range(size)
                 for digit in range(1, size + 1)}
    for group in exactly_one_groups(puzzle):
        model.add_constraint(model.sum(variables[index] for index in group) == 1)
    for index in clue_indices(puzzle):
        model.add_constraint(variables[index] == 1)
    model.minimize(0)
    return model, variables


def build_gurobi_mip_model(puzzle: Puzzle):
    import gurobipy as gp

    size = puzzle.size
    model = gp.Model(name=f"sudoku_{puzzle.puzzle_id or size}")
    model.Params.OutputFlag = 0
    variables = model.addVars(range(size), range(size), range(1, size + 1),
                              vtype=gp.GRB.BINARY, name="x")
    for group in exactly_one_groups(puzzle):
        model.addConstr(gp.quicksum(variables[index] for index in group) == 1)
    for index in clue_indices(puzzle):
        model.addConstr(variables[index] == 1)
    model.setObjective(0, gp.GRB.MINIMIZE)
    model.update()
    return model, variables

"""Check a completed Sudoku independently of the solver that produced it."""

from collections.abc import Iterable

from .puzzle import Grid, Puzzle


def _candidate_grid(rows: Iterable[Iterable[int]]) -> Grid | None:
    try:
        return tuple(tuple(row) for row in rows)
    except (TypeError, ValueError):
        return None


def validate_solution(puzzle: Puzzle, solution: Iterable[Iterable[int]]) -> bool:
    """Return whether ``solution`` is a complete solution to ``puzzle``.

    Invalid solution shapes and values return False. Invalid puzzle inputs are
    rejected when the Puzzle is constructed.
    """
    grid = _candidate_grid(solution)
    size = puzzle.size
    box_size = puzzle.box_size
    digits = set(range(1, size + 1))

    if grid is None or len(grid) != size or any(len(row) != size for row in grid):
        return False
    if any(type(value) is not int for row in grid for value in row):
        return False

    for row in range(size):
        if set(grid[row]) != digits:
            return False
        for column in range(size):
            clue = puzzle.grid[row][column]
            if clue != 0 and grid[row][column] != clue:
                return False

    for column in range(size):
        if {grid[row][column] for row in range(size)} != digits:
            return False

    for top in range(0, size, box_size):
        for left in range(0, size, box_size):
            values = {
                grid[row][column]
                for row in range(top, top + box_size)
                for column in range(left, left + box_size)
            }
            if values != digits:
                return False

    return True

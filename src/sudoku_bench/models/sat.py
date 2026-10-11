"""Build a Sudoku SAT formula with sequential at-most-one constraints."""

from dataclasses import dataclass

from sudoku_bench.encodings.sequential import at_most_one
from sudoku_bench.puzzle import Grid, Puzzle


Clause = tuple[int, ...]


def cell_variable(size: int, row: int, column: int, digit: int) -> int:
    """Map x[row,column,digit] to a positive SAT variable (zero-based cell)."""
    return (row * size + column) * size + digit


@dataclass(frozen=True, slots=True)
class SatModel:
    size: int
    clauses: tuple[Clause, ...]
    variable_count: int

    @property
    def clause_count(self) -> int:
        return len(self.clauses)


def build_sat_model(puzzle: Puzzle) -> SatModel:
    """Encode each cell and each digit in a row, column and box exactly once."""
    size = puzzle.size
    box_size = puzzle.box_size
    clauses: list[Clause] = []
    next_variable = size**3 + 1

    def new_var() -> int:
        nonlocal next_variable
        variable = next_variable
        next_variable += 1
        return variable

    def exactly_one(literals: list[int]) -> None:
        clauses.append(tuple(literals))  # At least one.
        clauses.extend(at_most_one(literals, new_var))

    for row in range(size):
        for column in range(size):
            exactly_one([cell_variable(size, row, column, digit) for digit in range(1, size + 1)])

    for digit in range(1, size + 1):
        for row in range(size):
            exactly_one([cell_variable(size, row, column, digit) for column in range(size)])
        for column in range(size):
            exactly_one([cell_variable(size, row, column, digit) for row in range(size)])
        for top in range(0, size, box_size):
            for left in range(0, size, box_size):
                exactly_one(
                    [
                        cell_variable(size, row, column, digit)
                        for row in range(top, top + box_size)
                        for column in range(left, left + box_size)
                    ]
                )

    for row in range(size):
        for column in range(size):
            clue = puzzle.grid[row][column]
            if clue:
                clauses.append((cell_variable(size, row, column, clue),))

    return SatModel(size=size, clauses=tuple(clauses), variable_count=next_variable - 1)


def decode_sat_model(size: int, assignment: list[int]) -> Grid:
    """Decode true cell variables; reject missing or duplicate digit choices."""
    cells = [[0] * size for _ in range(size)]
    for literal in assignment:
        if 0 < literal <= size**3:
            index = literal - 1
            row, remainder = divmod(index, size * size)
            column, digit_index = divmod(remainder, size)
            if cells[row][column] != 0:
                raise ValueError("SAT assignment has multiple digits in a cell")
            cells[row][column] = digit_index + 1

    if any(value == 0 for row in cells for value in row):
        raise ValueError("SAT assignment has an empty cell")
    return tuple(tuple(row) for row in cells)

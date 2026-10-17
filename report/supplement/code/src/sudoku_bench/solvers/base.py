"""Result contract shared by all Sudoku solver adapters."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Callable

from sudoku_bench.puzzle import Grid, Puzzle
from sudoku_bench.validator import validate_solution


class SolveStatus(StrEnum):
    SOLVED = "SOLVED"
    UNSAT = "UNSAT"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class SolveResult:
    status: SolveStatus
    solution: Grid | None = None
    build_time_s: float = 0.0
    solve_time_s: float = 0.0
    message: str = ""
    model_variables: int | None = None
    model_constraints: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, SolveStatus):
            raise ValueError("status must be a SolveStatus")
        if self.status is SolveStatus.SOLVED and self.solution is None:
            raise ValueError("SOLVED requires a solution")
        if self.status is not SolveStatus.SOLVED and self.solution is not None:
            raise ValueError("only SOLVED may contain a solution")
        for name in ("build_time_s", "solve_time_s"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite nonnegative number")
        for name in ("model_variables", "model_constraints"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{name} must be a nonnegative integer or None")

    @property
    def total_time_s(self) -> float:
        return self.build_time_s + self.solve_time_s


def decode_binary_assignment(size: int, value: Callable[[int, int, int], float]) -> Grid:
    """Extract exactly one digit per cell from binary MIP variables."""
    rows: list[tuple[int, ...]] = []
    for row in range(size):
        digits: list[int] = []
        for column in range(size):
            selected = [digit for digit in range(1, size + 1)
                        if value(row, column, digit) > 0.5]
            if len(selected) != 1:
                raise ValueError(f"cell ({row}, {column}) has {len(selected)} selected digits")
            digits.append(selected[0])
        rows.append(tuple(digits))
    return tuple(rows)


def checked_solution(puzzle: Puzzle, solution: Grid, build_time_s: float,
                     solve_time_s: float, message: str = "",
                     model_variables: int | None = None,
                     model_constraints: int | None = None) -> SolveResult:
    counts = {"model_variables": model_variables, "model_constraints": model_constraints}
    if not validate_solution(puzzle, solution):
        return SolveResult(SolveStatus.ERROR, build_time_s=build_time_s,
                           solve_time_s=solve_time_s, message="solver returned an invalid Sudoku solution",
                           **counts)
    return SolveResult(SolveStatus.SOLVED, solution=solution, build_time_s=build_time_s,
                       solve_time_s=solve_time_s, message=message, **counts)

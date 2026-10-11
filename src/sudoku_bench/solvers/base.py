"""Result contract shared by all Sudoku solver adapters."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from sudoku_bench.puzzle import Grid


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

    @property
    def total_time_s(self) -> float:
        return self.build_time_s + self.solve_time_s

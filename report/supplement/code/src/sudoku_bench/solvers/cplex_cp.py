"""Run IBM CP Optimizer through DOcplex.CP."""

import os
import shutil
from time import perf_counter

from sudoku_bench.models.cp import build_cp_model
from sudoku_bench.puzzle import Puzzle
from sudoku_bench.solvers.base import SolveResult, SolveStatus, checked_solution


def solve_cplex_cp(puzzle: Puzzle, time_limit_s: float | None = None) -> SolveResult:
    try:
        import docplex.cp.model  # noqa: F401
    except ImportError as exc:
        return SolveResult(SolveStatus.ERROR, message=f"DOcplex.CP is unavailable: {exc}")
    executable = os.getenv("CP_OPTIMIZER_EXECUTABLE") or shutil.which("cpoptimizer")
    if not executable or not os.path.isfile(executable):
        return SolveResult(SolveStatus.ERROR, message=(
            "CP Optimizer executable not found; install IBM ILOG CPLEX Optimization Studio "
            "and set CP_OPTIMIZER_EXECUTABLE to cpoptimizer.exe"
        ))

    build_started = perf_counter()
    try:
        model, cells = build_cp_model(puzzle)
        counts = {"model_variables": len(cells),
                  "model_constraints": 3 * puzzle.size + puzzle.clue_count}
        build_time = perf_counter() - build_started
    except Exception as exc:
        return SolveResult(SolveStatus.ERROR, build_time_s=perf_counter() - build_started,
                           message=f"{type(exc).__name__}: {exc}")

    solve_started = perf_counter()
    try:
        options = {"Workers": 1, "LogVerbosity": "Quiet", "log_output": None,
                   "execfile": executable}
        if time_limit_s is not None:
            options["TimeLimit"] = time_limit_s
        result = model.solve(**options)
        status = result.get_solve_status()
        if result.is_solution():
            solution = tuple(tuple(int(result.get_value(cells[row, column]))
                                   for column in range(puzzle.size))
                             for row in range(puzzle.size))
            return checked_solution(puzzle, solution, build_time,
                                    perf_counter() - solve_started, message=status, **counts)
        if status == "Infeasible":
            return SolveResult(SolveStatus.UNSAT, build_time_s=build_time,
                               solve_time_s=perf_counter() - solve_started, **counts)
        if result.get_fail_status() == "SearchStoppedByLimit":
            return SolveResult(SolveStatus.TIMEOUT, build_time_s=build_time,
                               solve_time_s=perf_counter() - solve_started, **counts)
        return SolveResult(SolveStatus.ERROR, build_time_s=build_time,
                           solve_time_s=perf_counter() - solve_started,
                           message=f"CP Optimizer status: {status}; {result.get_fail_status()}",
                           **counts)
    except Exception as exc:
        return SolveResult(SolveStatus.ERROR, build_time_s=build_time,
                           solve_time_s=perf_counter() - solve_started,
                           message=f"{type(exc).__name__}: {exc}", **counts)

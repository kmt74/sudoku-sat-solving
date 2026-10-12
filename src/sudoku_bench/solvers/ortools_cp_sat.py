"""Run OR-Tools CP-SAT with a single worker and a common result contract."""

from time import perf_counter

from sudoku_bench.models.cp_sat import build_cp_sat_model
from sudoku_bench.puzzle import Puzzle
from sudoku_bench.solvers.base import SolveResult, SolveStatus, checked_solution


def solve_cp_sat(puzzle: Puzzle, time_limit_s: float | None = None) -> SolveResult:
    try:
        from ortools.sat.python import cp_model
    except ImportError as exc:
        return SolveResult(SolveStatus.ERROR, message=f"OR-Tools is unavailable: {exc}")

    build_started = perf_counter()
    try:
        model, cells = build_cp_sat_model(puzzle)
        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = 0
        if time_limit_s is not None:
            solver.parameters.max_time_in_seconds = time_limit_s
        counts = {"model_variables": len(cells),
                  "model_constraints": 3 * puzzle.size + puzzle.clue_count}
        build_time = perf_counter() - build_started
    except Exception as exc:
        return SolveResult(SolveStatus.ERROR, build_time_s=perf_counter() - build_started,
                           message=f"{type(exc).__name__}: {exc}")

    solve_started = perf_counter()
    try:
        status = solver.Solve(model)
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            solution = tuple(tuple(solver.Value(cells[row, column])
                                   for column in range(puzzle.size))
                             for row in range(puzzle.size))
            return checked_solution(puzzle, solution, build_time,
                                    perf_counter() - solve_started, **counts)
        if status == cp_model.INFEASIBLE:
            return SolveResult(SolveStatus.UNSAT, build_time_s=build_time,
                               solve_time_s=perf_counter() - solve_started, **counts)
        if status == cp_model.UNKNOWN and time_limit_s is not None:
            return SolveResult(SolveStatus.TIMEOUT, build_time_s=build_time,
                               solve_time_s=perf_counter() - solve_started, **counts)
        return SolveResult(SolveStatus.ERROR, build_time_s=build_time,
                           solve_time_s=perf_counter() - solve_started,
                           message=f"CP-SAT status: {solver.StatusName(status)}", **counts)
    except Exception as exc:
        return SolveResult(SolveStatus.ERROR, build_time_s=build_time,
                           solve_time_s=perf_counter() - solve_started,
                           message=f"{type(exc).__name__}: {exc}", **counts)

"""Run the shared binary Sudoku MIP with IBM CPLEX."""

from time import perf_counter

from sudoku_bench.models.mip import build_cplex_mip_model
from sudoku_bench.puzzle import Puzzle
from sudoku_bench.solvers.base import (SolveResult, SolveStatus, checked_solution,
                                        decode_binary_assignment)


def solve_cplex_mip(puzzle: Puzzle, time_limit_s: float | None = None) -> SolveResult:
    try:
        import cplex  # noqa: F401
        import docplex.mp.model  # noqa: F401
    except ImportError as exc:
        return SolveResult(SolveStatus.ERROR, message=f"CPLEX MIP is unavailable: {exc}")

    build_started = perf_counter()
    try:
        model, variables = build_cplex_mip_model(puzzle)
        model.parameters.threads = 1
        model.parameters.randomseed = 0
        if time_limit_s is not None:
            model.time_limit = time_limit_s
        counts = {"model_variables": len(variables),
                  "model_constraints": 4 * puzzle.size**2 + puzzle.clue_count}
        build_time = perf_counter() - build_started
    except Exception as exc:
        return SolveResult(SolveStatus.ERROR, build_time_s=perf_counter() - build_started,
                           message=f"{type(exc).__name__}: {exc}")

    solve_started = perf_counter()
    try:
        solution = model.solve(log_output=False)
        if solution is not None:
            grid = decode_binary_assignment(
                puzzle.size,
                lambda row, column, digit: solution.get_value(variables[row, column, digit]),
            )
            return checked_solution(puzzle, grid, build_time, perf_counter() - solve_started,
                                    message=str(model.solve_details.status), **counts)
        status = str(model.solve_details.status or "").lower()
        if "time" in status and "limit" in status:
            result_status = SolveStatus.TIMEOUT
        elif "infeasible" in status and "infeasible or unbounded" not in status:
            result_status = SolveStatus.UNSAT
        else:
            result_status = SolveStatus.ERROR
        return SolveResult(result_status, build_time_s=build_time,
                           solve_time_s=perf_counter() - solve_started,
                           message=f"CPLEX status: {model.solve_details.status}", **counts)
    except Exception as exc:
        return SolveResult(SolveStatus.ERROR, build_time_s=build_time,
                           solve_time_s=perf_counter() - solve_started,
                           message=f"{type(exc).__name__}: {exc}", **counts)
    finally:
        model.end()

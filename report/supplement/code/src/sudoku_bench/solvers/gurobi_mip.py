"""Run the shared binary Sudoku MIP with Gurobi."""

from time import perf_counter

from sudoku_bench.models.mip import build_gurobi_mip_model
from sudoku_bench.puzzle import Puzzle
from sudoku_bench.solvers.base import (SolveResult, SolveStatus, checked_solution,
                                        decode_binary_assignment)


def solve_gurobi_mip(puzzle: Puzzle, time_limit_s: float | None = None) -> SolveResult:
    try:
        import gurobipy as gp
    except ImportError as exc:
        return SolveResult(SolveStatus.ERROR, message=f"Gurobi is unavailable: {exc}")

    build_started = perf_counter()
    try:
        model, variables = build_gurobi_mip_model(puzzle)
        model.Params.Threads = 1
        model.Params.Seed = 0
        if time_limit_s is not None:
            model.Params.TimeLimit = time_limit_s
        counts = {"model_variables": len(variables),
                  "model_constraints": 4 * puzzle.size**2 + puzzle.clue_count}
        build_time = perf_counter() - build_started
    except Exception as exc:
        return SolveResult(SolveStatus.ERROR, build_time_s=perf_counter() - build_started,
                           message=f"{type(exc).__name__}: {exc}")

    solve_started = perf_counter()
    try:
        model.optimize()
        if model.SolCount > 0:
            grid = decode_binary_assignment(
                puzzle.size,
                lambda row, column, digit: variables[row, column, digit].X,
            )
            return checked_solution(puzzle, grid, build_time, perf_counter() - solve_started,
                                    message=f"Gurobi status: {model.Status}", **counts)
        if model.Status == gp.GRB.INFEASIBLE:
            status = SolveStatus.UNSAT
        elif model.Status == gp.GRB.TIME_LIMIT:
            status = SolveStatus.TIMEOUT
        else:
            status = SolveStatus.ERROR
        return SolveResult(status, build_time_s=build_time,
                           solve_time_s=perf_counter() - solve_started,
                           message=f"Gurobi status: {model.Status}", **counts)
    except Exception as exc:
        return SolveResult(SolveStatus.ERROR, build_time_s=build_time,
                           solve_time_s=perf_counter() - solve_started,
                           message=f"{type(exc).__name__}: {exc}", **counts)
    finally:
        model.dispose()

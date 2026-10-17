"""Solve Sudoku CNF with PySAT and validate the decoded board."""

from __future__ import annotations

import argparse
from math import isfinite
from threading import Event, Timer
from time import perf_counter

from sudoku_bench.encodings import ENCODINGS
from sudoku_bench.models.sat import build_sat_model, decode_sat_model
from sudoku_bench.puzzle import Puzzle, load_puzzle
from sudoku_bench.solvers.base import SolveResult, SolveStatus
from sudoku_bench.validator import validate_solution


def solve_sat(puzzle: Puzzle, solver_name: str = "g3", encoding: str = "sequential",
              time_limit_s: float | None = None) -> SolveResult:
    """Return a common result; ``g3`` is PySAT's Glucose3 solver."""
    if time_limit_s is not None and (not isfinite(time_limit_s) or time_limit_s <= 0):
        return SolveResult(SolveStatus.ERROR, message="time_limit_s must be positive")
    try:
        from pysat.solvers import Solver
    except ImportError as exc:
        return SolveResult(SolveStatus.ERROR, message=f"PySAT is unavailable: {exc}")

    build_started = perf_counter()
    try:
        model = build_sat_model(puzzle, encoding=encoding)
        counts = {"model_variables": model.variable_count,
                  "model_constraints": model.clause_count}
        with Solver(name=solver_name, bootstrap_with=model.clauses) as solver:
            build_time = perf_counter() - build_started
            solve_started = perf_counter()
            try:
                timed_out = Event()
                if time_limit_s is None:
                    satisfiable = solver.solve()
                else:
                    def interrupt_solver() -> None:
                        timed_out.set()
                        solver.interrupt()

                    timer = Timer(time_limit_s, interrupt_solver)
                    timer.daemon = True
                    timer.start()
                    try:
                        satisfiable = solver.solve_limited(expect_interrupt=True)
                    finally:
                        timer.cancel()
                        timer.join()
                        solver.clear_interrupt()
                if satisfiable is False:
                    return SolveResult(SolveStatus.UNSAT, build_time_s=build_time,
                                       solve_time_s=perf_counter() - solve_started, **counts)
                if satisfiable is not True:
                    status = SolveStatus.TIMEOUT if timed_out.is_set() else SolveStatus.ERROR
                    return SolveResult(status, build_time_s=build_time,
                                       solve_time_s=perf_counter() - solve_started,
                                       message="SAT search interrupted without a decision", **counts)

                assignment = solver.get_model()
                if assignment is None:
                    raise ValueError("SAT solver returned no assignment")
                solution = decode_sat_model(puzzle.size, assignment)
                if not validate_solution(puzzle, solution):
                    raise ValueError("SAT solver returned an invalid Sudoku solution")
                return SolveResult(SolveStatus.SOLVED, solution=solution,
                                   build_time_s=build_time,
                                   solve_time_s=perf_counter() - solve_started, **counts)
            except Exception as exc:
                return SolveResult(SolveStatus.ERROR, build_time_s=build_time,
                                   solve_time_s=perf_counter() - solve_started,
                                   message=f"{type(exc).__name__}: {exc}", **counts)
    except Exception as exc:
        return SolveResult(SolveStatus.ERROR, build_time_s=perf_counter() - build_started,
                           message=f"{type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Solve one Sudoku JSON puzzle using SAT/PySAT.")
    parser.add_argument("puzzle", help="Path to a puzzle JSON file")
    parser.add_argument("--solver", default="g3", help="PySAT solver name (default: g3)")
    parser.add_argument("--encoding", choices=sorted(ENCODINGS), default="sequential")
    parser.add_argument("--time-limit", type=float, default=None, metavar="SECONDS")
    args = parser.parse_args()

    try:
        puzzle = load_puzzle(args.puzzle)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    result = solve_sat(puzzle, solver_name=args.solver, encoding=args.encoding,
                       time_limit_s=args.time_limit)
    print(f"status: {result.status.value}")
    print(f"build_time_s: {result.build_time_s:.6f}")
    print(f"solve_time_s: {result.solve_time_s:.6f}")
    if result.message:
        print(f"message: {result.message}")
    if result.solution is not None:
        for row in result.solution:
            print(" ".join(str(value) for value in row))
    return 0 if result.status is SolveStatus.SOLVED else 1


if __name__ == "__main__":
    raise SystemExit(main())

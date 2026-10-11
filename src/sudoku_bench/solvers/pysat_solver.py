"""Solve Sudoku CNF with PySAT and validate the decoded board."""

from __future__ import annotations

import argparse
from time import perf_counter

from sudoku_bench.models.sat import build_sat_model, decode_sat_model
from sudoku_bench.puzzle import Puzzle, load_puzzle
from sudoku_bench.solvers.base import SolveResult, SolveStatus
from sudoku_bench.validator import validate_solution


def solve_sat(puzzle: Puzzle, solver_name: str = "g3") -> SolveResult:
    """Return a common result; ``g3`` is PySAT's Glucose3 solver."""
    try:
        from pysat.solvers import Solver
    except ImportError as exc:
        return SolveResult(SolveStatus.ERROR, message=f"PySAT is unavailable: {exc}")

    build_started = perf_counter()
    try:
        model = build_sat_model(puzzle)
        with Solver(name=solver_name, bootstrap_with=model.clauses) as solver:
            build_time = perf_counter() - build_started
            solve_started = perf_counter()
            try:
                satisfiable = solver.solve()
                if satisfiable is False:
                    return SolveResult(SolveStatus.UNSAT, build_time_s=build_time,
                                       solve_time_s=perf_counter() - solve_started)
                if satisfiable is not True:
                    raise RuntimeError("SAT solver returned no conclusive status")

                assignment = solver.get_model()
                if assignment is None:
                    raise ValueError("SAT solver returned no assignment")
                solution = decode_sat_model(puzzle.size, assignment)
                if not validate_solution(puzzle, solution):
                    raise ValueError("SAT solver returned an invalid Sudoku solution")
                return SolveResult(SolveStatus.SOLVED, solution=solution,
                                   build_time_s=build_time,
                                   solve_time_s=perf_counter() - solve_started)
            except Exception as exc:
                return SolveResult(SolveStatus.ERROR, build_time_s=build_time,
                                   solve_time_s=perf_counter() - solve_started,
                                   message=f"{type(exc).__name__}: {exc}")
    except Exception as exc:
        return SolveResult(SolveStatus.ERROR, build_time_s=perf_counter() - build_started,
                           message=f"{type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Solve one Sudoku JSON puzzle using SAT/PySAT.")
    parser.add_argument("puzzle", help="Path to a puzzle JSON file")
    parser.add_argument("--solver", default="g3", help="PySAT solver name (default: g3)")
    args = parser.parse_args()

    try:
        puzzle = load_puzzle(args.puzzle)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    result = solve_sat(puzzle, solver_name=args.solver)
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

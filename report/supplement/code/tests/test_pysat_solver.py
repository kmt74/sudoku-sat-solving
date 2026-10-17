"""End-to-end tests for SAT solving on small and standard Sudoku boards."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from sudoku_bench.models.sat import cell_variable
from sudoku_bench.puzzle import Puzzle, load_puzzle
from sudoku_bench.solvers import SolveStatus
from sudoku_bench.solvers.pysat_solver import solve_sat
from sudoku_bench.validator import validate_solution


class AdapterTests(unittest.TestCase):
    def test_decodes_and_validates_solver_assignment(self) -> None:
        puzzle = Puzzle.from_rows([
            [1, 0, 0, 4],
            [0, 4, 1, 0],
            [0, 1, 4, 0],
            [4, 0, 0, 1],
        ])
        solution = ((1, 2, 3, 4), (3, 4, 1, 2), (2, 1, 4, 3), (4, 3, 2, 1))
        assignment = [
            cell_variable(4, row, column, digit)
            for row, values in enumerate(solution)
            for column, digit in enumerate(values)
        ]

        class FakeSolver:
            outcome: bool | None = True

            def __init__(self, *, name: str, bootstrap_with: object) -> None:
                self.assert_name = name
                self.assert_clauses = bootstrap_with

            def __enter__(self) -> "FakeSolver":
                return self

            def __exit__(self, *args: object) -> None:
                pass

            def solve(self) -> bool | None:
                return self.outcome

            def get_model(self) -> list[int]:
                return assignment

        package = types.ModuleType("pysat")
        package.__path__ = []
        solvers = types.ModuleType("pysat.solvers")
        solvers.Solver = FakeSolver
        with patch.dict(sys.modules, {"pysat": package, "pysat.solvers": solvers}):
            for outcome, expected in ((True, SolveStatus.SOLVED),
                                      (False, SolveStatus.UNSAT),
                                      (None, SolveStatus.ERROR)):
                with self.subTest(outcome=outcome):
                    FakeSolver.outcome = outcome
                    result = solve_sat(puzzle)
                    self.assertEqual(result.status, expected, result.message)
                    self.assertEqual(result.solution, solution if outcome is True else None)


@unittest.skipUnless(importlib.util.find_spec("pysat"), "install python-sat to run integration tests")
class PySatSolverTests(unittest.TestCase):
    def test_solves_4x4(self) -> None:
        puzzle = Puzzle.from_rows([
            [1, 0, 0, 4],
            [0, 4, 1, 0],
            [0, 1, 4, 0],
            [4, 0, 0, 1],
        ])
        result = solve_sat(puzzle)
        self.assertEqual(result.status, SolveStatus.SOLVED, result.message)
        self.assertTrue(validate_solution(puzzle, result.solution))
        self.assertGreaterEqual(result.build_time_s, 0)
        self.assertGreaterEqual(result.solve_time_s, 0)

    def test_solves_9x9_json(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "9x9" / "example.json"
        puzzle = load_puzzle(path)
        for encoding in ("binary", "commander", "product", "sequential"):
            with self.subTest(encoding=encoding):
                result = solve_sat(puzzle, encoding=encoding, time_limit_s=5)
                self.assertEqual(result.status, SolveStatus.SOLVED, result.message)
                self.assertTrue(validate_solution(puzzle, result.solution))
                self.assertGreater(result.model_variables, 0)
                self.assertGreater(result.model_constraints, 0)

    def test_reports_unsat_for_consistent_but_impossible_clues(self) -> None:
        puzzle = Puzzle.from_rows([
            [1, 2, 3, 0],
            [0, 0, 0, 4],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ])
        result = solve_sat(puzzle)
        self.assertEqual(result.status, SolveStatus.UNSAT, result.message)
        self.assertIsNone(result.solution)


if __name__ == "__main__":
    unittest.main()

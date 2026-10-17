"""Check the CP and MIP implementations against the independent validator."""

import importlib.util
import os
import shutil
import unittest

from sudoku_bench.models.cp import build_cp_model
from sudoku_bench.models.mip import clue_indices, exactly_one_groups
from sudoku_bench.puzzle import Puzzle
from sudoku_bench.solvers import SolveStatus
from sudoku_bench.solvers.cplex_cp import solve_cplex_cp
from sudoku_bench.solvers.cplex_mip import solve_cplex_mip
from sudoku_bench.solvers.gurobi_mip import solve_gurobi_mip
from sudoku_bench.solvers.ortools_cp_sat import solve_cp_sat
from sudoku_bench.validator import validate_solution


SOLVABLE = Puzzle.from_rows([
    [1, 0, 0, 4], [0, 4, 1, 0], [0, 1, 4, 0], [4, 0, 0, 1],
])
IMPOSSIBLE = Puzzle.from_rows([
    [1, 2, 3, 0], [0, 0, 0, 4], [0, 0, 0, 0], [0, 0, 0, 0],
])


class SharedMipModelTests(unittest.TestCase):
    def test_both_mip_adapters_use_same_groups(self) -> None:
        groups = list(exactly_one_groups(SOLVABLE))
        self.assertEqual(len(groups), 4 * SOLVABLE.size**2)
        self.assertTrue(all(len(group) == SOLVABLE.size for group in groups))
        self.assertEqual(len(list(clue_indices(SOLVABLE))), SOLVABLE.clue_count)

    @unittest.skipUnless(importlib.util.find_spec("docplex"), "install docplex")
    def test_cp_optimizer_model_builds_without_solver_executable(self) -> None:
        model, cells = build_cp_model(SOLVABLE)
        self.assertEqual(len(cells), SOLVABLE.size**2)
        self.assertGreater(len(model.get_all_expressions()), 0)


class SolverTests(unittest.TestCase):
    def assert_solved(self, method) -> None:
        result = method(SOLVABLE, time_limit_s=5)
        if result.status is SolveStatus.ERROR and "license" in result.message.lower():
            self.skipTest(result.message)
        self.assertEqual(result.status, SolveStatus.SOLVED, result.message)
        self.assertTrue(validate_solution(SOLVABLE, result.solution))
        self.assertGreater(result.model_variables, 0)

    @unittest.skipUnless(importlib.util.find_spec("ortools"), "install ortools")
    def test_cp_sat_solves_and_proves_unsat(self) -> None:
        self.assert_solved(solve_cp_sat)
        self.assertEqual(solve_cp_sat(IMPOSSIBLE, time_limit_s=5).status,
                         SolveStatus.UNSAT)

    @unittest.skipUnless(importlib.util.find_spec("cplex") and
                         importlib.util.find_spec("docplex"), "install cplex and docplex")
    def test_cplex_mip_solves(self) -> None:
        self.assert_solved(solve_cplex_mip)

    @unittest.skipUnless(importlib.util.find_spec("gurobipy"), "install gurobipy")
    def test_gurobi_mip_solves(self) -> None:
        self.assert_solved(solve_gurobi_mip)

    @unittest.skipUnless(importlib.util.find_spec("docplex"), "install docplex")
    def test_cp_optimizer_or_explains_missing_executable(self) -> None:
        result = solve_cplex_cp(SOLVABLE, time_limit_s=5)
        executable = os.getenv("CP_OPTIMIZER_EXECUTABLE") or shutil.which("cpoptimizer")
        if executable and os.path.isfile(executable):
            self.assertEqual(result.status, SolveStatus.SOLVED, result.message)
            self.assertTrue(validate_solution(SOLVABLE, result.solution))
        else:
            self.assertEqual(result.status, SolveStatus.ERROR)
            self.assertIn("CP Optimizer executable not found", result.message)


if __name__ == "__main__":
    unittest.main()

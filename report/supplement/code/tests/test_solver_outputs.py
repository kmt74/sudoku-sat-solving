"""Tests for the result contract used by all solver adapters."""

import unittest

from sudoku_bench.solvers import SolveResult, SolveStatus

class SolveResultTests(unittest.TestCase):
    def test_solved_result_has_solution_and_timings(self) -> None:
        solution = ((1, 2, 3, 4), (3, 4, 1, 2), (2, 1, 4, 3), (4, 3, 2, 1))
        result = SolveResult(SolveStatus.SOLVED, solution, 0.1, 0.2)
        self.assertEqual(result.status, SolveStatus.SOLVED)
        self.assertAlmostEqual(result.total_time_s, 0.3)

    def test_unsolved_statuses_have_no_solution(self) -> None:
        for status in (SolveStatus.UNSAT, SolveStatus.TIMEOUT, SolveStatus.ERROR):
            with self.subTest(status=status):
                self.assertIsNone(SolveResult(status).solution)

    def test_rejects_inconsistent_results(self) -> None:
        with self.assertRaises(ValueError):
            SolveResult(SolveStatus.SOLVED)
        with self.assertRaises(ValueError):
            SolveResult(SolveStatus.TIMEOUT, ((1,),))
        with self.assertRaises(ValueError):
            SolveResult(SolveStatus.ERROR, build_time_s=-1)


if __name__ == "__main__":
    unittest.main()

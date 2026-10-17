"""Tests for Sudoku input validation and independent solution checking."""

import json
import tempfile
import unittest
from pathlib import Path

from sudoku_bench.puzzle import Puzzle, load_puzzle
from sudoku_bench.validator import validate_solution


PUZZLE_ROWS = [
    [1, 0, 0, 4],
    [0, 4, 1, 0],
    [0, 1, 4, 0],
    [4, 0, 0, 1],
]
SOLUTION_ROWS = [
    [1, 2, 3, 4],
    [3, 4, 1, 2],
    [2, 1, 4, 3],
    [4, 3, 2, 1],
]


class PuzzleTests(unittest.TestCase):
    def test_normalizes_grid_and_reports_size(self) -> None:
        puzzle = Puzzle.from_rows(PUZZLE_ROWS, puzzle_id="four-by-four")
        self.assertEqual(puzzle.size, 4)
        self.assertEqual(puzzle.box_size, 2)
        self.assertEqual(puzzle.clue_count, 8)
        self.assertIsInstance(puzzle.grid, tuple)

    def test_rejects_non_square_size_and_ragged_rows(self) -> None:
        with self.assertRaises(ValueError):
            Puzzle.from_rows([[0] * 3 for _ in range(3)])
        with self.assertRaises(ValueError):
            Puzzle.from_rows([[0] * 4, [0] * 4, [0] * 4, [0] * 3])

    def test_rejects_out_of_range_and_non_integer_values(self) -> None:
        for bad_value in (-1, 5, True, 1.5):
            with self.subTest(value=bad_value), self.assertRaises(ValueError):
                rows = [row.copy() for row in PUZZLE_ROWS]
                rows[0][1] = bad_value
                Puzzle.from_rows(rows)

    def test_rejects_conflicting_clues(self) -> None:
        for second_cell in ((0, 2), (2, 0), (1, 1)):
            with self.subTest(second_cell=second_cell), self.assertRaises(ValueError):
                rows = [[0] * 4 for _ in range(4)]
                rows[0][0] = 1
                rows[second_cell[0]][second_cell[1]] = 1
                Puzzle.from_rows(rows)

    def test_loads_json_puzzle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.json"
            path.write_text(json.dumps({"id": "example", "grid": PUZZLE_ROWS,
                                        "source": "unit test", "difficulty": "easy"}),
                            encoding="utf-8")
            puzzle = load_puzzle(path)
        self.assertEqual(puzzle.puzzle_id, "example")
        self.assertEqual(puzzle.size, 4)
        self.assertEqual(puzzle.source, "unit test")
        self.assertEqual(puzzle.difficulty, "easy")


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.puzzle = Puzzle.from_rows(PUZZLE_ROWS)

    def test_accepts_valid_solution(self) -> None:
        self.assertTrue(validate_solution(self.puzzle, SOLUTION_ROWS))

    def test_rejects_changed_clue(self) -> None:
        # Swapping digits globally preserves Sudoku rules, but changes clues.
        rows = [[2 if value == 1 else 1 if value == 2 else value for value in row]
                for row in SOLUTION_ROWS]
        self.assertFalse(validate_solution(self.puzzle, rows))

    def test_rejects_duplicate_and_empty_cells(self) -> None:
        for value in (1, 0):
            with self.subTest(value=value):
                rows = [row.copy() for row in SOLUTION_ROWS]
                rows[0][1] = value
                self.assertFalse(validate_solution(self.puzzle, rows))

    def test_rejects_column_violation(self) -> None:
        blank = Puzzle.from_rows([[0] * 4 for _ in range(4)])
        rows = [row.copy() for row in SOLUTION_ROWS]
        rows[1] = rows[0].copy()  # Each row still has 1..4.
        self.assertFalse(validate_solution(blank, rows))

    def test_rejects_box_violation(self) -> None:
        blank = Puzzle.from_rows([[0] * 4 for _ in range(4)])
        latin_square = [
            [1, 2, 3, 4],
            [2, 3, 4, 1],
            [3, 4, 1, 2],
            [4, 1, 2, 3],
        ]
        self.assertFalse(validate_solution(blank, latin_square))

    def test_rejects_wrong_shape(self) -> None:
        self.assertFalse(validate_solution(self.puzzle, SOLUTION_ROWS[:-1]))
        self.assertFalse(validate_solution(self.puzzle, [row[:-1] for row in SOLUTION_ROWS]))


if __name__ == "__main__":
    unittest.main()

"""Check that benchmark rows remain independently verifiable and summarizable."""

import json
import tempfile
import unittest
from pathlib import Path

from sudoku_bench.benchmark import discover_puzzles, run_benchmark


class BenchmarkTests(unittest.TestCase):
    def test_raw_jsonl_and_summary(self) -> None:
        from scripts.summarize import summarize_file

        puzzle = Path(__file__).resolve().parents[1] / "data" / "9x9" / "example.json"
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "raw.jsonl"
            output = Path(directory) / "summary.csv"
            records = run_benchmark([puzzle], raw, methods=["sat-sequential"],
                                    repeats=2, time_limit_s=5)
            lines = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(lines[0]["kind"], "meta")
            self.assertEqual(len(records), 2)
            self.assertEqual(len(lines), 3)
            self.assertTrue(all(row["status"] == "SOLVED" and row["solution_valid"]
                                for row in records))
            summary = summarize_file(raw, output)
            self.assertEqual(summary[0]["solved"], 2)
            self.assertEqual(summary[0]["error"], 0)
            self.assertGreater(summary[0]["median_model_variables"], 0)
            self.assertTrue(output.exists())

    def test_discovers_puzzles_and_rejects_empty_runs(self) -> None:
        root = Path(__file__).resolve().parents[1] / "data" / "9x9"
        self.assertTrue(discover_puzzles(root))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                run_benchmark([], Path(directory) / "raw.jsonl")

    def test_summary_separates_timeout_error_and_unsat(self) -> None:
        from scripts.summarize import summarize_file

        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "mixed.jsonl"
            summary_path = Path(directory) / "summary.csv"
            rows = [
                {"kind": "result", "size": 4, "method": "sat-sequential",
                 "puzzle_path": "one.json", "status": status,
                 "solution_valid": status == "SOLVED", "build_time_s": 1.0,
                 "solve_time_s": 2.0, "total_time_s": 3.0,
                 "model_variables": 10, "model_constraints": 20}
                for status in ("SOLVED", "UNSAT", "TIMEOUT", "ERROR")
            ]
            raw.write_text("\n".join(json.dumps(row) for row in rows) + "\n",
                           encoding="utf-8")
            summary = summarize_file(raw, summary_path)[0]
        self.assertEqual((summary["solved"], summary["unsat"],
                          summary["timeout"], summary["error"]), (1, 1, 1, 1))
        self.assertEqual(summary["solved_rate"], 0.25)
        self.assertEqual(summary["median_solve_s"], 2.0)


if __name__ == "__main__":
    unittest.main()

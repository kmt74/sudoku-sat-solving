"""Summarize raw JSONL attempts without conflating errors and timeouts."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median


FIELDS = ("size", "method", "puzzles", "attempts", "solved", "unsat", "timeout",
          "error", "solved_rate", "median_build_s", "median_solve_s", "median_total_s",
          "median_attempt_wall_s", "median_peak_rss_mib", "max_peak_rss_mib",
          "median_model_variables", "median_model_constraints")


def summarize_file(raw_path: str | Path, output_path: str | Path) -> list[dict]:
    groups: dict[tuple[int, str], list[dict]] = defaultdict(list)
    with Path(raw_path).open(encoding="utf-8") as stream:
        for line in stream:
            entry = json.loads(line)
            if entry.get("kind") == "result":
                groups[(entry["size"], entry["method"])].append(entry)

    summary: list[dict] = []
    for (size, method), rows in sorted(groups.items()):
        solved_rows = [row for row in rows if row["status"] == "SOLVED"
                       and row["solution_valid"]]
        count = len(rows)
        variable_counts = [row["model_variables"] for row in rows
                           if row.get("model_variables") is not None]
        constraint_counts = [row["model_constraints"] for row in rows
                             if row.get("model_constraints") is not None]
        memory_bytes = [row["peak_rss_bytes"] for row in rows
                        if row["status"] != "ERROR" and row.get("peak_rss_bytes") is not None]
        wall_times = [row["attempt_wall_s"] for row in solved_rows
                      if row.get("attempt_wall_s") is not None]
        summary.append({
            "size": size, "method": method,
            "puzzles": len({row["puzzle_path"] for row in rows}),
            "attempts": count, "solved": len(solved_rows),
            "unsat": sum(row["status"] == "UNSAT" for row in rows),
            "timeout": sum(row["status"] == "TIMEOUT" for row in rows),
            "error": sum(row["status"] == "ERROR" for row in rows),
            "solved_rate": len(solved_rows) / count,
            "median_build_s": median(row["build_time_s"] for row in solved_rows)
            if solved_rows else "",
            "median_solve_s": median(row["solve_time_s"] for row in solved_rows)
            if solved_rows else "",
            "median_total_s": median(row["total_time_s"] for row in solved_rows)
            if solved_rows else "",
            "median_attempt_wall_s": median(wall_times) if wall_times else "",
            "median_peak_rss_mib": median(memory_bytes) / 1048576 if memory_bytes else "",
            "max_peak_rss_mib": max(memory_bytes) / 1048576 if memory_bytes else "",
            "median_model_variables": median(variable_counts) if variable_counts else "",
            "median_model_constraints": median(constraint_counts) if constraint_counts else "",
        })

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a Sudoku benchmark JSONL file.")
    parser.add_argument("raw", type=Path, help="Input results/raw/*.jsonl")
    parser.add_argument("--output", type=Path, default=Path("results/summary/summary.csv"))
    args = parser.parse_args()
    rows = summarize_file(args.raw, args.output)
    print(f"Wrote {len(rows)} groups to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI for the eight SAT/CP/MIP configurations."""

import argparse
from datetime import datetime, timezone
from pathlib import Path

from sudoku_bench.benchmark import ALL_METHODS, discover_puzzles, run_benchmark


def _time_limit(value: str) -> float | None:
    if value.lower() == "none":
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use positive seconds or 'none'") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Sudoku exact solvers.")
    parser.add_argument("--data", default="data/9x9", help="Puzzle JSON file or directory")
    parser.add_argument("--methods", nargs="+", choices=ALL_METHODS, default=list(ALL_METHODS))
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--time-limit", type=_time_limit, default=60.0,
                        metavar="SECONDS|none", help="Solve limit; 'none' runs without one")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, default=None, help="Raw JSONL output path")
    parser.add_argument("--measure-memory", action="store_true",
                        help="Run each attempt in a fresh process and sample peak process-tree RSS")
    args = parser.parse_args()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    output = args.output or Path("results/raw") / f"run-{timestamp}.jsonl"

    def report(row: dict) -> None:
        line = (f"{row['puzzle_id']}  {row['method']}  repeat={row['repeat']}  "
                f"{row['status']}  total={row['total_time_s']:.4f}s  "
                f"wall={row['attempt_wall_s']:.4f}s")
        if row["peak_rss_bytes"] is not None:
            line += f"  peak={row['peak_rss_bytes'] / 1048576:.1f}MiB"
        print(line, flush=True)

    try:
        paths = discover_puzzles(args.data)
        run_benchmark(
            paths, output, methods=args.methods, repeats=args.repeats,
            time_limit_s=args.time_limit, seed=args.seed,
            measure_memory=args.measure_memory,
            on_record=report,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Raw results: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

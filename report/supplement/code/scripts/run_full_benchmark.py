"""Run the balanced 90-puzzle benchmark with per-puzzle checkpoints."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sudoku_bench.benchmark import ALL_METHODS, run_benchmark
from summarize import summarize_file


DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def _complete(path: Path, puzzle_id: str, repeats: int,
              time_limit_s: float) -> bool:
    if not path.is_file():
        return False
    try:
        with path.open(encoding="utf-8") as stream:
            entries = [json.loads(line) for line in stream]
        meta, *rows = entries
        expected = {(method, repeat) for method in ALL_METHODS
                    for repeat in range(1, repeats + 1)}
        actual = {(row["method"], row["repeat"]) for row in rows}
        return (meta["kind"] == "meta"
                and meta["time_limit_s"] == time_limit_s
                and meta["measurement_mode"] == "isolated-process-tree"
                and meta["repeats"] == repeats
                and len(rows) == len(expected) and actual == expected
                and all(row["kind"] == "result" and row["puzzle_id"] == puzzle_id
                        for row in rows))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def _write_progress(path: Path, completed: int, total: int,
                    current: str | None, repeats: int) -> None:
    payload = {"completed_puzzles": completed, "total_puzzles": total,
               "completed_attempts": completed * len(ALL_METHODS) * repeats,
               "current_puzzle": current,
               "updated_at_utc": datetime.now(timezone.utc).isoformat()}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=Path("results/runs/full-60s"))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--time-limit", type=float, default=60.0)
    args = parser.parse_args()
    if args.repeats < 1 or args.time_limit <= 0:
        parser.error("repeats and time limit must be positive")

    dataset = Path("data/benchmark")
    with (dataset / "manifest.csv").open(newline="", encoding="utf-8") as stream:
        puzzles = list(csv.DictReader(stream))
    puzzles.sort(key=lambda row: (int(row["size"]), DIFFICULTY_ORDER[row["difficulty"]],
                                  row["id"]))
    if len(puzzles) != 90:
        parser.error(f"expected 90 puzzles, found {len(puzzles)}")

    run_dir = args.run_dir
    shards = run_dir / "puzzles"
    shards.mkdir(parents=True, exist_ok=True)
    completed = 0
    progress_path = run_dir / "progress.json"
    for index, row in enumerate(puzzles):
        puzzle_path = dataset / row["output_path"]
        shard_path = shards / f"{row['id']}.jsonl"
        if _complete(shard_path, row["id"], args.repeats, args.time_limit):
            completed += 1
            _write_progress(progress_path, completed, len(puzzles), row["id"], args.repeats)
            print(f"[{completed}/{len(puzzles)}] kept {row['id']}", flush=True)
            continue
        _write_progress(progress_path, completed, len(puzzles), row["id"], args.repeats)
        print(f"[{completed + 1}/{len(puzzles)}] starting {row['id']}", flush=True)
        run_benchmark([puzzle_path], shard_path, repeats=args.repeats,
                      time_limit_s=args.time_limit, seed=index,
                      measure_memory=True,
                      on_record=lambda result: print(
                          f"  {result['method']} repeat={result['repeat']} "
                          f"{result['status']} wall={result['attempt_wall_s']:.2f}s",
                          flush=True))
        if not _complete(shard_path, row["id"], args.repeats, args.time_limit):
            raise RuntimeError(f"incomplete puzzle result: {shard_path}")
        completed += 1
        _write_progress(progress_path, completed, len(puzzles), None, args.repeats)
        print(f"[{completed}/{len(puzzles)}] finished {row['id']}", flush=True)

    combined = run_dir / "all-results.jsonl"
    temporary = run_dir / "all-results.jsonl.tmp"
    with temporary.open("w", encoding="utf-8") as output:
        for index, row in enumerate(puzzles):
            shard = shards / f"{row['id']}.jsonl"
            with shard.open(encoding="utf-8") as stream:
                meta = json.loads(next(stream))
                if index == 0:
                    meta["puzzles"] = [str(dataset / item["output_path"]) for item in puzzles]
                    meta["seed_scheme"] = "manifest-order index per puzzle"
                    meta["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
                    output.write(json.dumps(meta, ensure_ascii=False) + "\n")
                for line in stream:
                    output.write(line)
    os.replace(temporary, combined)
    summary = run_dir / "summary.csv"
    summarize_file(combined, summary)
    stratified = run_dir / "summary-by-difficulty.csv"
    summarize_file(combined, stratified, by_difficulty=True)
    print(f"Completed {completed} puzzles. Raw: {combined}; summaries: {summary}, {stratified}",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

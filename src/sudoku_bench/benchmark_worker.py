"""Execute one solver attempt in an isolated process for memory sampling."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("puzzle", type=Path)
    parser.add_argument("method")
    parser.add_argument("time_limit_s", type=float)
    parser.add_argument("result_path", type=Path)
    args = parser.parse_args()

    # The parent starts sampling before releasing the worker. Import costs and
    # short lived solver processes are therefore included in the memory trace.
    if sys.stdin.readline() != "start\n":
        return 2

    from sudoku_bench.benchmark import run_method
    from sudoku_bench.puzzle import load_puzzle
    from sudoku_bench.solvers.base import SolveResult, SolveStatus

    try:
        result = run_method(load_puzzle(args.puzzle), args.method, args.time_limit_s)
    except Exception as exc:
        result = SolveResult(SolveStatus.ERROR, message=f"{type(exc).__name__}: {exc}")
    payload = {
        "status": result.status.value,
        "solution": result.solution,
        "build_time_s": result.build_time_s,
        "solve_time_s": result.solve_time_s,
        "message": result.message,
        "model_variables": result.model_variables,
        "model_constraints": result.model_constraints,
    }
    args.result_path.write_text(json.dumps(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

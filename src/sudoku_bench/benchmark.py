"""Run each exact method on identical puzzles and save reproducible raw results."""

from __future__ import annotations

import json
import math
import os
import platform
import random
import sys
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from sudoku_bench.puzzle import Puzzle, load_puzzle
from sudoku_bench.solvers.base import SolveResult, SolveStatus
from sudoku_bench.solvers.cplex_cp import solve_cplex_cp
from sudoku_bench.solvers.cplex_mip import solve_cplex_mip
from sudoku_bench.solvers.gurobi_mip import solve_gurobi_mip
from sudoku_bench.solvers.ortools_cp_sat import solve_cp_sat
from sudoku_bench.solvers.pysat_solver import solve_sat
from sudoku_bench.validator import validate_solution


SAT_ENCODINGS = ("binary", "commander", "product", "sequential")
ALL_METHODS = tuple(f"sat-{encoding}" for encoding in SAT_ENCODINGS) + (
    "cp-optimizer", "cplex-mip", "gurobi-mip", "cp-sat",
)


def run_method(puzzle: Puzzle, method: str, time_limit_s: float) -> SolveResult:
    if method.startswith("sat-") and method[4:] in SAT_ENCODINGS:
        return solve_sat(puzzle, encoding=method[4:], time_limit_s=time_limit_s)
    implementations = {
        "cp-optimizer": solve_cplex_cp,
        "cplex-mip": solve_cplex_mip,
        "gurobi-mip": solve_gurobi_mip,
        "cp-sat": solve_cp_sat,
    }
    if method not in implementations:
        raise ValueError(f"unknown method: {method}")
    return implementations[method](puzzle, time_limit_s=time_limit_s)


def discover_puzzles(path: str | Path) -> list[Path]:
    source = Path(path)
    if source.is_file():
        return [source]
    if not source.is_dir():
        raise FileNotFoundError(f"puzzle path does not exist: {source}")
    puzzles = sorted(source.rglob("*.json"))
    if not puzzles:
        raise ValueError(f"no JSON puzzles found in {source}")
    return puzzles


def _package_versions() -> dict[str, str | None]:
    packages = ("python-sat", "ortools", "docplex", "cplex", "gurobipy")
    found: dict[str, str | None] = {}
    for package in packages:
        try:
            found[package] = version(package)
        except PackageNotFoundError:
            found[package] = None
    return found


def run_benchmark(puzzle_paths: Sequence[str | Path], output_path: str | Path,
                  methods: Sequence[str] = ALL_METHODS, repeats: int = 1,
                  time_limit_s: float = 30.0, seed: int = 0,
                  on_record: Callable[[dict], None] | None = None) -> list[dict]:
    """Write JSON Lines, with one metadata header and one row per solver attempt."""
    if repeats < 1 or not math.isfinite(time_limit_s) or time_limit_s <= 0:
        raise ValueError("repeats and time_limit_s must be positive")
    if not methods or any(method not in ALL_METHODS for method in methods):
        raise ValueError("methods must be nonempty and selected from ALL_METHODS")
    if len(set(methods)) != len(methods):
        raise ValueError("methods must not contain duplicates")

    puzzles = [(Path(path), load_puzzle(path)) for path in puzzle_paths]
    if not puzzles:
        raise ValueError("at least one puzzle is required")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    started_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "kind": "meta", "started_at_utc": started_at,
        "python": sys.version.split()[0], "platform": platform.platform(),
        "logical_cpus": os.cpu_count(),
        "packages": _package_versions(), "methods": list(methods),
        "repeats": repeats, "time_limit_s": time_limit_s, "seed": seed,
        "puzzles": [str(path) for path, _ in puzzles],
    }
    records: list[dict] = []
    with destination.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(metadata, ensure_ascii=False) + "\n")
        for path, puzzle in puzzles:
            for repetition in range(1, repeats + 1):
                order = list(methods)
                rng.shuffle(order)
                for method in order:
                    try:
                        result = run_method(puzzle, method, time_limit_s)
                    except Exception as exc:
                        result = SolveResult(SolveStatus.ERROR,
                                             message=f"{type(exc).__name__}: {exc}")
                    valid = result.solution is not None and validate_solution(puzzle, result.solution)
                    if result.status is SolveStatus.SOLVED and not valid:
                        result = SolveResult(SolveStatus.ERROR,
                                             build_time_s=result.build_time_s,
                                             solve_time_s=result.solve_time_s,
                                             message="independent solution validation failed",
                                             model_variables=result.model_variables,
                                             model_constraints=result.model_constraints)
                    record = {
                        "kind": "result", "puzzle_id": puzzle.puzzle_id or path.stem,
                        "puzzle_path": str(path), "size": puzzle.size,
                        "clues": puzzle.clue_count, "source": puzzle.source,
                        "difficulty": puzzle.difficulty, "dataset_kind": puzzle.kind,
                        "method": method,
                        "encoding": method[4:] if method.startswith("sat-") else None,
                        "repeat": repetition, "status": result.status.value,
                        "build_time_s": result.build_time_s,
                        "solve_time_s": result.solve_time_s,
                        "total_time_s": result.total_time_s,
                        "model_variables": result.model_variables,
                        "model_constraints": result.model_constraints,
                        "solution_valid": valid, "solution": result.solution,
                        "message": result.message,
                    }
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                    stream.flush()
                    records.append(record)
                    if on_record is not None:
                        on_record(record)
    return records

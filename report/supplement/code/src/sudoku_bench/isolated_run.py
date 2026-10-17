"""Measure a solver in a fresh process, including its child solver processes."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import psutil

from sudoku_bench.solvers.base import SolveResult, SolveStatus


SAMPLE_INTERVAL_S = 0.01


def _process_tree_rss(process: psutil.Process) -> tuple[int, int]:
    """Return total and child RSS at one instant, tolerating process exit races."""
    try:
        members = [process, *process.children(recursive=True)]
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        members = [process]
    total = 0
    child_total = 0
    for index, member in enumerate(members):
        try:
            rss = member.memory_info().rss
            total += rss
            if index:
                child_total += rss
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return total, child_total


def _decode_result(path: Path) -> SolveResult:
    data = json.loads(path.read_text(encoding="utf-8"))
    solution = data["solution"]
    if solution is not None:
        solution = tuple(tuple(row) for row in solution)
    return SolveResult(
        status=SolveStatus(data["status"]), solution=solution,
        build_time_s=data["build_time_s"], solve_time_s=data["solve_time_s"],
        message=data["message"], model_variables=data["model_variables"],
        model_constraints=data["model_constraints"],
    )


def run_isolated(puzzle_path: str | Path, method: str,
                 time_limit_s: float | None) -> tuple[SolveResult, int | None, int, int]:
    """Return result, peak tree RSS, sample count and peak child RSS."""
    with tempfile.TemporaryDirectory(prefix="sudoku-bench-") as directory:
        result_path = Path(directory) / "result.json"
        command = [sys.executable, "-m", "sudoku_bench.benchmark_worker",
                   str(Path(puzzle_path).resolve()), method,
                   "none" if time_limit_s is None else str(time_limit_s), str(result_path)]
        peak = 0
        child_peak = 0
        samples = 0
        stop = threading.Event()
        first_sample = threading.Event()
        try:
            with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True) as worker:
                process = psutil.Process(worker.pid)

                def sample() -> None:
                    nonlocal peak, child_peak, samples
                    while True:
                        rss, child_rss = _process_tree_rss(process)
                        peak = max(peak, rss)
                        child_peak = max(child_peak, child_rss)
                        samples += 1
                        first_sample.set()
                        if stop.wait(SAMPLE_INTERVAL_S):
                            break

                monitor = threading.Thread(target=sample, daemon=True)
                monitor.start()
                try:
                    first_sample.wait(timeout=1)
                    _stdout, stderr = worker.communicate(input="start\n")
                finally:
                    stop.set()
                    monitor.join()
                if worker.returncode != 0 or not result_path.exists():
                    detail = stderr.strip()[-500:] or f"worker exited with code {worker.returncode}"
                    return SolveResult(SolveStatus.ERROR, message=detail), peak or None, samples, child_peak
        except OSError as exc:
            return SolveResult(SolveStatus.ERROR,
                               message=f"{type(exc).__name__}: {exc}"), peak or None, samples, child_peak
        try:
            result = _decode_result(result_path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result = SolveResult(SolveStatus.ERROR,
                                 message=f"invalid worker result: {type(exc).__name__}: {exc}")
        return result, peak or None, samples, child_peak

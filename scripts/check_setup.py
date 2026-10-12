"""Display installed solver support and run a quick 4x4 adapter smoke check."""

import os
import shutil
from importlib.metadata import PackageNotFoundError, version

from sudoku_bench.benchmark import ALL_METHODS, run_method
from sudoku_bench.puzzle import Puzzle


def main() -> int:
    print("Python packages:")
    for package in ("python-sat", "ortools", "docplex", "cplex", "gurobipy"):
        try:
            installed = version(package)
        except PackageNotFoundError:
            installed = "missing"
        print(f"  {package}: {installed}")
    executable = os.getenv("CP_OPTIMIZER_EXECUTABLE") or shutil.which("cpoptimizer")
    print(f"CP Optimizer executable: {executable or 'missing'}")

    puzzle = Puzzle.from_rows([
        [1, 0, 0, 4], [0, 4, 1, 0], [0, 1, 4, 0], [4, 0, 0, 1],
    ])
    print("4x4 smoke check:")
    for method in ALL_METHODS:
        result = run_method(puzzle, method, time_limit_s=5)
        detail = f" - {result.message}" if result.message else ""
        print(f"  {method}: {result.status.value}{detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

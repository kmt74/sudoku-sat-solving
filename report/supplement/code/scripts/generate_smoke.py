"""Generate reproducible, solvable Sudoku instances for pipeline smoke tests.

These near-complete instances are not a calibrated difficulty benchmark.
"""

import argparse
import json
import random
from math import isqrt
from pathlib import Path

from sudoku_bench.puzzle import Puzzle


def make_smoke_grid(size: int, blanks_per_row: int, seed: int) -> list[list[int]]:
    box = isqrt(size)
    if size < 4 or box * box != size:
        raise ValueError("size must be a perfect square of at least 4")
    if not 0 <= blanks_per_row < size:
        raise ValueError("blanks_per_row must be between 0 and size-1")

    rng = random.Random(seed)

    def permuted_units() -> list[int]:
        bands = list(range(box))
        rng.shuffle(bands)
        units = []
        for band in bands:
            within = list(range(box))
            rng.shuffle(within)
            units.extend(band * box + offset for offset in within)
        return units

    rows = permuted_units()
    columns = permuted_units()
    digits = list(range(1, size + 1))
    rng.shuffle(digits)
    grid = [[digits[(box * (row % box) + row // box + column) % size]
             for column in columns] for row in rows]
    for row in grid:
        for column in rng.sample(range(size), blanks_per_row):
            row[column] = 0
    Puzzle.from_rows(grid)  # Verify the generated clues before writing.
    return grid


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate solvable Sudoku smoke instances.")
    parser.add_argument("--sizes", nargs="+", type=int, default=[16, 25])
    parser.add_argument("--blanks-per-row", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    for size in args.sizes:
        try:
            grid = make_smoke_grid(size, args.blanks_per_row, args.seed)
        except ValueError as exc:
            parser.error(str(exc))
        destination = args.output_dir / f"{size}x{size}" / f"smoke-seed{args.seed}.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({
            "id": f"smoke-{size}x{size}-seed{args.seed}",
            "kind": "smoke", "source": "scripts/generate_smoke.py",
            "seed": args.seed, "blanks_per_row": args.blanks_per_row,
            "grid": grid,
        }, indent=2) + "\n", encoding="utf-8")
        print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

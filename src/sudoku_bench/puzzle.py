"""Sudoku input model and JSON loading.

A grid has N rows and N columns, where N is a perfect square. Zero denotes
an empty cell; filled cells contain integers from 1 through N.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import isqrt
from pathlib import Path
from typing import Iterable


Grid = tuple[tuple[int, ...], ...]


def _as_grid(rows: Iterable[Iterable[int]]) -> Grid:
    try:
        return tuple(tuple(row) for row in rows)
    except (TypeError, ValueError) as exc:
        raise ValueError("grid must be a sequence of rows") from exc


def _no_duplicate_clues(values: Iterable[int]) -> bool:
    clues = [value for value in values if value != 0]
    return len(clues) == len(set(clues))


@dataclass(frozen=True, slots=True)
class Puzzle:
    grid: Grid
    puzzle_id: str = ""

    def __post_init__(self) -> None:
        grid = _as_grid(self.grid)
        object.__setattr__(self, "grid", grid)

        if not isinstance(self.puzzle_id, str):
            raise ValueError("puzzle_id must be a string")

        size = len(grid)
        box_size = isqrt(size)
        if size == 0 or box_size * box_size != size:
            raise ValueError("board size must be a nonzero perfect square")
        if any(len(row) != size for row in grid):
            raise ValueError("grid must have N rows of N cells")
        if any(type(value) is not int or not 0 <= value <= size for row in grid for value in row):
            raise ValueError("cells must be integers from 0 to N")

        for row in grid:
            if not _no_duplicate_clues(row):
                raise ValueError("conflicting clues in a row")
        for column in range(size):
            if not _no_duplicate_clues(grid[row][column] for row in range(size)):
                raise ValueError("conflicting clues in a column")
        for top in range(0, size, box_size):
            for left in range(0, size, box_size):
                block = (
                    grid[row][column]
                    for row in range(top, top + box_size)
                    for column in range(left, left + box_size)
                )
                if not _no_duplicate_clues(block):
                    raise ValueError("conflicting clues in a box")

    @property
    def size(self) -> int:
        return len(self.grid)

    @property
    def box_size(self) -> int:
        return isqrt(self.size)

    @property
    def clue_count(self) -> int:
        return sum(value != 0 for row in self.grid for value in row)

    @classmethod
    def from_rows(cls, rows: Iterable[Iterable[int]], puzzle_id: str = "") -> Puzzle:
        return cls(_as_grid(rows), puzzle_id=puzzle_id)


def load_puzzle(path: str | Path) -> Puzzle:
    """Load ``{"id": "...", "grid": [[...], ...]}`` from a JSON file."""
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "grid" not in data:
        raise ValueError("puzzle JSON must be an object with a grid field")
    return Puzzle.from_rows(data["grid"], puzzle_id=data.get("id", source.stem))

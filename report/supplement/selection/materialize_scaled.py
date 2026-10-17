"""Convert the selected scaled Sudoku instances to the benchmark JSON schema."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


WORK = Path(__file__).parent
SOURCE = WORK / "scaled-sudoku-corpus"
REPO = Path("D:/Workspace/sudoku-sat-solving")
DESTINATION = REPO / "data" / "benchmark"
sys.path.insert(0, str(REPO / "src"))

from sudoku_bench.puzzle import Puzzle, load_puzzle  # noqa: E402
from sudoku_bench.validator import validate_solution  # noqa: E402


SYMBOLS = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOOKUP = {character: value for value, character in enumerate(SYMBOLS, 1)}


def parse_grid(text: str, size: int) -> list[list[int]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    expected_box = int(size ** 0.5)
    if lines[0] != f"# size={size} box={expected_box}x{expected_box}":
        raise ValueError(f"unexpected puzzle header: {lines[0]}")
    rows = lines[1:]
    if len(rows) != size or any(len(row) != size for row in rows):
        raise ValueError("incorrect source puzzle dimensions")
    grid = [[0 if value == "." else LOOKUP[value] for value in row] for row in rows]
    if any(value > size for row in grid for value in row):
        raise ValueError("symbol exceeds grid size")
    return grid


def main() -> None:
    plan = json.loads((WORK / "scaled-selection.json").read_text(encoding="utf-8"))
    commit = plan["source_commit"]
    selected = plan["selection"]
    counts: Counter[tuple[int, str]] = Counter()
    seen_grids: set[str] = set()
    seen_roots: set[str] = set()
    rows: list[dict[str, str | int]] = []

    for item in selected:
        size, tier, label = item["size"], item["tier"], item["hardness_level"]
        sidecar = json.loads((SOURCE / item["sidecar_path"]).read_text(encoding="utf-8"))
        source_text = (SOURCE / item["puzzle_path"]).read_text(encoding="utf-8")
        grid = parse_grid(source_text, size)
        if sidecar["size"]["order"] != size or sidecar["hardness"]["level"] != label:
            raise ValueError(f"source metadata mismatch: {item['sidecar_path']}")
        if sidecar["identity"]["source_path"] != item["puzzle_path"]:
            raise ValueError(f"source path mismatch: {item['puzzle_path']}")
        if sum(value != 0 for row in grid for value in row) != sidecar["clues_count"]:
            raise ValueError(f"source clue count mismatch: {item['puzzle_path']}")
        if item["root_id"] in seen_roots:
            raise ValueError(f"source root reused: {item['root_id']}")
        seen_roots.add(item["root_id"])

        grid_hash = hashlib.sha256(json.dumps(grid).encode("utf-8")).hexdigest()
        if grid_hash in seen_grids:
            raise ValueError(f"duplicate puzzle grid: {item['puzzle_path']}")
        seen_grids.add(grid_hash)

        solution_flat = sidecar["solution_grid"]
        if len(solution_flat) != size * size:
            raise ValueError(f"incorrect source solution dimensions: {item['puzzle_path']}")
        solution = [solution_flat[offset:offset + size]
                    for offset in range(0, size * size, size)]
        source_puzzle = Puzzle.from_rows(grid)
        if not validate_solution(source_puzzle, solution):
            raise ValueError(f"source solution failed validation: {item['puzzle_path']}")

        counts[(size, tier)] += 1
        number = counts[(size, tier)]
        puzzle_id = f"scaled-{size}x{size}-{tier}-{number:02d}"
        relative_output = Path(f"{size}x{size}") / tier / f"{puzzle_id}.json"
        output = DESTINATION / relative_output
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "id": puzzle_id,
            "kind": "benchmark",
            "source": f"zayenz/scaled-sudoku-instances@{commit}",
            "source_id": sidecar["identity"]["source_id"],
            "source_path": item["puzzle_path"],
            "source_root": item["root_id"],
            "difficulty": tier,
            "hardness_level": label,
            "grid": grid,
        }
        metadata_lines = json.dumps({key: value for key, value in payload.items()
                                     if key != "grid"}, indent=2, ensure_ascii=False).splitlines()
        compact_grid = ["  \"grid\": ["]
        compact_grid.extend(
            f"    {json.dumps(row)}{',' if index < size - 1 else ''}"
            for index, row in enumerate(grid)
        )
        compact_grid.append("  ]")
        rendered = "\n".join(metadata_lines[:-1]) + ",\n" + "\n".join(compact_grid) + "\n}\n"
        output.write_text(rendered, encoding="utf-8")
        loaded = load_puzzle(output)
        if loaded.hardness_level != label or not validate_solution(loaded, solution):
            raise ValueError(f"imported puzzle failed validation: {output}")
        rows.append({
            "id": puzzle_id, "size": size, "difficulty": tier,
            "hardness_level": label, "clues": sidecar["clues_count"],
            "source_id": sidecar["identity"]["source_id"],
            "source_root": item["root_id"], "source_path": item["puzzle_path"],
            "source_commit": commit,
            "source_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
            "output_path": relative_output.as_posix(),
        })

    if len(rows) != 90 or len(counts) != 9 or any(count != 10 for count in counts.values()):
        raise ValueError(f"unexpected sample counts: {counts}")
    manifest = DESTINATION / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} validated puzzles and {manifest}")
    print("Labels:", dict(sorted(Counter(row["hardness_level"] for row in rows).items())))


if __name__ == "__main__":
    main()

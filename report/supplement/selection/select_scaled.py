"""Select a reproducible, label-diverse Sudoku benchmark sample."""

from __future__ import annotations

import json
import random
import subprocess
from collections import defaultdict
from pathlib import Path


SOURCE = Path(__file__).parent / "scaled-sudoku-corpus"
SEED = 20261015
QUOTAS = {
    9: {
        "hard": {"Dom": 2, "DomBS": 8},
        "medium": {"Bnd": 1, "BndBS": 6, "BndDS": 3},
        "easy": {"Val": 2, "ValBS": 4, "ValDS": 2, "ValChan": 2},
    },
    16: {
        "hard": {"DomBS": 4, "DomDS": 3, "UNSOLVED": 3},
        "medium": {"Bnd": 1, "BndBS": 4, "BndDS": 3, "BndChan": 2},
        "easy": {"Val": 2, "ValBS": 4, "ValDS": 2, "ValChan": 2},
    },
    25: {
        "hard": {"UNSOLVED": 3, "Dom": 4, "DomBS": 3},
        "medium": {"BndBS": 4, "BndDS": 3, "BndChan": 3},
        "easy": {"Val": 2, "ValBS": 4, "ValDS": 2, "ValChan": 2},
    },
}


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=SOURCE, text=True).strip()


def root_id(path: str) -> str:
    parts = path.split("/")
    if parts[0] == "base":
        return "/".join(parts[1:3] + [parts[3].removesuffix(".sdk.json")])
    return "/".join(parts[2:5])


def base_candidates(size: int, label: str) -> dict[str, list[str]]:
    pattern = f'"level": "{label}"'
    paths = run("rg", "-l", "-F", pattern, f"base/{size}x{size}", "-g", "*.sdk.json")
    grouped: dict[str, list[str]] = defaultdict(list)
    for path in paths.splitlines():
        path = path.replace("\\", "/")
        grouped[root_id(path)].append(path)
    return grouped


def variant_candidates(size: int) -> dict[str, dict[str, list[str]]]:
    paths = run("git", "ls-tree", "-r", "--name-only", "HEAD",
                f"walks/variants/{size}x{size}")
    grouped: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for path in paths.splitlines():
        if path.endswith(".sdk.json"):
            label = Path(path).name.removesuffix(".sdk.json").split("-")[-1]
            grouped[label][root_id(path)].append(path)
    return grouped


def main() -> None:
    rng = random.Random(SEED)
    selected: list[dict] = []
    source_commit = run("git", "rev-parse", "HEAD")
    for size, tiers in QUOTAS.items():
        variants = variant_candidates(size)
        used_roots: set[str] = set()
        for tier, labels in tiers.items():
            for label, count in labels.items():
                use_base = size == 9 or (size == 16 and tier == "hard") or label == "UNSOLVED"
                candidates = base_candidates(size, label) if use_base else variants[label]
                roots = sorted(set(candidates) - used_roots)
                if len(roots) < count:
                    raise RuntimeError(f"too few independent {size}x{size} {label} roots: "
                                       f"need {count}, found {len(roots)}")
                for root in rng.sample(roots, count):
                    sidecar = rng.choice(sorted(candidates[root]))
                    used_roots.add(root)
                    selected.append({
                        "size": size, "tier": tier, "hardness_level": label,
                        "root_id": root, "sidecar_path": sidecar,
                        "puzzle_path": sidecar.removesuffix(".sdk.json") + ".sdk.txt",
                    })
    payload = {"source_commit": source_commit, "seed": SEED, "quotas": QUOTAS,
               "selection": selected}
    (Path(__file__).parent / "scaled-selection.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    paths = sorted({path for row in selected for path in
                    (row["sidecar_path"], row["puzzle_path"])})
    (Path(__file__).parent / "scaled-selected-paths.txt").write_text(
        "\n".join(paths) + "\n", encoding="utf-8")
    print(f"Selected {len(selected)} puzzles from {len(set(row['root_id'] for row in selected))} "
          f"independent roots at {source_commit}")


if __name__ == "__main__":
    main()

"""Recursive commander at-most-one encoding with groups of three."""

from collections.abc import Callable, Sequence
from itertools import combinations


def at_most_one(literals: Sequence[int], new_var: Callable[[], int]) -> list[tuple[int, ...]]:
    """Use a commander for each group, then constrain commanders recursively."""
    if len(literals) < 2:
        return []
    if len(literals) <= 3:
        return [(-left, -right) for left, right in combinations(literals, 2)]

    clauses: list[tuple[int, ...]] = []
    commanders: list[int] = []
    for start in range(0, len(literals), 3):
        group = literals[start:start + 3]
        commander = new_var()
        commanders.append(commander)
        clauses.extend((-left, -right) for left, right in combinations(group, 2))
        clauses.extend((-literal, commander) for literal in group)
    clauses.extend(at_most_one(commanders, new_var))
    return clauses

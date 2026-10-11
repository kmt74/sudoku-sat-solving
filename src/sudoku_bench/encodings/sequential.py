"""Sinz sequential-counter encoding for an at-most-one constraint."""

from collections.abc import Callable, Sequence


def at_most_one(literals: Sequence[int], new_var: Callable[[], int]) -> list[tuple[int, ...]]:
    """Encode that no more than one input literal is true.

    ``new_var`` must return fresh positive IDs, disjoint from all input IDs.
    For n inputs this uses n-1 auxiliary variables and 3n-4 clauses (n >= 2).
    """
    count = len(literals)
    if count < 2:
        return []

    auxiliaries = [new_var() for _ in range(count - 1)]
    clauses: list[tuple[int, ...]] = [(-literals[0], auxiliaries[0])]

    for index in range(1, count - 1):
        clauses.extend(
            (
                (-literals[index], auxiliaries[index]),
                (-auxiliaries[index - 1], auxiliaries[index]),
                (-literals[index], -auxiliaries[index - 1]),
            )
        )

    clauses.append((-literals[-1], -auxiliaries[-1]))
    return clauses

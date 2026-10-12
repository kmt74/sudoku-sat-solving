"""Binary/bitwise at-most-one encoding."""

from collections.abc import Callable, Sequence


def at_most_one(literals: Sequence[int], new_var: Callable[[], int]) -> list[tuple[int, ...]]:
    """Assign each input a unique binary code using ceil(log2(n)) auxiliaries."""
    if len(literals) < 2:
        return []
    bits = [new_var() for _ in range((len(literals) - 1).bit_length())]
    return [
        (-literal, bit if index & (1 << position) else -bit)
        for index, literal in enumerate(literals)
        for position, bit in enumerate(bits)
    ]

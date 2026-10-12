"""Two-dimensional product at-most-one encoding."""

from collections.abc import Callable, Sequence
from itertools import combinations
from math import isqrt


def at_most_one(literals: Sequence[int], new_var: Callable[[], int]) -> list[tuple[int, ...]]:
    """Map each input to one row and column selector; constrain both axes."""
    count = len(literals)
    if count < 2:
        return []
    rows = isqrt(count - 1) + 1
    columns = (count + rows - 1) // rows
    row_vars = [new_var() for _ in range(rows)]
    column_vars = [new_var() for _ in range(columns)]
    clauses = [
        clause
        for index, literal in enumerate(literals)
        for clause in ((-literal, row_vars[index // columns]),
                       (-literal, column_vars[index % columns]))
    ]
    clauses.extend((-left, -right) for left, right in combinations(row_vars, 2))
    clauses.extend((-left, -right) for left, right in combinations(column_vars, 2))
    return clauses

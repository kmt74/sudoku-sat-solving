"""At-most-one CNF encodings sharing one callable interface."""

from collections.abc import Callable, Sequence

from . import binary, commander, product, sequential

Encoding = Callable[[Sequence[int], Callable[[], int]], list[tuple[int, ...]]]
ENCODINGS: dict[str, Encoding] = {
    "binary": binary.at_most_one,
    "commander": commander.at_most_one,
    "product": product.at_most_one,
    "sequential": sequential.at_most_one,
}

from dataclasses import dataclass

from .errors import InvalidQuantity

MAX_BOXES_PER_LINE = 25


@dataclass(frozen=True, slots=True)
class BoxQuantity:
    """
    Value object representing number of boxes ordered for one product line.

    DOMAIN MEANING:
    - The value is counted in boxes, not individual consumer units
    - Must be a positive integer
    - Must not exceed the current per-line sanity limit

    WHY THE MAX LIMIT EXISTS:
    The current ordering UI is intended for normal store ordering.
    Extremely large per-line values are more likely to be mistakes than
    valid orders, so the value object protects the system invariant.
    """

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise InvalidQuantity("Number of boxes must be an integer.")
        if self.value <= 0:
            raise InvalidQuantity("Number of boxes must be greater than zero.")
        if self.value > MAX_BOXES_PER_LINE:
            raise InvalidQuantity(
                f"Number of boxes cannot exceed {MAX_BOXES_PER_LINE}."
            )

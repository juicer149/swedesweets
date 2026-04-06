from dataclasses import dataclass

from .errors import InvalidQuantity


@dataclass(frozen=True, slots=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise InvalidQuantity("Quantity must be an integer.")
        if self.value <= 0:
            raise InvalidQuantity("Quantity must be greater than zero.")

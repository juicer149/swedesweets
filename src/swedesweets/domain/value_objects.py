#! src/swedesweets/domain/value_objects.py
"""
Value objects.

Purpose:
- Encapsulate primitive values with validation
- Make invalid states unrepresentable
- Improve readability and correctness

Design:
- Immutable (frozen=True)
- Validated at construction time
- No business rules here, only intrinsic constraints
"""

from dataclasses import dataclass

from .errors import ValidationError


@dataclass(frozen=True)
class ProductCode:
    """User-facing product identifier.

    Example: "42"
    Used in UI and communication instead of UUID.
    """

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise ValidationError("product code must be int")

        if self.value <= 0:
            raise ValidationError("product code must be > 0")

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Quantity:
    """Represents a strictly positive quantity.

    Design:
    - Zero is not allowed
    - Removal should be handled outside with explicit behavior
    """

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise ValidationError("quantity must be int")

        if self.value <= 0:
            raise ValidationError("quantity must be > 0")

    def add(self, other: "Quantity") -> "Quantity":
        return Quantity(self.value + other.value)

    def subtract(self, other: "Quantity") -> "Quantity":
        """Return a new Quantity after subtraction.

        Note:
        - Cannot result in zero or negative
        - Removal should be handled outside this value object
        """
        result = self.value - other.value
        if result <= 0:
            raise ValidationError("quantity cannot be <= 0")
        return Quantity(result)

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

#! src/swedesweets/domain/product.py
"""Product entity.

Represents a product in the catalog.

Design decisions:
- UUID is internal identity
- ProductCode is user-facing identifier
- Name is validated but simple for MVP

Out of scope:
- pricing
- categories
- inventory
"""

from dataclasses import dataclass
from uuid import UUID

from ._validation import require_max_length, require_non_empty_str, require_uuid
from .value_objects import ProductCode


@dataclass(frozen=True)
class Product:
    """A product that can be ordered."""

    id: UUID
    code: ProductCode
    name: str

    def __post_init__(self) -> None:
        require_uuid(self.id, field="product.id")
        require_non_empty_str(self.name, field="product.name")
        require_max_length(self.name, field="product.name", max_length=255)

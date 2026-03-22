from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .errors import ValidationError


@dataclass(frozen=True)
class OrderItem:
    product_id: UUID
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValidationError("quantity must be > 0")


@dataclass(frozen=True)
class Order:
    id: UUID
    store_id: UUID
    created_at: datetime
    items: tuple[OrderItem, ...]

    def __post_init__(self):
        if not self.items:
            raise ValidationError("order must have items")

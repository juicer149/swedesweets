#! src/swedesweets/domain/order.py
"""
Order entities.

Represents finalized orders.

Design:
- Immutable snapshot of what was ordered
- No editing or lifecycle in MVP
- Safe for persistence, history, and caching

Important distinction:
- OrderDraft = editable intent
- Order = finalized fact
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ._validation import require_uuid
from .errors import ValidationError
from .value_objects import Quantity


@dataclass(frozen=True)
class OrderItem:
    """A single product and quantity in an order."""

    product_id: UUID
    quantity: Quantity

    def __post_init__(self) -> None:
        require_uuid(self.product_id, field="order_item.product_id")


@dataclass(frozen=True)
class Order:
    """Finalized order.

    Invariants:
    - Must contain at least one item
    - Timestamp must be timezone-aware

    Why immutable:
    - Prevent accidental modification
    - Safe to treat as historical record
    """

    id: UUID
    store_id: UUID
    created_at: datetime
    items: tuple[OrderItem, ...]

    def __post_init__(self) -> None:
        require_uuid(self.id, field="order.id")
        require_uuid(self.store_id, field="order.store_id")

        if not self.items:
            raise ValidationError("order must have items")

        if self.created_at.tzinfo is None:
            raise ValidationError("created_at must be timezone-aware")

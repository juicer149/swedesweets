#! src/swedesweets/domain/draft.py
"""
OrderDraft entity.

Represents an editable order before submission.

Key concept:
- Draft = intent (changes over time)
- Order = fact (frozen history)

Design:
- Immutable structure: changes return new instances
- Internal mapping protected from accidental mutation
- Business rules enforced in services, not here
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Mapping
from uuid import UUID

from ._validation import require_uuid
from .errors import ValidationError
from .policies import ORDER_EDIT_CUTOFF_HOURS
from .value_objects import Quantity


@dataclass(frozen=True)
class OrderDraft:
    """Editable order draft."""

    store_id: UUID
    delivery_at: datetime
    items: Mapping[UUID, Quantity]

    def __post_init__(self) -> None:
        require_uuid(self.store_id, field="draft.store_id")

        if self.delivery_at.tzinfo is None:
            raise ValidationError("delivery_at must be timezone-aware")

    @staticmethod
    def empty(store_id: UUID, delivery_at: datetime) -> "OrderDraft":
        """Create a new empty draft."""
        return OrderDraft(
            store_id=store_id,
            delivery_at=delivery_at,
            items=MappingProxyType({}),
        )

    def can_modify(self, now: datetime) -> bool:
        """Return whether the draft is still editable.

        Rule:
        - Editing closes a fixed number of hours before delivery

        Why:
        - Prevent last-minute changes that disrupt logistics
        """
        cutoff = self.delivery_at - timedelta(hours=ORDER_EDIT_CUTOFF_HOURS)
        return now < cutoff

    def set_quantity(self, product_id: UUID, qty: int) -> "OrderDraft":
        """Set quantity for a product.

        Design:
        - qty == 0 removes item
        - avoids invalid Quantity(0)
        - returns a new draft instance

        Note:
        - Structural validation happens here
        - Business rules belong in services
        """
        require_uuid(product_id, field="draft.product_id")

        if not isinstance(qty, int):
            raise ValidationError("quantity must be int")

        new_items = dict(self.items)

        if qty == 0:
            new_items.pop(product_id, None)
        else:
            new_items[product_id] = Quantity(qty)

        return OrderDraft(
            store_id=self.store_id,
            delivery_at=self.delivery_at,
            items=MappingProxyType(new_items),
        )

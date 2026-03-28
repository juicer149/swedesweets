from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .errors import ValidationError
from .value_objects import OrderId, ProductId, Quantity, StoreId, require_aware


@dataclass(frozen=True)
class RequestedItem:
    product_id: ProductId
    quantity: Quantity


@dataclass(frozen=True)
class FulfilledItem:
    product_id: ProductId
    quantity: Quantity


@dataclass(frozen=True)
class RequestedOrder:
    """
    Store intent: what the store asked for.
    Immutable snapshot.
    """

    requested_order_id: OrderId
    store_id: StoreId
    created_at: datetime
    items: tuple[RequestedItem, ...]

    def __post_init__(self) -> None:
        require_aware(self.created_at)
        if len(self.items) == 0:
            raise ValidationError("RequestedOrder must contain at least one item")


@dataclass(frozen=True)
class FulfilledOrder:
    """
    Supplier fact: what was actually packed/accepted.
    Immutable snapshot. Later marked delivered by creating a new snapshot with delivered_at set.
    """

    fulfilled_order_id: OrderId
    requested_order_id: OrderId  # relationship to RequestedOrder
    packed_at: datetime
    delivered_at: datetime | None
    items: tuple[FulfilledItem, ...]
    packing_notes: str = ""

    def __post_init__(self) -> None:
        require_aware(self.packed_at)
        if self.delivered_at is not None:
            require_aware(self.delivered_at)

        if len(self.items) == 0:
            raise ValidationError("FulfilledOrder must contain at least one item")

        if self.delivered_at is not None and self.delivered_at < self.packed_at:
            raise ValidationError("delivered_at cannot be earlier than packed_at")

    @property
    def is_delivered(self) -> bool:
        return self.delivered_at is not None

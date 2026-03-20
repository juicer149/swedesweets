from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from .errors import ValidationError


class OrderItemStatus(StrEnum):
    PENDING = "pending"
    PARTIAL = "partial"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class OrderStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    CANCELED = "canceled"  # not used yet, but reserved for future use


@dataclass(frozen=True, slots=True)
class OrderItem:
    id: UUID
    product_id: UUID
    requested_qty: int
    delivered_qty: int = 0

    def __post_init__(self):

        if self.requested_qty <= 0:
            raise ValidationError("quantity must be > 0")

        if self.delivered_qty > self.requested_qty:
            raise ValidationError("invalid delivery quantity")

    @property
    def status(self) -> OrderItemStatus:

        if self.delivered_qty == 0:
            return OrderItemStatus.PENDING

        if self.delivered_qty < self.requested_qty:
            return OrderItemStatus.PARTIAL

        return OrderItemStatus.DELIVERED


@dataclass(frozen=True, slots=True)
class Order:
    id: UUID
    store_id: UUID
    created_at: datetime
    items: tuple[OrderItem, ...]

    def __post_init__(self):

        if not self.items:
            raise ValidationError("order must contain items")

    @property
    def status(self) -> OrderStatus:

        statuses = {item.status for item in self.items}

        if statuses == {OrderItemStatus.PENDING}:
            return OrderStatus.PENDING

        if statuses == {OrderItemStatus.DELIVERED}:
            return OrderStatus.COMPLETED

        if OrderItemStatus.PENDING in statuses:
            return OrderStatus.IN_PROGRESS

        return OrderStatus.PARTIAL

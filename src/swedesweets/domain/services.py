from __future__ import annotations

from datetime import datetime
from uuid import UUID

from .errors import ValidationError
from .normalize import normalize_fulfilled_items, normalize_requested_items
from .orders import FulfilledItem, FulfilledOrder, RequestedItem, RequestedOrder
from .value_objects import OrderId, ProductId, Quantity, StoreId, require_aware


def create_requested_order(
    *,
    requested_order_id: UUID,
    store_id: UUID,
    created_at: datetime,
    items: list[tuple[UUID, int]],  # [(product_id, qty)]
) -> RequestedOrder:
    """
    Build a RequestedOrder snapshot from primitives.
    """
    require_aware(created_at)

    if len(items) == 0:
        raise ValidationError("items cannot be empty")

    requested_items = tuple(
        RequestedItem(product_id=ProductId(pid), quantity=Quantity(qty))
        for pid, qty in items
    )
    requested_items = normalize_requested_items(requested_items)

    return RequestedOrder(
        requested_order_id=OrderId(requested_order_id),
        store_id=StoreId(store_id),
        created_at=created_at,
        items=requested_items,
    )


def fulfill_requested_order(
    *,
    fulfilled_order_id: UUID,
    requested: RequestedOrder,
    packed_at: datetime,
    items: list[tuple[UUID, int]],  # what was actually packed
    packing_notes: str = "",
) -> FulfilledOrder:
    """
    Build a FulfilledOrder snapshot linked to a RequestedOrder.
    """
    require_aware(packed_at)

    if len(items) == 0:
        raise ValidationError("items cannot be empty")

    fulfilled_items = tuple(
        FulfilledItem(product_id=ProductId(pid), quantity=Quantity(qty))
        for pid, qty in items
    )
    fulfilled_items = normalize_fulfilled_items(fulfilled_items)

    return FulfilledOrder(
        fulfilled_order_id=OrderId(fulfilled_order_id),
        requested_order_id=requested.requested_order_id,
        packed_at=packed_at,
        delivered_at=None,
        items=fulfilled_items,
        packing_notes=packing_notes,
    )


def mark_delivered(*, fulfilled: FulfilledOrder, delivered_at: datetime) -> FulfilledOrder:
    """
    Return a new FulfilledOrder snapshot with delivered_at set.
    """
    require_aware(delivered_at)

    return FulfilledOrder(
        fulfilled_order_id=fulfilled.fulfilled_order_id,
        requested_order_id=fulfilled.requested_order_id,
        packed_at=fulfilled.packed_at,
        delivered_at=delivered_at,
        items=fulfilled.items,
        packing_notes=fulfilled.packing_notes,
    )

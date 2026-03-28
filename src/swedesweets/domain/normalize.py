from __future__ import annotations

from .orders import FulfilledItem, RequestedItem
from .value_objects import ProductId, Quantity


def normalize_requested_items(items: tuple[RequestedItem, ...]) -> tuple[RequestedItem, ...]:
    """
    Canonicalize items:
    - sum quantities per product_id
    - sort by product_id for stable snapshots
    """
    totals: dict[ProductId, int] = {}
    for it in items:
        totals[it.product_id] = totals.get(it.product_id, 0) + it.quantity.value

    normalized = [
        RequestedItem(product_id=pid, quantity=Quantity(qty))
        for pid, qty in totals.items()
    ]
    normalized.sort(key=lambda x: str(x.product_id.value))
    return tuple(normalized)


def normalize_fulfilled_items(items: tuple[FulfilledItem, ...]) -> tuple[FulfilledItem, ...]:
    """
    Canonicalize items:
    - sum quantities per product_id
    - sort by product_id for stable snapshots
    """
    totals: dict[ProductId, int] = {}
    for it in items:
        totals[it.product_id] = totals.get(it.product_id, 0) + it.quantity.value

    normalized = [
        FulfilledItem(product_id=pid, quantity=Quantity(qty))
        for pid, qty in totals.items()
    ]
    normalized.sort(key=lambda x: str(x.product_id.value))
    return tuple(normalized)

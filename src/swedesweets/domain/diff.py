from __future__ import annotations

from dataclasses import dataclass

from .errors import RelationshipError
from .orders import FulfilledOrder, RequestedOrder
from .value_objects import ProductId


@dataclass(frozen=True)
class ItemDiff:
    product_id: ProductId
    requested_qty: int
    fulfilled_qty: int

    @property
    def delta(self) -> int:
        return self.fulfilled_qty - self.requested_qty

    @property
    def is_missing(self) -> bool:
        return self.fulfilled_qty < self.requested_qty

    @property
    def is_extra(self) -> bool:
        return self.fulfilled_qty > self.requested_qty


def _sum_requested(requested: RequestedOrder) -> dict[ProductId, int]:
    totals: dict[ProductId, int] = {}
    for it in requested.items:
        totals[it.product_id] = totals.get(it.product_id, 0) + it.quantity.value
    return totals


def _sum_fulfilled(fulfilled: FulfilledOrder) -> dict[ProductId, int]:
    totals: dict[ProductId, int] = {}
    for it in fulfilled.items:
        totals[it.product_id] = totals.get(it.product_id, 0) + it.quantity.value
    return totals


def diff_requested_vs_fulfilled(
    requested: RequestedOrder,
    fulfilled: FulfilledOrder,
) -> tuple[ItemDiff, ...]:
    """
    Compare requested vs fulfilled per product_id.

    Returns only the products where quantity differs.
    """
    if fulfilled.requested_order_id != requested.requested_order_id:
        raise RelationshipError("FulfilledOrder does not belong to RequestedOrder")

    req = _sum_requested(requested)
    ful = _sum_fulfilled(fulfilled)

    product_ids = sorted(set(req.keys()) | set(ful.keys()), key=lambda x: str(x.value))

    diffs: list[ItemDiff] = []
    for pid in product_ids:
        r = req.get(pid, 0)
        f = ful.get(pid, 0)
        if r != f:
            diffs.append(ItemDiff(product_id=pid, requested_qty=r, fulfilled_qty=f))

    return tuple(diffs)

from __future__ import annotations

from uuid import UUID

from .diff import diff_requested_vs_fulfilled
from .errors import ValidationError
from .orders import FulfilledOrder, RequestedOrder
from .ports import Clock, FulfilledOrderRepository, RequestedOrderRepository, UnitOfWork
from .services import create_requested_order, fulfill_requested_order, mark_delivered


def request_order(
    *,
    requested_order_id: UUID,
    store_id: UUID,
    items: list[tuple[UUID, int]],
    clock: Clock,
    requested_repo: RequestedOrderRepository,
    uow: UnitOfWork | None = None,
) -> RequestedOrder:
    order = create_requested_order(
        requested_order_id=requested_order_id,
        store_id=store_id,
        created_at=clock.now(),
        items=items,
    )
    requested_repo.save(order)
    if uow:
        uow.commit()
    return order


def pack_order(
    *,
    fulfilled_order_id: UUID,
    requested_order_id: UUID,
    packed_items: list[tuple[UUID, int]],
    packing_notes: str,
    clock: Clock,
    requested_repo: RequestedOrderRepository,
    fulfilled_repo: FulfilledOrderRepository,
    uow: UnitOfWork | None = None,
) -> FulfilledOrder:
    requested = requested_repo.get(requested_order_id)

    existing = fulfilled_repo.get_by_requested(requested_order_id)
    if existing is not None:
        raise ValidationError("Order already packed/fulfilled")

    fulfilled = fulfill_requested_order(
        fulfilled_order_id=fulfilled_order_id,
        requested=requested,
        packed_at=clock.now(),
        items=packed_items,
        packing_notes=packing_notes,
    )

    fulfilled_repo.save(fulfilled)
    if uow:
        uow.commit()
    return fulfilled


def deliver_order(
    *,
    requested_order_id: UUID,
    clock: Clock,
    fulfilled_repo: FulfilledOrderRepository,
    uow: UnitOfWork | None = None,
) -> FulfilledOrder:
    fulfilled = fulfilled_repo.get_by_requested(requested_order_id)
    if fulfilled is None:
        raise ValidationError("Cannot deliver: order not packed yet")

    if fulfilled.is_delivered:
        return fulfilled

    delivered = mark_delivered(fulfilled=fulfilled, delivered_at=clock.now())
    fulfilled_repo.save(delivered)
    if uow:
        uow.commit()
    return delivered

from .diff import ItemDiff

def get_order_diff(
    *,
    requested_order_id: UUID,
    requested_repo: RequestedOrderRepository,
    fulfilled_repo: FulfilledOrderRepository,
) -> tuple[ItemDiff, ...]:
    requested = requested_repo.get(requested_order_id)
    fulfilled = fulfilled_repo.get_by_requested(requested_order_id)
    if fulfilled is None:
        return ()
    return diff_requested_vs_fulfilled(requested, fulfilled)

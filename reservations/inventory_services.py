"""Inventory mutations that must account for active reservations."""

from __future__ import annotations

from datetime import date

from django.db import transaction

from inventory.errors import InvalidStockOperation
from inventory.models import InventoryBatch
from reservations.selectors import (
    active_reserved_quantity_for_batch_pk,
)


@transaction.atomic
def update_batch(
    *,
    batch: InventoryBatch,
    quantity: int,
    best_before: date,
    location: str,
    user=None,
) -> InventoryBatch:
    """Correct a batch without reducing stock below active reservations."""

    batch = (
        InventoryBatch.objects
        .select_for_update()
        .select_related("product")
        .get(pk=batch.pk)
    )

    if batch.status == InventoryBatch.Status.CLOSED:
        raise InvalidStockOperation(
            f"Batch {batch.batch_id} is closed"
        )

    reserved_quantity = (
        active_reserved_quantity_for_batch_pk(
            batch_pk=batch.pk,
        )
    )

    if quantity < reserved_quantity:
        raise InvalidStockOperation(
            f"Cannot set batch {batch.batch_id} to {quantity} units; "
            f"{reserved_quantity} units are reserved."
        )

    batch.adjust_quantity(
        quantity=quantity,
    )

    batch.best_before = best_before
    batch.location = location
    batch.save(
        update_fields=[
            "best_before",
            "location",
            "updated_at",
        ]
    )
    batch.mark_as_edited(
        user=user,
    )

    return batch


@transaction.atomic
def close_batch(
    *,
    batch: InventoryBatch,
    user=None,
) -> InventoryBatch:
    """Close a batch only when no active quantity is reserved."""

    batch = (
        InventoryBatch.objects
        .select_for_update()
        .select_related("product")
        .get(pk=batch.pk)
    )

    reserved_quantity = (
        active_reserved_quantity_for_batch_pk(
            batch_pk=batch.pk,
        )
    )

    if reserved_quantity > 0:
        raise InvalidStockOperation(
            f"Cannot close batch {batch.batch_id}; "
            f"{reserved_quantity} units are reserved."
        )

    batch.close(
        user=user,
    )

    return batch

#! src/swedesweets/domain/services.py
"""
Domain services.

Purpose:
- Orchestrate domain behavior
- Apply business rules
- Convert external input into domain objects

Design:
- Stateless
- Side-effect free
- Framework-independent
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable
from uuid import UUID, uuid4

from ._validation import require_uuid
from .draft import OrderDraft
from .errors import BusinessRuleError, ValidationError
from .order import Order, OrderItem
from .policies import enforce_max_quantity
from .value_objects import Quantity


def now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


# ------------------------
# Draft
# ------------------------


def create_draft(*, store_id: UUID, delivery_at: datetime) -> OrderDraft:
    """Create a new empty draft.

    Entry point for building an order over time.
    """
    return OrderDraft.empty(
        store_id=store_id,
        delivery_at=delivery_at,
    )


def update_draft(
    *,
    draft: OrderDraft,
    product_id: UUID,
    qty: int,
    current_time: datetime,
) -> OrderDraft:
    """Update quantity for one product in a draft.

    Responsibilities:
    - enforce cutoff rule
    - enforce quantity limits
    - delegate actual state change to the draft
    """
    if not draft.can_modify(current_time):
        raise BusinessRuleError("order can no longer be modified")

    enforce_max_quantity(qty)

    return draft.set_quantity(product_id, qty)


# ------------------------
# Finalize
# ------------------------


def finalize_draft(*, draft: OrderDraft) -> Order:
    """Convert a draft into a finalized order.

    Important:
    - Enforces cutoff rule
    - Rejects empty drafts
    - Produces an immutable snapshot
    """
    current_time = now()

    if not draft.can_modify(current_time):
        raise BusinessRuleError("cannot finalize after cutoff")

    if not draft.items:
        raise ValidationError("cannot finalize empty order")

    items = tuple(
        OrderItem(product_id=product_id, quantity=quantity)
        for product_id, quantity in draft.items.items()
    )

    return Order(
        id=uuid4(),
        store_id=draft.store_id,
        created_at=current_time,
        items=items,
    )


# ------------------------
# Direct order (fallback)
# ------------------------


def create_order(
    *,
    store_id: UUID,
    requested_items: Iterable[tuple[UUID, int]],
) -> Order:
    """Create an order directly from raw input.

    Use cases:
    - tests
    - simple integrations
    - fallback flow without drafts

    Important:
    - Aggregates duplicate product entries
    - Enforces business rules
    """
    aggregated: dict[UUID, int] = defaultdict(int)

    for product_id, qty in requested_items:
        require_uuid(product_id, field="product_id")
        enforce_max_quantity(qty)
        aggregated[product_id] += qty

    if not aggregated:
        raise ValidationError("order must contain items")

    items = tuple(
        OrderItem(
            product_id=product_id,
            quantity=Quantity(qty),
        )
        for product_id, qty in aggregated.items()
    )

    return Order(
        id=uuid4(),
        store_id=store_id,
        created_at=now(),
        items=items,
    )

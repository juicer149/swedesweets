from datetime import datetime, timezone
from uuid import uuid4, UUID
from typing import Iterable

from .order import Order, OrderItem
from .assortment import StoreAssortment
from .errors import ValidationError, BusinessRuleError


def now():
    return datetime.now(timezone.utc)


def create_order(
    *,
    store_id: UUID,
    assortment: StoreAssortment,
    requested_items: Iterable[tuple[UUID, int]],
) -> Order:

    items = []

    for product_id, qty in requested_items:
        if qty <= 0:
            raise ValidationError("quantity must be > 0")

        if not assortment.includes(product_id):
            raise BusinessRuleError("product not in assortment")

        items.append(OrderItem(product_id=product_id, quantity=qty))

    if not items:
        raise ValidationError("empty order")

    return Order(
        id=uuid4(),
        store_id=store_id,
        created_at=now(),
        items=tuple(items),
    )

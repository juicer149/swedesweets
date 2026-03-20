from uuid import uuid4
from datetime import datetime, timezone

from .order import Order, OrderItem


def create_order(store_id, items):

    order_items = tuple(
        OrderItem(
            id=uuid4(),
            product_id=product_id,
            requested_qty=qty,
        )
        for product_id, qty in items
    )

    return Order(
        id=uuid4(),
        store_id=store_id,
        created_at=datetime.now(timezone.utc),
        items=order_items,
    )

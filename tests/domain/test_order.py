import pytest
from uuid import uuid4
from datetime import datetime, timezone

from swedesweets.domain import Order, OrderItem, Quantity
from swedesweets.domain.errors import ValidationError


def now():
    return datetime.now(timezone.utc)


# ------------------------
# OrderItem
# ------------------------

def test_order_item_valid():
    item = OrderItem(
        product_id=uuid4(),
        quantity=Quantity(2),
    )

    assert item.quantity.value == 2


def test_order_item_invalid_quantity():
    with pytest.raises(ValidationError):
        Quantity(0)


# ------------------------
# Order
# ------------------------

def test_order_creation():
    order = Order(
        id=uuid4(),
        store_id=uuid4(),
        created_at=now(),
        items=(
            OrderItem(product_id=uuid4(), quantity=Quantity(1)),
        ),
    )

    assert len(order.items) == 1


def test_order_must_have_items():
    with pytest.raises(ValidationError):
        Order(
            id=uuid4(),
            store_id=uuid4(),
            created_at=now(),
            items=(),
        )


def test_order_requires_timezone():
    with pytest.raises(ValidationError):
        Order(
            id=uuid4(),
            store_id=uuid4(),
            created_at=datetime.now(),  # ❌ no timezone
            items=(OrderItem(product_id=uuid4(), quantity=Quantity(1)),),
        )

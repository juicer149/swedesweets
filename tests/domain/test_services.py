import pytest

from swedesweets.domain import create_order
from swedesweets.domain.errors import ValidationError, BusinessRuleError


def test_create_order_success(store, products):
    product = products[0]

    order = create_order(
        store_id=store.id,
        requested_items=[(product.id, 3)],
    )

    assert len(order.items) == 1
    assert order.items[0].quantity.value == 3


def test_create_order_aggregates_duplicates(store, products):
    product = products[0]

    order = create_order(
        store_id=store.id,
        requested_items=[
            (product.id, 2),
            (product.id, 3),
        ],
    )

    assert len(order.items) == 1
    assert order.items[0].quantity.value == 5


def test_create_order_empty_fails(store):
    with pytest.raises(ValidationError):
        create_order(
            store_id=store.id,
            requested_items=[],
        )


def test_create_order_invalid_quantity_zero(store, products):
    product = products[0]

    with pytest.raises(ValidationError):
        create_order(
            store_id=store.id,
            requested_items=[(product.id, 0)],
        )


def test_create_order_exceeds_max_quantity(store, products):
    product = products[0]

    with pytest.raises(BusinessRuleError):
        create_order(
            store_id=store.id,
            requested_items=[(product.id, 100)],
        )

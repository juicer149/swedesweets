import pytest
from uuid import uuid4

from swedesweets.domain.services import create_order
from swedesweets.domain.assortment import StoreAssortment, StoreProduct
from swedesweets.domain.errors import ValidationError, BusinessRuleError


def test_create_order_success():
    store_id = uuid4()
    product_id = uuid4()

    assortment = StoreAssortment(
        store_id=store_id,
        items=(
            StoreProduct(
                id=uuid4(),
                store_id=store_id,
                product_id=product_id,
            ),
        ),
    )

    order = create_order(
        store_id=store_id,
        assortment=assortment,
        requested_items=[(product_id, 3)],
    )

    assert len(order.items) == 1
    assert order.items[0].quantity == 3


def test_create_order_invalid_product():
    store_id = uuid4()

    assortment = StoreAssortment(store_id=store_id, items=())

    with pytest.raises(BusinessRuleError):
        create_order(
            store_id=store_id,
            assortment=assortment,
            requested_items=[(uuid4(), 1)],
        )


def test_create_order_empty_fails():
    with pytest.raises(ValidationError):
        create_order(
            store_id=uuid4(),
            assortment=StoreAssortment(store_id=uuid4(), items=()),
            requested_items=[],
        )

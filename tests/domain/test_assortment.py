import pytest
from uuid import uuid4

from swedesweets.domain.assortment import StoreAssortment, StoreProduct
from swedesweets.domain.errors import ValidationError


def test_assortment_includes_product():
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

    assert assortment.includes(product_id)


def test_assortment_add_product():
    store_id = uuid4()
    product_id = uuid4()

    assortment = StoreAssortment(store_id=store_id, items=())
    new_assortment = assortment.add(product_id)

    assert new_assortment.includes(product_id)


def test_assortment_rejects_duplicate_products():
    store_id = uuid4()
    product_id = uuid4()

    with pytest.raises(ValidationError):
        StoreAssortment(
            store_id=store_id,
            items=(
                StoreProduct(id=uuid4(), store_id=store_id, product_id=product_id),
                StoreProduct(id=uuid4(), store_id=store_id, product_id=product_id),
            ),
        )

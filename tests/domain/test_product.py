import pytest
from uuid import uuid4

from swedesweets.domain import Product, ProductCode
from swedesweets.domain.errors import ValidationError


def test_product_valid():
    product = Product(
        id=uuid4(),
        code=ProductCode(42),
        name="Cola nappar",
    )

    assert product.name == "Cola nappar"
    assert int(product.code) == 42


def test_product_requires_name():
    with pytest.raises(ValidationError):
        Product(
            id=uuid4(),
            code=ProductCode(1),
            name="",
        )


def test_product_name_max_length():
    with pytest.raises(ValidationError):
        Product(
            id=uuid4(),
            code=ProductCode(1),
            name="x" * 256,
        )


def test_product_requires_valid_code():
    with pytest.raises(ValidationError):
        Product(
            id=uuid4(),
            code=ProductCode(0),
            name="Cola",
        )

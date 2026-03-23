import pytest
from uuid import uuid4

from swedesweets.domain import Product, Store, ProductCode


@pytest.fixture
def store():
    return Store(
        id=uuid4(),
        name="Test Store",
    )


@pytest.fixture
def product():
    return Product(
        id=uuid4(),
        code=ProductCode(1),
        name="Cola nappar",
    )


@pytest.fixture
def products():
    return [
        Product(id=uuid4(), code=ProductCode(1), name="Cola"),
        Product(id=uuid4(), code=ProductCode(2), name="Sura"),
        Product(id=uuid4(), code=ProductCode(3), name="Choklad"),
    ]

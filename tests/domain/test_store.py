import pytest
from uuid import uuid4

from swedesweets.domain import Store
from swedesweets.domain.errors import ValidationError


def test_store_valid():
    store = Store(id=uuid4(), name="My Store")

    assert store.name == "My Store"


def test_store_requires_name():
    with pytest.raises(ValidationError):
        Store(id=uuid4(), name="")

import pytest

from swedesweets.domain import Quantity, ProductCode
from swedesweets.domain.errors import ValidationError


def test_quantity_must_be_positive():
    with pytest.raises(ValidationError):
        Quantity(0)


def test_quantity_add():
    q1 = Quantity(2)
    q2 = Quantity(3)

    result = q1.add(q2)

    assert result.value == 5


def test_quantity_subtract_invalid():
    q1 = Quantity(2)
    q2 = Quantity(2)

    with pytest.raises(ValidationError):
        q1.subtract(q2)


def test_product_code_positive():
    with pytest.raises(ValidationError):
        ProductCode(0)

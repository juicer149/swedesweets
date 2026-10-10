from __future__ import annotations

import pytest

from orders.datatypes import BuyerInput, OrderLineInput
from orders.errors import InvalidOrderOperation


@pytest.mark.django_db
def test_order_line_input_accepts_product_id_or_product(apple):
    by_id = OrderLineInput.units(
        product_id=apple.id,
        quantity=10,
    )

    by_product = OrderLineInput.units(
        product=apple,
        quantity=10,
    )

    assert by_id.resolve_product_id() == apple.id
    assert by_product.resolve_product_id() == apple.id


@pytest.mark.django_db
def test_order_line_input_accepts_matching_product_and_product_id(apple):
    line = OrderLineInput.units(
        product=apple,
        product_id=apple.id,
        quantity=10,
    )

    assert line.resolve_product_id() == apple.id


@pytest.mark.django_db
def test_order_line_input_rejects_conflicting_product_and_product_id(
    apple,
    banana,
):
    line = OrderLineInput.units(
        product=apple,
        product_id=banana.id,
        quantity=10,
    )

    with pytest.raises(InvalidOrderOperation, match="different products"):
        line.resolve_product_id()


def test_order_line_input_rejects_missing_product_reference():
    line = OrderLineInput.units(
        quantity=10,
    )

    with pytest.raises(
        InvalidOrderOperation,
        match="product_id or product is required",
    ):
        line.resolve_product_id()


def test_order_line_input_counts_whole_stock_units():
    line = OrderLineInput.units(
        product_id=1,
        quantity=10,
    )

    assert line.quantity == 10


@pytest.mark.parametrize(
    "quantity",
    [2.5, "3", True],
)
def test_order_line_input_rejects_a_quantity_that_is_not_a_whole_number(
    quantity,
):
    with pytest.raises(
        InvalidOrderOperation,
        match="must be a whole number",
    ):
        OrderLineInput.units(
            product_id=1,
            quantity=quantity,
        )


def test_buyer_input_represents_buyer_without_customer_model():
    buyer = BuyerInput(
        name="Marie Dupont",
        email="marie@example.fr",
        phone_number="+33612345678",
        country="FR",
        city="Annecy",
        address_line="10 Rue du Lac",
    )

    assert buyer.name == "Marie Dupont"
    assert buyer.email == "marie@example.fr"
    assert buyer.phone_number == "+33612345678"
    assert buyer.country == "FR"
    assert buyer.city == "Annecy"
    assert buyer.address_line == "10 Rue du Lac"
    assert buyer.postal_code == ""

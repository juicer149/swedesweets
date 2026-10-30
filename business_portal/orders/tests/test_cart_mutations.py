from __future__ import annotations

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from accounts.tests.factories import (
    customer_user_factory,
)
from business.cart_services import (
    add_catalog_offer_to_cart,
)
from business.models import BusinessCart
from business.tests.factories import (
    standard_business_offer_factory,
)
from carts.models import CartLine
from customers.tests.factories import (
    customer_factory,
)
from inventory.tests.conftest import TODAY
from inventory.tests.factories import (
    batch_factory,
)
from products.tests.factories import (
    product_factory,
)

pytestmark = pytest.mark.usefixtures("fast_password_hashing")


def _stored_messages(
    response,
) -> list[str]:
    return [
        str(message)
        for message in get_messages(
            response.wsgi_request
        )
    ]


def _login_customer(
    *,
    client,
):
    customer = customer_factory()

    user = customer_user_factory(
        customer=customer,
    )

    client.force_login(
        user
    )

    return customer


def _create_cart_line(
    *,
    customer,
    product,
    quantity: int,
) -> CartLine:
    offer = standard_business_offer_factory(
        product=product,
    )

    return add_catalog_offer_to_cart(
        customer=customer,
        product=product,
        commercial_price_id=offer.pk,
        quantity=quantity,
    )


@pytest.mark.django_db
def test_customer_can_set_cart_line_quantity(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=1,
    )

    response = client.post(
        reverse(
            "business_portal:set_cart_line_quantity",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
        {
            "quantity": "5",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "business_portal:cart"
    )

    line.refresh_from_db()

    assert line.quantity == 5


@pytest.mark.django_db
def test_set_cart_line_quantity_returns_json_success(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=1,
    )

    response = client.post(
        reverse(
            "business_portal:set_cart_line_quantity",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
        {
            "quantity": "5",
        },
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "message": "Quantity updated.",
        "quantity": 5,
        "change_direction": 1,
        "line_total_label": None,
        "subtotal_label": None,
        "subtotal_delta_label": None,
    }

    line.refresh_from_db()

    assert line.quantity == 5


@pytest.mark.django_db
def test_set_cart_line_quantity_rejects_invalid_quantity(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=3,
    )

    response = client.post(
        reverse(
            "business_portal:set_cart_line_quantity",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
        {
            "quantity": "not-a-number",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "business_portal:cart"
    )

    line.refresh_from_db()

    assert line.quantity == 3

    assert _stored_messages(
        response
    ) == [
        "Quantity must be a whole number."
    ]


@pytest.mark.django_db
def test_set_cart_line_quantity_returns_json_error_for_invalid_quantity(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=3,
    )

    response = client.post(
        reverse(
            "business_portal:set_cart_line_quantity",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
        {
            "quantity": "not-a-number",
        },
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 400

    assert response.json() == {
        "ok": False,
        "message": "Quantity must be a whole number.",
    }

    line.refresh_from_db()

    assert line.quantity == 3


@pytest.mark.django_db
def test_set_cart_line_quantity_rejects_non_positive_quantity(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=3,
    )

    response = client.post(
        reverse(
            "business_portal:set_cart_line_quantity",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
        {
            "quantity": "0",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "business_portal:cart"
    )

    line.refresh_from_db()

    assert line.quantity == 3

    assert _stored_messages(
        response
    ) == [
        "cart line quantity must be positive"
    ]


@pytest.mark.django_db
def test_set_cart_line_quantity_returns_json_error_for_non_positive_quantity(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=3,
    )

    response = client.post(
        reverse(
            "business_portal:set_cart_line_quantity",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
        {
            "quantity": "-1",
        },
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 400

    assert response.json() == {
        "ok": False,
        "message": "cart line quantity must be positive",
    }

    line.refresh_from_db()

    assert line.quantity == 3


@pytest.mark.django_db
def test_set_cart_line_quantity_does_not_apply_stock_availability(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    batch_factory(
        product=product,
        today=TODAY,
        quantity=10,
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=3,
    )

    response = client.post(
        reverse(
            "business_portal:set_cart_line_quantity",
            kwargs={
                "cart_line_id": line.id,
            },
        ),
        {
            "quantity": "11",
        },
    )

    assert response.status_code == 302

    line.refresh_from_db()

    assert line.quantity == 11


@pytest.mark.django_db
def test_set_cart_line_quantity_cannot_mutate_another_customer_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    other_customer = customer_factory(
        name="Other Customer",
        email="other@example.com",
    )

    product = product_factory(
        name="Apple",
    )

    other_line = _create_cart_line(
        customer=other_customer,
        product=product,
        quantity=3,
    )

    response = client.post(
        reverse(
            "business_portal:set_cart_line_quantity",
            kwargs={
                "cart_line_id": other_line.id,
            },
        ),
        {
            "quantity": "5",
        },
    )

    assert response.status_code == 404

    other_line.refresh_from_db()

    assert other_line.quantity == 3

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_set_cart_line_quantity_returns_404_for_unknown_line(
    client,
):
    customer = _login_customer(
        client=client,
    )

    response = client.post(
        reverse(
            "business_portal:set_cart_line_quantity",
            kwargs={
                "cart_line_id": 999_999,
            },
        ),
        {
            "quantity": "5",
        },
    )

    assert response.status_code == 404

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_set_cart_line_quantity_get_is_not_allowed(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=1,
    )

    response = client.get(
        reverse(
            "business_portal:set_cart_line_quantity",
            kwargs={
                "cart_line_id": line.id,
            },
        )
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_customer_can_remove_cart_line(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=3,
    )

    response = client.post(
        reverse(
            "business_portal:remove_cart_line",
            kwargs={
                "cart_line_id": line.id,
            },
        )
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "business_portal:cart"
    )

    assert not CartLine.objects.filter(
        pk=line.pk,
    ).exists()


@pytest.mark.django_db
def test_remove_last_cart_line_keeps_empty_customer_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=3,
    )

    cart_id = line.cart_id

    response = client.post(
        reverse(
            "business_portal:remove_cart_line",
            kwargs={
                "cart_line_id": line.id,
            },
        )
    )

    assert response.status_code == 302

    business_cart = BusinessCart.objects.get(
        customer=customer,
    )

    assert business_cart.cart_id == cart_id
    assert not business_cart.cart.lines.exists()


@pytest.mark.django_db
def test_remove_cart_line_cannot_mutate_another_customer_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    other_customer = customer_factory(
        name="Other Customer",
        email="other@example.com",
    )

    product = product_factory(
        name="Apple",
    )

    other_line = _create_cart_line(
        customer=other_customer,
        product=product,
        quantity=3,
    )

    response = client.post(
        reverse(
            "business_portal:remove_cart_line",
            kwargs={
                "cart_line_id": other_line.id,
            },
        )
    )

    assert response.status_code == 404

    assert CartLine.objects.filter(
        pk=other_line.pk,
    ).exists()

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_remove_cart_line_returns_404_for_unknown_line(
    client,
):
    customer = _login_customer(
        client=client,
    )

    response = client.post(
        reverse(
            "business_portal:remove_cart_line",
            kwargs={
                "cart_line_id": 999_999,
            },
        )
    )

    assert response.status_code == 404

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_remove_cart_line_get_is_not_allowed(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=1,
    )

    response = client.get(
        reverse(
            "business_portal:remove_cart_line",
            kwargs={
                "cart_line_id": line.id,
            },
        )
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_customer_can_remove_cart_line_with_json_response(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    line = _create_cart_line(
        customer=customer,
        product=product,
        quantity=3,
    )

    line_id = line.id

    response = client.post(
        reverse(
            "business_portal:remove_cart_line",
            kwargs={
                "cart_line_id": line_id,
            },
        ),
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "message": "Product removed from your cart.",
        "cart_line_id": line_id,
        "change_direction": -1,
        "subtotal_label": "€0.00",
        "subtotal_delta_label": None,
    }

    assert not CartLine.objects.filter(
        pk=line_id,
    ).exists()


@pytest.mark.django_db
def test_quantity_response_recalculates_priced_business_line(client):
    from decimal import Decimal

    from pricing.tests.factories import price_amount_factory

    customer = _login_customer(client=client)
    product = product_factory(name="Priced Apple")
    line = _create_cart_line(customer=customer, product=product, quantity=2)
    price_amount_factory(commercial_price=line.commercial_price, price=Decimal("7.50"))
    response = client.post(
        reverse(
            "business_portal:set_cart_line_quantity", kwargs={"cart_line_id": line.id},
        ),
        {"quantity": "5"}, HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    assert response.json()["line_total_label"] == "€37.50"


@pytest.mark.django_db
def test_priced_business_add_and_remove_return_exact_subtotal_changes(client):
    from decimal import Decimal

    from business_portal.orders.cart_viewmodels import build_portal_cart_context
    from pricing.tests.factories import price_amount_factory

    customer = _login_customer(client=client)
    line = _create_cart_line(customer=customer, product=product_factory(), quantity=2)
    price_amount_factory(commercial_price=line.commercial_price, price=Decimal("7.50"))
    added = client.post(reverse("business_portal:add_cart_offer"), {
        "commercial_price_id": line.commercial_price_id,
    }, HTTP_ACCEPT="application/json").json()
    assert added["ok"] is True
    assert added["subtotal_label"] == "€22.50"
    assert added["subtotal_delta_label"] == "+€7.50"
    assert added["change_direction"] == 1
    assert build_portal_cart_context(cart=line.cart).subtotal_label == "€22.50"

    removed = client.post(reverse("business_portal:remove_cart_line", kwargs={
        "cart_line_id": line.id,
    }), HTTP_ACCEPT="application/json").json()
    assert removed["subtotal_label"] == "€0.00"
    assert removed["subtotal_delta_label"] == "−€22.50"
    assert removed["change_direction"] == -1


@pytest.mark.django_db
def test_business_subtotal_is_hidden_if_any_line_has_no_price(client):
    from decimal import Decimal

    from business_portal.orders.cart_viewmodels import build_portal_cart_context
    from pricing.tests.factories import price_amount_factory

    customer = _login_customer(client=client)
    line = _create_cart_line(customer=customer, product=product_factory(), quantity=2)
    price_amount_factory(commercial_price=line.commercial_price, price=Decimal("7.50"))
    _create_cart_line(
        customer=customer, product=product_factory(name="Other"), quantity=1
    )
    context = build_portal_cart_context(cart=line.cart)
    assert context.subtotal is None
    assert context.subtotal_label is None


@pytest.mark.django_db
def test_checked_products_add_together_with_one_subtotal_feedback(client):
    from decimal import Decimal

    from pricing.tests.factories import price_amount_factory

    _login_customer(client=client)
    offers = [
        standard_business_offer_factory(
            product=product_factory(name=f"Checked {index}"),
        )
        for index in range(2)
    ]
    for offer in offers:
        price_amount_factory(commercial_price=offer, price=Decimal("7.50"))
    response = client.post(reverse("business_portal:add_cart_offer"), {
        "commercial_price_id": [offer.pk for offer in offers],
    }, HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["lines"]) == 2
    assert all(line["quantity"] == 1 and line["line_html"] for line in payload["lines"])
    assert payload["subtotal_label"] == "€15.00"
    assert payload["subtotal_delta_label"] == "+€15.00"


@pytest.mark.django_db
def test_checked_product_batch_rolls_back_when_later_offer_is_rejected(client):
    customer = _login_customer(client=client)
    valid = standard_business_offer_factory(product=product_factory())
    unavailable = standard_business_offer_factory(
        product=product_factory(name="Rejected"),
    )
    unavailable.enabled = False
    unavailable.save(update_fields=["enabled"])
    response = client.post(reverse("business_portal:add_cart_offer"), {
        "commercial_price_id": [valid.pk, unavailable.pk],
    }, HTTP_ACCEPT="application/json")
    assert response.status_code == 400
    from business.cart_selectors import get_customer_cart

    cart = get_customer_cart(customer=customer)
    assert cart is None or not cart.lines.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("values", [[], ["bad"], ["0"], ["-1"], ["1"] * 101])
def test_checked_product_batch_rejects_invalid_selection(client, values):
    _login_customer(client=client)
    response = client.post(reverse("business_portal:add_cart_offer"), {
        "commercial_price_id": values,
    }, HTTP_ACCEPT="application/json")
    assert response.status_code == 400
    assert response.json()["ok"] is False


@pytest.mark.django_db
def test_checked_product_batch_deduplicates_ids(client):
    _login_customer(client=client)
    offer = standard_business_offer_factory(product=product_factory())
    response = client.post(reverse("business_portal:add_cart_offer"), {
        "commercial_price_id": [offer.pk, offer.pk],
    }, HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    assert len(response.json()["lines"]) == 1
    assert response.json()["quantity"] == 1

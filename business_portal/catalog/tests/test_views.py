from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from accounts.tests.factories import (
    customer_user_factory,
)
from business.models import BusinessCart
from business.tests.factories import (
    standard_business_offer_factory,
)
from customers.tests.factories import (
    customer_factory,
)
from inventory.tests.conftest import TODAY
from inventory.tests.factories import (
    batch_factory,
)
from orders.models import Order
from pricing.models import CommercialPrice
from pricing.tests.factories import (
    commercial_price_factory,
    price_amount_factory,
)
from products.tests.factories import (
    product_factory,
)


def _business_price(
    *,
    product,
    batch=None,
    price: str = "8.50",
    enabled: bool = True,
    reason: str = "",
) -> CommercialPrice:
    commercial_price = commercial_price_factory(
        product=product,
        batch=batch,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=enabled,
        reason=reason,
    )

    price_amount_factory(
        commercial_price=commercial_price,
        price=Decimal(price),
    )

    return commercial_price


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


def _customer_cart(
    *,
    customer,
):
    return BusinessCart.objects.get(
        customer=customer,
    ).cart


def _customer_cart_line(
    *,
    customer,
):
    return _customer_cart(
        customer=customer,
    ).lines.get()


def _assert_no_business_cart(
    *,
    customer,
) -> None:
    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


def _assert_no_business_draft_order(
    *,
    customer,
) -> None:
    assert not Order.objects.filter(
        channel=Order.Channel.BUSINESS,
        customer=customer,
        status=Order.Status.DRAFT,
    ).exists()


@pytest.mark.django_db
def test_catalog_requires_login(
    client,
):
    response = client.get(
        reverse(
            "business_portal:catalog"
        )
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_catalog_renders_for_business_customer(
    client,
):
    _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_business_offer_factory(
        product=product,
    )

    batch_factory(
        product=product,
        today=TODAY,
        quantity=10,
    )

    response = client.get(
        reverse(
            "business_portal:catalog"
        )
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_product_detail_requires_login(
    client,
):
    product = product_factory(
        name="Apple",
    )

    response = client.get(
        reverse(
            "business_portal:catalog_product",
            kwargs={
                "product_id": product.pk,
            },
        )
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_product_detail_renders_orderable_product(
    client,
):
    _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_business_offer_factory(
        product=product,
    )

    batch_factory(
        product=product,
        today=TODAY,
        quantity=10,
    )

    response = client.get(
        reverse(
            "business_portal:catalog_product",
            kwargs={
                "product_id": product.pk,
            },
        )
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_product_detail_returns_404_for_unavailable_product(
    client,
):
    _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    product.active = False
    product.save(
        update_fields=[
            "active",
            "updated_at",
        ],
    )

    response = client.get(
        reverse(
            "business_portal:catalog_product",
            kwargs={
                "product_id": product.pk,
            },
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_catalog_add_product_requires_login(
    client,
):
    product = product_factory(
        name="Apple",
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.pk,
            },
        )
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_catalog_add_product_requires_post(
    client,
):
    _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    response = client.get(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.pk,
            },
        )
    )

    assert response.status_code == 405


@pytest.mark.django_db
def test_catalog_add_product_returns_404_for_unknown_product(
    client,
):
    customer = _login_customer(
        client=client,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": 999_999,
            },
        )
    )

    assert response.status_code == 404

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_customer_can_add_catalog_product_to_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_offer = standard_business_offer_factory(
        product=product,
    )

    batch_factory(
        product=product,
        today=TODAY,
        quantity=100,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        )
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "business_portal:catalog"
    )

    line = _customer_cart_line(
        customer=customer,
    )

    assert line.commercial_price == standard_offer
    assert line.quantity == 1

    _assert_no_business_draft_order(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_defaults_missing_quantity_to_one(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_offer = standard_business_offer_factory(
        product=product,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "",
        },
    )

    assert response.status_code == 302

    line = _customer_cart_line(
        customer=customer,
    )

    assert line.commercial_price == standard_offer
    assert line.quantity == 1


@pytest.mark.django_db
def test_catalog_add_product_accepts_explicit_quantity(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_offer = standard_business_offer_factory(
        product=product,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "",
            "quantity": "4",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "business_portal:catalog"
    )

    line = _customer_cart_line(
        customer=customer,
    )

    assert line.commercial_price == standard_offer
    assert line.quantity == 4


@pytest.mark.django_db
def test_catalog_add_product_accepts_explicit_quantity_for_batch_offer(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_business_offer_factory(
        product=product,
    )

    batch = batch_factory(
        product=product,
        today=TODAY,
        quantity=100,
    )

    commercial_price = _business_price(
        product=product,
        batch=batch,
        price="7.50",
        reason=CommercialPrice.Reason.SHORT_DATED,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": str(
                commercial_price.pk
            ),
            "quantity": "3",
        },
    )

    assert response.status_code == 302

    line = _customer_cart_line(
        customer=customer,
    )

    assert line.commercial_price == commercial_price
    assert line.quantity == 3


@pytest.mark.django_db
def test_customer_adding_same_catalog_product_increments_quantity(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_offer = standard_business_offer_factory(
        product=product,
    )

    url = reverse(
        "business_portal:catalog_add_product",
        kwargs={
            "product_id": product.id,
        },
    )

    first_response = client.post(
        url,
        {
            "commercial_price_id": "",
            "quantity": "2",
        },
    )

    second_response = client.post(
        url,
        {
            "commercial_price_id": "",
            "quantity": "3",
        },
    )

    assert first_response.status_code == 302
    assert second_response.status_code == 302

    cart = _customer_cart(
        customer=customer,
    )

    assert cart.lines.count() == 1

    line = cart.lines.get()

    assert line.commercial_price == standard_offer
    assert line.quantity == 5


@pytest.mark.django_db
def test_catalog_add_product_rejects_empty_quantity(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    standard_business_offer_factory(
        product=product,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "",
            "quantity": "",
        },
    )

    assert response.status_code == 302

    assert _stored_messages(
        response
    ) == [
        "quantity is required"
    ]

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "quantity",
        "expected_message",
    ),
    [
        (
            "abc",
            "invalid quantity",
        ),
        (
            "1.5",
            "invalid quantity",
        ),
        (
            "0",
            "cart line quantity must be positive",
        ),
        (
            "-1",
            "cart line quantity must be positive",
        ),
    ],
)
def test_catalog_add_product_rejects_invalid_quantity(
    client,
    quantity,
    expected_message,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_business_offer_factory(
        product=product,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "",
            "quantity": quantity,
        },
    )

    assert response.status_code == 302

    assert _stored_messages(
        response
    ) == [
        expected_message
    ]

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_returns_json_error_for_empty_quantity(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    standard_business_offer_factory(
        product=product,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "",
            "quantity": "",
        },
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 400
    assert response.json() == {
        "ok": False,
        "message": "quantity is required",
    }

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_returns_json_error_for_invalid_quantity(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    standard_business_offer_factory(
        product=product,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "",
            "quantity": "abc",
        },
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 400
    assert response.json() == {
        "ok": False,
        "message": "invalid quantity",
    }

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_accepts_explicit_standard_selection(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_offer = standard_business_offer_factory(
        product=product,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": str(
                standard_offer.pk
            ),
        },
    )

    assert response.status_code == 302

    line = _customer_cart_line(
        customer=customer,
    )

    assert line.commercial_price == standard_offer
    assert line.quantity == 1


@pytest.mark.django_db
def test_catalog_add_product_accepts_business_batch_offer(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    standard_business_offer_factory(
        product=product,
    )

    batch = batch_factory(
        product=product,
        today=TODAY,
        quantity=10,
    )

    commercial_price = _business_price(
        product=product,
        batch=batch,
        price="7.50",
        reason=CommercialPrice.Reason.SHORT_DATED,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": str(
                commercial_price.pk
            ),
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "business_portal:catalog"
    )

    line = _customer_cart_line(
        customer=customer,
    )

    assert line.commercial_price == commercial_price
    assert line.quantity == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "commercial_price_id",
    [
        "abc",
        "0",
        "-1",
    ],
)
def test_catalog_add_product_rejects_invalid_offer_id(
    client,
    commercial_price_id,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": commercial_price_id,
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "business_portal:catalog"
    )

    assert _stored_messages(
        response
    ) == [
        "invalid business offer"
    ]

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_rejects_unknown_offer_id(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "999999",
        },
    )

    assert response.status_code == 302

    assert _stored_messages(
        response
    ) == [
        "business offer is not currently available"
    ]

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_rejects_retail_price(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    retail_price = commercial_price_factory(
        product=product,
        channel=CommercialPrice.Channel.RETAIL,
        enabled=True,
    )

    price_amount_factory(
        commercial_price=retail_price,
        price=Decimal("12.50"),
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": str(
                retail_price.pk
            ),
        },
    )

    assert response.status_code == 302

    assert _stored_messages(
        response
    ) == [
        "business offer is not currently available"
    ]

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_rejects_disabled_business_price(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    disabled_price = _business_price(
        product=product,
        enabled=False,
        price="12.50",
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": str(
                disabled_price.pk
            ),
        },
    )

    assert response.status_code == 302

    assert _stored_messages(
        response
    ) == [
        "business offer is not currently available"
    ]

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_rejects_offer_for_other_product(
    client,
):
    customer = _login_customer(
        client=client,
    )

    route_product = product_factory(
        name="Apple",
    )

    other_product = product_factory(
        name="Banana",
    )

    other_offer = standard_business_offer_factory(
        product=other_product,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": route_product.id,
            },
        ),
        {
            "commercial_price_id": str(
                other_offer.pk
            ),
        },
    )

    assert response.status_code == 302

    assert _stored_messages(
        response
    ) == [
        "business offer is not currently available"
    ]

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_rejects_batch_offer_without_eur_price(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    batch = batch_factory(
        product=product,
        today=TODAY,
        quantity=10,
    )

    offer = commercial_price_factory(
        product=product,
        batch=batch,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=True,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": str(
                offer.pk
            ),
        },
    )

    assert response.status_code == 302

    assert _stored_messages(
        response
    ) == [
        "business offer is not currently available"
    ]

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_returns_json_success(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        brand="Generic",
        name="Apple",
        weight_per_unit=5000,
    )

    standard_offer = standard_business_offer_factory(
        product=product,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "",
            "quantity": "3",
        },
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200

    assert response.json() == {
        "ok": True,
        "message": "Generic — Apple added to your cart.",
    }

    line = _customer_cart_line(
        customer=customer,
    )

    assert line.commercial_price == standard_offer
    assert line.quantity == 3


@pytest.mark.django_db
def test_catalog_add_product_returns_json_error_for_invalid_offer(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "abc",
        },
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 400
    assert response.json() == {
        "ok": False,
        "message": "invalid business offer",
    }

    _assert_no_business_cart(
        customer=customer,
    )


@pytest.mark.django_db
def test_catalog_add_product_shows_success_message(
    client,
):
    _login_customer(
        client=client,
    )

    product = product_factory(
        brand="Generic",
        name="Apple",
        weight_per_unit=5000,
    )

    standard_business_offer_factory(
        product=product,
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "",
            "quantity": "2",
        },
    )

    assert _stored_messages(
        response
    ) == [
        "Generic — Apple added to your cart."
    ]


@pytest.mark.django_db
def test_catalog_add_product_rejects_inactive_product(
    client,
):
    customer = _login_customer(
        client=client,
    )

    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

    product.active = False
    product.save(
        update_fields=[
            "active",
            "updated_at",
        ],
    )

    response = client.post(
        reverse(
            "business_portal:catalog_add_product",
            kwargs={
                "product_id": product.id,
            },
        ),
        {
            "commercial_price_id": "",
            "quantity": "2",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse(
        "business_portal:catalog"
    )

    assert _stored_messages(
        response
    ) == [
        "business offer is not currently available"
    ]

    _assert_no_business_cart(
        customer=customer,
    )

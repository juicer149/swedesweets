from __future__ import annotations

import pytest
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
from customers.tests.factories import (
    customer_factory,
)
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from products.tests.factories import (
    product_factory,
)

pytestmark = pytest.mark.usefixtures("fast_password_hashing")


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
    quantity: int = 3,
):
    product = product_factory(
        name="Apple",
        weight_per_unit=5000,
    )

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
def test_cart_does_not_create_empty_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    response = client.get(
        reverse(
            "business_portal:cart"
        )
    )

    assert response.status_code == 200
    assert response.context["cart_lines"] == ()

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_cart_reads_customer_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    line = _create_cart_line(
        customer=customer,
        quantity=3,
    )

    response = client.get(
        reverse(
            "business_portal:cart"
        )
    )

    assert response.status_code == 200

    cart_lines = response.context[
        "cart_lines"
    ]

    assert len(cart_lines) == 1

    presented_line = cart_lines[0]

    assert presented_line.cart_line_id == line.id
    assert presented_line.quantity == 3

    assert presented_line.quantity_url == reverse(
        "business_portal:set_cart_line_quantity",
        kwargs={
            "cart_line_id": line.id,
        },
    )

    assert presented_line.remove_url == reverse(
        "business_portal:remove_cart_line",
        kwargs={
            "cart_line_id": line.id,
        },
    )

    product_url = reverse(
        "business_portal:catalog_product",
        kwargs={
            "product_id": line.commercial_price.product_id,
        },
    )

    assert presented_line.product_url == product_url
    assert presented_line.image_url is None
    assert f'href="{product_url}"' in response.content.decode()


@pytest.mark.django_db
def test_cart_does_not_show_another_customers_cart(
    client,
):
    customer = _login_customer(
        client=client,
    )

    other_customer = customer_factory(
        name="Other Customer",
        email="other@example.com",
    )

    _create_cart_line(
        customer=other_customer,
    )

    response = client.get(
        reverse(
            "business_portal:cart"
        )
    )

    assert response.status_code == 200
    assert response.context["cart_lines"] == ()

    assert not BusinessCart.objects.filter(
        customer=customer,
    ).exists()


@pytest.mark.django_db
def test_cart_line_action_forms_use_the_presented_urls(client):
    customer = _login_customer(client=client)
    line = _create_cart_line(customer=customer, quantity=3)

    response = client.get(reverse("business_portal:cart"))

    assert response.status_code == 200
    (presented_line,) = response.context["cart_lines"]
    html = response.content.decode()

    assert f'action="{presented_line.quantity_url}"' in html
    assert f'action="{presented_line.remove_url}"' in html
    assert f'data-cart-line-id="{line.id}"' in html


@pytest.mark.django_db
def test_cart_review_lists_lines_with_quantity_and_actions(
    client,
):
    customer = _login_customer(
        client=client,
    )

    _create_cart_line(
        customer=customer,
        quantity=3,
    )

    response = client.get(
        reverse(
            "business_portal:cart_review"
        )
    )

    assert response.status_code == 200

    (review_line,) = response.context["lines"]

    assert review_line.quantity == 3
    assert review_line.image_url is None

    content = response.content.decode()

    assert response.context["navbar_cart_locked"] is True
    assert 'data-order-progress="review"' in content
    assert content.count('class="order-progress__step is-lit"') == 2
    assert 'aria-disabled="true" tabindex="-1" inert' in content
    assert 'value="place_order"' in content
    assert 'value="clear_cart"' in content
    assert f'href="{reverse("business_portal:cart")}"' in content


@pytest.mark.django_db
def test_cart_remove_form_carries_the_csrf_token(
    client,
):
    customer = _login_customer(
        client=client,
    )

    line = _create_cart_line(
        customer=customer,
    )

    html = client.get(
        reverse("business_portal:cart")
    ).content.decode()
    remove_url = reverse(
        "business_portal:remove_cart_line",
        kwargs={"cart_line_id": line.id},
    )
    form = html[html.index(f'action="{remove_url}"'):]

    assert 'name="csrfmiddlewaretoken"' in form[: form.index("</form>")]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "route", ["business_portal:cart", "business_portal:cart_review"]
)
def test_clear_cart_redirects_to_catalog_with_a_local_confirmation(client, route):
    customer = _login_customer(client=client)
    _create_cart_line(customer=customer)
    cart_html = client.get(reverse(route)).content.decode()
    assert 'data-confirm="Remove all products from your cart?"' in cart_html
    assert "js/confirm_action." in cart_html
    response = client.post(reverse(route), {"intent": "clear_cart"})
    assert response.status_code == 302
    assert response.url == reverse("business_portal:catalog")
    assert not BusinessCart.objects.get(customer=customer).cart.lines.exists()
    landing = client.get(response.url, follow=True)
    html = landing.content.decode()
    assert 'class="cart-notice" data-cart-notice role="status"' in html
    assert "Cart cleared." in html
    assert 'class="message message--success"' not in html


@pytest.mark.django_db
def test_placed_destination_has_no_duplicate_success_banner(client):
    customer = _login_customer(client=client)
    line = _create_cart_line(customer=customer, quantity=1)
    batch_factory(product=line.commercial_price.product, today=TODAY, quantity=10)
    response = client.post(
        reverse("business_portal:cart_review"), {"intent": "place_order"},
        follow=True,
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert 'data-order-progress="placed"' in html
    assert 'class="message message--success"' not in html

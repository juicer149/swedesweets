from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from carts.models import Cart
from carts.services import create_cart
from common.channels import SalesChannel
from inventory.errors import InsufficientStockError
from inventory.services import create_batch
from orders.models import Order
from payments.contracts import HostedPaymentError
from retail.models import RetailCheckoutSession
from retail.payments import (
    RetailPaymentRecovery,
    RetailPaymentRecoveryAction,
    RetailPaymentRedirect,
)
from retail.services import (
    add_retail_cart_line,
    fail_retail_payment,
    start_retail_payment,
)
from retail.tests.factories import (
    retail_postal_area_factory,
    retail_product_price_factory,
)
from storefront.cart import (
    COOKIE_NAME,
    COOKIE_SALT,
)
from storefront.checkout_session import CHECKOUT_IDS_SESSION_KEY


def _set_signed_retail_cart_cookie(
    client,
    *,
    cart: Cart,
) -> None:
    response = HttpResponse()

    response.set_signed_cookie(
        COOKIE_NAME,
        str(cart.id),
        salt=COOKIE_SALT,
    )

    client.cookies[COOKIE_NAME] = (
        response.cookies[COOKIE_NAME].value
    )


def _details(**overrides: str) -> dict[str, str]:
    return {
        "first_name": "Marie",
        "last_name": "Dupont",
        "email": "marie@example.com",
        "phone_number": "+33612345678",
        "address_line": "10 Rue de Test",
        "postal_code": "74000",
        "city": "Annecy",
    } | overrides


@pytest.fixture
def cart(client, db):
    retail_postal_area_factory()

    offer = retail_product_price_factory(
        enabled=True,
        price=Decimal("10.00"),
    )
    create_batch(
        batch_id="CHECKOUT-001",
        product=offer.product,
        quantity=10,
        best_before=timezone.localdate() + timedelta(days=60),
        location="Shelf A1",
    )

    cart = create_cart(
        channel=SalesChannel.RETAIL,
    )
    add_retail_cart_line(
        cart=cart,
        commercial_price_id=offer.pk,
        quantity=2,
    )

    _set_signed_retail_cart_cookie(
        client,
        cart=cart,
    )

    return cart


def _submit_details(client, **overrides: str):
    return client.post(
        reverse("storefront:checkout"),
        _details(**overrides),
    )


@pytest.mark.django_db
def test_checkout_without_cart_redirects_to_cart(client):
    response = client.get(
        reverse("storefront:checkout")
    )

    assert response.status_code == 302
    assert response.url == reverse("storefront:cart")


@pytest.mark.django_db
def test_checkout_form_renders_with_cart_summary(client, cart):
    response = client.get(
        reverse("storefront:checkout")
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert 'name="first_name"' in content
    assert "€20.00" in content


@pytest.mark.django_db
def test_valid_details_create_checkout_and_keep_cart(client, cart):
    response = _submit_details(client)

    checkout = RetailCheckoutSession.objects.get()

    assert response.status_code == 302
    assert response.url == reverse(
        "storefront:checkout_review",
        kwargs={
            "checkout_id": checkout.pk,
        },
    )
    assert checkout.order.status == Order.Status.DRAFT
    assert checkout.order.buyer_name_snapshot == "Marie Dupont"
    assert checkout.cart_id == cart.pk
    assert Cart.objects.filter(pk=cart.pk).exists()
    assert str(checkout.pk) in client.session[CHECKOUT_IDS_SESSION_KEY]


@pytest.mark.django_db
def test_unsupported_destination_is_a_field_error(client, cart):
    response = _submit_details(
        client,
        postal_code="75001",
        city="Paris",
    )

    assert response.status_code == 200
    assert response.context["form"].has_error("postal_code")
    assert not RetailCheckoutSession.objects.exists()


@pytest.mark.django_db
def test_review_shows_order_to_owning_session(client, cart):
    _submit_details(client)
    checkout = RetailCheckoutSession.objects.get()

    response = client.get(
        reverse(
            "storefront:checkout_review",
            kwargs={
                "checkout_id": checkout.pk,
            },
        )
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert "Marie Dupont" in content
    assert "€20.00" in content
    assert response.context["lines"][0].image_url is None


@pytest.mark.django_db
def test_review_is_hidden_from_other_sessions(client, cart):
    _submit_details(client)
    checkout = RetailCheckoutSession.objects.get()

    response = Client().get(
        reverse(
            "storefront:checkout_review",
            kwargs={
                "checkout_id": checkout.pk,
            },
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_resubmitting_details_replaces_unpaid_checkout(client, cart):
    _submit_details(client)
    first = RetailCheckoutSession.objects.get()

    response = _submit_details(
        client,
        first_name="Anne",
    )

    second = RetailCheckoutSession.objects.exclude(pk=first.pk).get()
    first.order.refresh_from_db()

    assert first.order.status == Order.Status.CANCELLED
    assert response.url == reverse(
        "storefront:checkout_review",
        kwargs={
            "checkout_id": second.pk,
        },
    )


@pytest.mark.django_db
def test_payment_in_progress_redirects_to_existing_checkout(client, cart):
    _submit_details(client)
    checkout = RetailCheckoutSession.objects.get()

    start_retail_payment(
        checkout=checkout,
    )

    response = _submit_details(client)

    assert response.status_code == 302
    assert response.url == reverse(
        "storefront:checkout_review",
        kwargs={
            "checkout_id": checkout.pk,
        },
    )
    assert RetailCheckoutSession.objects.count() == 1


@pytest.mark.django_db
def test_details_form_is_prefilled_from_session(client, cart):
    _submit_details(client)

    response = client.get(
        reverse("storefront:checkout")
    )

    assert response.context["form"].initial["email"] == "marie@example.com"


@pytest.mark.django_db
def test_cart_page_links_to_checkout(client, cart):
    response = client.get(
        reverse("storefront:cart")
    )

    assert reverse("storefront:checkout") in response.content.decode()


def _created_checkout(client) -> RetailCheckoutSession:
    _submit_details(client)

    return RetailCheckoutSession.objects.get()


def _pay_url(checkout: RetailCheckoutSession) -> str:
    return reverse(
        "storefront:checkout_pay",
        kwargs={
            "checkout_id": checkout.pk,
        },
    )


def _review_url(checkout: RetailCheckoutSession) -> str:
    return reverse(
        "storefront:checkout_review",
        kwargs={
            "checkout_id": checkout.pk,
        },
    )


def _return_url(checkout: RetailCheckoutSession) -> str:
    return reverse(
        "storefront:payment_return",
        kwargs={
            "checkout_id": checkout.pk,
        },
    )


@pytest.mark.django_db
def test_review_shows_pay_button(client, cart):
    checkout = _created_checkout(client)

    response = client.get(
        _review_url(checkout)
    )

    assert _pay_url(checkout) in response.content.decode()


@pytest.mark.django_db
def test_pay_requires_owning_session(client, cart):
    checkout = _created_checkout(client)

    response = Client().post(
        _pay_url(checkout)
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_pay_redirects_to_hosted_checkout(client, cart, monkeypatch):
    checkout = _created_checkout(client)
    calls = []

    def fake_begin(**kwargs):
        calls.append(kwargs)

        return RetailPaymentRedirect(
            attempt=None,
            redirect_url="https://pay.example/123",
        )

    monkeypatch.setattr(
        "storefront.checkout_views.begin_retail_hosted_payment",
        fake_begin,
    )

    response = client.post(
        _pay_url(checkout)
    )

    assert response.status_code == 302
    assert response.url == "https://pay.example/123"
    assert calls[0]["customer_return_url"] == (
        "http://testserver" + _return_url(checkout)
    )
    assert calls[0]["webhook_url"].endswith(
        reverse("payments:sumup_webhook")
    )


@pytest.mark.django_db
def test_pay_with_started_provider_payment_resumes_it(client, cart):
    checkout = _created_checkout(client)

    attempt = start_retail_payment(
        checkout=checkout,
    )
    attempt.provider_payment_id = "sumup-existing"
    attempt.save(
        update_fields=[
            "provider_payment_id",
        ]
    )

    response = client.post(
        _pay_url(checkout)
    )

    assert response.status_code == 302
    assert response.url == _return_url(checkout)


@pytest.mark.django_db
def test_pay_with_pending_attempt_without_provider_id_never_retries(
    client,
    cart,
    monkeypatch,
):
    checkout = _created_checkout(client)
    start_retail_payment(
        checkout=checkout,
    )

    def fail_if_called(**kwargs):
        raise AssertionError("must not start another external payment")

    monkeypatch.setattr(
        "storefront.checkout_views.begin_retail_hosted_payment",
        fail_if_called,
    )

    response = client.post(
        _pay_url(checkout)
    )

    assert response.status_code == 302
    assert response.url == _return_url(checkout)


@pytest.mark.django_db
def test_provider_error_after_attempt_goes_to_payment_return(
    client,
    cart,
    monkeypatch,
):
    checkout = _created_checkout(client)

    def fake_begin(**kwargs):
        start_retail_payment(
            checkout=kwargs["checkout"],
        )

        raise HostedPaymentError("connection reset")

    monkeypatch.setattr(
        "storefront.checkout_views.begin_retail_hosted_payment",
        fake_begin,
    )

    response = client.post(
        _pay_url(checkout)
    )

    assert response.status_code == 302
    assert response.url == _return_url(checkout)


@pytest.mark.django_db
def test_provider_error_without_attempt_returns_to_review(
    client,
    cart,
    monkeypatch,
):
    checkout = _created_checkout(client)

    def fake_begin(**kwargs):
        raise HostedPaymentError("provider not configured")

    monkeypatch.setattr(
        "storefront.checkout_views.begin_retail_hosted_payment",
        fake_begin,
    )

    response = client.post(
        _pay_url(checkout)
    )

    assert response.url == _review_url(checkout)


@pytest.mark.django_db
def test_programming_errors_are_not_reported_as_provider_errors(
    client,
    cart,
    monkeypatch,
):
    checkout = _created_checkout(client)

    def fake_begin(**kwargs):
        raise AttributeError("bug")

    monkeypatch.setattr(
        "storefront.checkout_views.begin_retail_hosted_payment",
        fake_begin,
    )

    with pytest.raises(AttributeError):
        client.post(
            _pay_url(checkout)
        )


@pytest.mark.django_db
def test_pay_out_of_stock_sends_buyer_to_cart(client, cart, monkeypatch):
    checkout = _created_checkout(client)

    def fake_begin(**kwargs):
        raise InsufficientStockError(
            product_name="Test",
            requested_quantity=2,
            available_quantity=0,
            missing_quantity=2,
        )

    monkeypatch.setattr(
        "storefront.checkout_views.begin_retail_hosted_payment",
        fake_begin,
    )

    response = client.post(
        _pay_url(checkout)
    )

    assert response.url == reverse("storefront:cart")



@pytest.mark.django_db
def test_failed_payment_offers_retry_to_owning_session(
    client,
    cart,
    monkeypatch,
):
    checkout = _created_checkout(client)
    start_retail_payment(
        checkout=checkout,
    )

    def fake_recover(*, attempt):
        return RetailPaymentRecovery(
            attempt=attempt,
            action=RetailPaymentRecoveryAction.PAYMENT_FAILED,
        )

    monkeypatch.setattr(
        "storefront.views.recover_retail_payment",
        fake_recover,
    )

    own = client.get(
        _return_url(checkout)
    )
    other = Client().get(
        _return_url(checkout)
    )

    assert own.context["retry_url"] == _pay_url(checkout)
    assert other.context["retry_url"] is None


@pytest.mark.django_db
def test_provider_error_without_new_attempt_ignores_old_failed_attempt(
    client,
    cart,
    monkeypatch,
):
    checkout = _created_checkout(client)

    old_attempt = start_retail_payment(
        checkout=checkout,
    )
    fail_retail_payment(
        attempt=old_attempt,
    )

    def fake_begin(**kwargs):
        raise HostedPaymentError(
            "provider not configured"
        )

    monkeypatch.setattr(
        "storefront.checkout_views.begin_retail_hosted_payment",
        fake_begin,
    )

    response = client.post(
        _pay_url(checkout)
    )

    assert response.url == _review_url(checkout)


@pytest.mark.django_db
def test_city_lookup_returns_towns_for_postal_code(client, db):
    retail_postal_area_factory(
        postal_code="74400",
        city="Chamonix-Mont-Blanc",
    )

    response = client.get(
        reverse("storefront:checkout_cities"),
        {
            "postal_code": "74400",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "cities": ["Chamonix-Mont-Blanc"],
    }


@pytest.mark.django_db
def test_city_lookup_returns_empty_list_for_unknown_postal_code(client, db):
    response = client.get(
        reverse("storefront:checkout_cities"),
        {
            "postal_code": "75001",
        },
    )

    assert response.json() == {
        "cities": [],
    }


@pytest.mark.django_db
def test_details_store_official_town_spelling(client, cart):
    _submit_details(
        client,
        city="ANNECY",
    )

    checkout = RetailCheckoutSession.objects.get()

    assert checkout.order.buyer_city_snapshot == "Annecy"


@pytest.mark.django_db
def test_wrong_town_for_known_postal_code_is_a_city_error(client, cart):
    response = _submit_details(
        client,
        city="Chamonix",
    )

    form = response.context["form"]

    assert form.has_error("city")
    assert not form.has_error("postal_code")
    assert "Annecy" in str(form.errors["city"])


@pytest.mark.django_db
def test_unconfigured_provider_leaves_no_pending_attempt(
    client,
    cart,
    settings,
):
    settings.PAYMENT_PROVIDER = "sumup"
    settings.SUMUP_API_KEY = ""
    settings.SUMUP_MERCHANT_CODE = ""

    checkout = _created_checkout(client)

    response = client.post(
        _pay_url(checkout)
    )

    assert response.url == _review_url(checkout)
    assert not checkout.order.payment_attempts.exists()
    assert not checkout.order.allocations.exists()

    retry = _submit_details(client)

    assert retry.status_code == 302
    assert "payment in progress" not in str(
        list(retry.wsgi_request._messages)
    )


def _pay_with_fake_provider(client, checkout, outcome: str):
    pay = client.post(
        _pay_url(checkout)
    )

    assert pay.status_code == 302
    assert pay.url.startswith("/payments/fake/")
    assert client.get(pay.url).status_code == 200

    back = client.post(
        pay.url,
        {
            "outcome": outcome,
        },
    )

    assert back.url == "http://testserver" + _return_url(checkout)

    return client.get(
        _return_url(checkout)
    )


@pytest.mark.django_db
def test_fake_payment_success_places_order_and_consumes_cart(
    client,
    cart,
    settings,
):
    settings.PAYMENT_PROVIDER = "fake"
    checkout = _created_checkout(client)

    result = _pay_with_fake_provider(
        client,
        checkout,
        "pay",
    )

    checkout.order.refresh_from_db()

    assert result.context["result"] == "confirmed"
    assert checkout.order.status == Order.Status.PLACED
    assert not Cart.objects.filter(pk=cart.pk).exists()


@pytest.mark.django_db
def test_fake_payment_decline_keeps_cart_and_offers_retry(
    client,
    cart,
    settings,
):
    settings.PAYMENT_PROVIDER = "fake"
    checkout = _created_checkout(client)

    result = _pay_with_fake_provider(
        client,
        checkout,
        "decline",
    )

    checkout.order.refresh_from_db()

    assert result.context["result"] == "failed"
    assert result.context["retry_url"] == _pay_url(checkout)
    assert checkout.order.status == Order.Status.DRAFT
    assert Cart.objects.filter(pk=cart.pk).exists()


@pytest.mark.django_db
def test_fake_checkout_page_is_hidden_when_provider_is_sumup(
    client,
    settings,
):
    settings.PAYMENT_PROVIDER = "sumup"

    response = client.get(
        reverse(
            "payments:fake_checkout",
            kwargs={
                "payment_id": "fake-anything",
            },
        )
    )

    assert response.status_code == 404


def _cancel_payment_url(checkout: RetailCheckoutSession) -> str:
    return reverse(
        "storefront:checkout_cancel_payment",
        kwargs={
            "checkout_id": checkout.pk,
        },
    )


@pytest.mark.django_db
def test_buyer_can_cancel_open_payment_and_check_out_again(
    client,
    cart,
    settings,
):
    settings.PAYMENT_PROVIDER = "fake"
    checkout = _created_checkout(client)

    client.post(
        _pay_url(checkout)
    )

    review = client.get(
        _review_url(checkout)
    )

    assert review.context["has_open_payment"] is True
    assert _cancel_payment_url(checkout) in review.content.decode()

    cancel = client.post(
        _cancel_payment_url(checkout)
    )

    assert cancel.url == reverse("storefront:cart")

    again = _submit_details(client)
    new_checkout = RetailCheckoutSession.objects.exclude(pk=checkout.pk).get()

    assert again.url == _review_url(new_checkout)





def _open_payment(client) -> RetailCheckoutSession:
    checkout = _created_checkout(client)

    start_retail_payment(
        checkout=checkout,
    )

    return checkout


def _quantity_url(line) -> str:
    return reverse(
        "storefront:set_cart_line_quantity",
        kwargs={
            "cart_line_id": line.pk,
        },
    )


@pytest.mark.django_db
def test_cart_page_is_read_only_while_payment_is_open(client, cart):
    checkout = _open_payment(client)

    response = client.get(
        reverse("storefront:cart")
    )
    content = response.content.decode()

    assert response.context["open_payment_url"] == _review_url(checkout)
    assert response.context["checkout_url"] is None
    assert "data-current-order-quantity-form" not in content
    assert 'value="clear_cart"' not in content


@pytest.mark.django_db
def test_quantity_change_is_refused_while_payment_is_open(client, cart):
    _open_payment(client)
    line = cart.lines.get()

    response = client.post(
        _quantity_url(line),
        {
            "quantity": "1",
        },
        HTTP_ACCEPT="application/json",
    )

    line.refresh_from_db()

    assert response.status_code == 409
    assert response.json()["ok"] is False
    assert line.quantity == 2


@pytest.mark.django_db
def test_line_removal_is_refused_while_payment_is_open(client, cart):
    _open_payment(client)
    line = cart.lines.get()

    client.post(
        reverse(
            "storefront:remove_cart_line",
            kwargs={
                "cart_line_id": line.pk,
            },
        )
    )

    assert cart.lines.filter(pk=line.pk).exists()


@pytest.mark.django_db
def test_clearing_cart_is_refused_while_payment_is_open(client, cart):
    _open_payment(client)

    client.post(
        reverse("storefront:cart"),
        {
            "intent": "clear_cart",
        },
    )

    assert cart.lines.exists()


@pytest.mark.django_db
def test_adding_to_cart_is_refused_while_payment_is_open(client, cart):
    _open_payment(client)
    line = cart.lines.select_related("commercial_price").get()

    response = client.post(
        reverse(
            "storefront:add_to_cart",
            kwargs={
                "product_id": line.commercial_price.product_id,
            },
        ),
        {
            "commercial_price_id": str(line.commercial_price_id),
            "quantity": "1",
        },
        HTTP_ACCEPT="application/json",
    )

    line.refresh_from_db()

    assert response.status_code == 400
    assert line.quantity == 2
    assert cart.lines.count() == 1


@pytest.mark.django_db
def test_checkout_page_sends_open_payment_to_review(client, cart):
    checkout = _open_payment(client)

    response = client.get(
        reverse("storefront:checkout")
    )

    assert response.status_code == 302
    assert response.url == _review_url(checkout)


@pytest.mark.django_db
def test_cart_is_editable_again_after_cancelling_payment(
    client,
    cart,
    settings,
):
    settings.PAYMENT_PROVIDER = "fake"
    checkout = _created_checkout(client)

    client.post(
        _pay_url(checkout)
    )
    client.post(
        _cancel_payment_url(checkout)
    )

    line = cart.lines.get()
    response = client.post(
        _quantity_url(line),
        {
            "quantity": "1",
        },
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 1

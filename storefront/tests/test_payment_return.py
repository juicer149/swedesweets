from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from orders.models import Order
from orders.tests.factories import order_line_factory
from payments.models import PaymentAttempt
from products.tests.factories import product_factory
from retail.models import RetailCheckoutSession
from retail.payments import (
    RetailPaymentRecovery,
    RetailPaymentRecoveryAction,
)
from retail.rules import RETAIL_CHECKOUT_WINDOW
from storefront.checkout_session import CHECKOUT_IDS_SESSION_KEY


@pytest.fixture
def payment_return_attempt():
    from django.utils import timezone

    order = Order.objects.create(
        channel=Order.Channel.RETAIL,
        currency=Order.Currency.EUR,
        status=Order.Status.DRAFT,
    )

    checkout = RetailCheckoutSession.objects.create(
        order=order,
        expires_at=(
            timezone.now()
            + RETAIL_CHECKOUT_WINDOW
        ),
    )

    attempt = PaymentAttempt.objects.create(
        order=order,
        status=PaymentAttempt.Status.PENDING,
        provider=PaymentAttempt.Provider.SUMUP,
        provider_payment_id="sumup-return-test",
        amount=Decimal("25.00"),
        currency="EUR",
    )

    return checkout, attempt


@pytest.mark.django_db
def test_payment_return_is_public_and_shows_confirmation(
    client,
    monkeypatch,
    payment_return_attempt,
):
    checkout, attempt = payment_return_attempt

    def fake_recover_retail_payment(
        *,
        attempt: PaymentAttempt,
    ) -> RetailPaymentRecovery:
        return RetailPaymentRecovery(
            attempt=attempt,
            action=RetailPaymentRecoveryAction.CONFIRMED,
        )

    monkeypatch.setattr(
        "storefront.views.recover_retail_payment",
        fake_recover_retail_payment,
    )

    response = client.get(
        reverse(
            "storefront:payment_return",
            kwargs={
                "checkout_id": checkout.pk,
            },
        )
    )

    assert response.status_code == 200
    assert response.context["result"] == "confirmed"
    assert response.context["navbar_cart_locked"] is True
    assert response.context["navbar_cart_current"] is True
    assert response.context["navbar_account_current"] is False
    html = response.content.decode()
    assert 'data-order-progress="placed"' in html
    assert html.count('class="order-progress__step is-lit"') == 3
    assert 'class="crown-hero"' in response.content.decode()


@pytest.mark.django_db
def test_payment_return_redirects_to_existing_hosted_checkout(
    client,
    monkeypatch,
    payment_return_attempt,
):
    checkout, attempt = payment_return_attempt

    def fake_recover_retail_payment(
        *,
        attempt: PaymentAttempt,
    ) -> RetailPaymentRecovery:
        return RetailPaymentRecovery(
            attempt=attempt,
            action=RetailPaymentRecoveryAction.CONTINUE_PAYMENT,
            redirect_url="https://checkout.sumup.test/resume",
        )

    monkeypatch.setattr(
        "storefront.views.recover_retail_payment",
        fake_recover_retail_payment,
    )

    response = client.get(
        reverse(
            "storefront:payment_return",
            kwargs={
                "checkout_id": checkout.pk,
            },
        )
    )

    assert response.status_code == 302
    assert response.url == (
        "https://checkout.sumup.test/resume"
    )


@pytest.mark.django_db
def test_payment_return_shows_failed_state(
    client,
    monkeypatch,
    payment_return_attempt,
):
    checkout, attempt = payment_return_attempt

    def fake_recover_retail_payment(
        *,
        attempt: PaymentAttempt,
    ) -> RetailPaymentRecovery:
        return RetailPaymentRecovery(
            attempt=attempt,
            action=RetailPaymentRecoveryAction.PAYMENT_FAILED,
        )

    monkeypatch.setattr(
        "storefront.views.recover_retail_payment",
        fake_recover_retail_payment,
    )

    response = client.get(
        reverse(
            "storefront:payment_return",
            kwargs={
                "checkout_id": checkout.pk,
            },
        )
    )

    assert response.status_code == 200
    assert response.context["result"] == "failed"
    html = response.content.decode()
    assert 'data-order-progress="review"' in html
    assert 'data-order-progress="placed"' not in html


@pytest.mark.django_db
def test_payment_return_shows_support_state(
    client,
    monkeypatch,
    payment_return_attempt,
):
    checkout, attempt = payment_return_attempt

    def fake_recover_retail_payment(
        *,
        attempt: PaymentAttempt,
    ) -> RetailPaymentRecovery:
        return RetailPaymentRecovery(
            attempt=attempt,
            action=RetailPaymentRecoveryAction.NEEDS_SUPPORT,
        )

    monkeypatch.setattr(
        "storefront.views.recover_retail_payment",
        fake_recover_retail_payment,
    )

    response = client.get(
        reverse(
            "storefront:payment_return",
            kwargs={
                "checkout_id": checkout.pk,
            },
        )
    )

    assert response.status_code == 200
    assert response.context["result"] == "support"


@pytest.mark.django_db
def test_payment_return_returns_not_found_for_unknown_checkout(
    client,
):
    import uuid

    response = client.get(
        reverse(
            "storefront:payment_return",
            kwargs={
                "checkout_id": uuid.uuid4(),
            },
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_payment_return_returns_not_found_when_checkout_has_no_payment_attempt(
    client,
):
    from django.utils import timezone

    order = Order.objects.create(
        channel=Order.Channel.RETAIL,
        currency=Order.Currency.EUR,
        status=Order.Status.DRAFT,
    )

    checkout = RetailCheckoutSession.objects.create(
        order=order,
        expires_at=(
            timezone.now()
            + RETAIL_CHECKOUT_WINDOW
        ),
    )

    response = client.get(
        reverse(
            "storefront:payment_return",
            kwargs={
                "checkout_id": checkout.pk,
            },
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("owner,action,shows_receipt", [
    (True, RetailPaymentRecoveryAction.CONFIRMED, True),
    (False, RetailPaymentRecoveryAction.CONFIRMED, False),
    (True, RetailPaymentRecoveryAction.PAYMENT_FAILED, False),
    (True, RetailPaymentRecoveryAction.NEEDS_SUPPORT, False),
])
def test_receipt_requires_confirmed_payment_and_owning_session(
    client, monkeypatch, payment_return_attempt, owner, action, shows_receipt
):
    checkout, attempt = payment_return_attempt
    order = checkout.order
    order.buyer_name_snapshot = "Private Buyer"
    order.buyer_email_snapshot = "private@example.com"
    order.buyer_phone_snapshot = "+33612345678"
    order.buyer_address_line_snapshot = "12 Private Street"
    order.buyer_postal_code_snapshot = "74400"
    order.buyer_city_snapshot = "Chamonix-Mont-Blanc"
    order.save()
    product = product_factory(name="Renamed sweets")
    line = order_line_factory(
        order=order, product=product, quantity=2,
        unit_price_snapshot=Decimal("12.50"),
    )
    line.name_snapshot = "Bought sweets — 200 g"
    line.save(update_fields=["name_snapshot"])
    if owner:
        session = client.session
        session[CHECKOUT_IDS_SESSION_KEY] = [str(checkout.pk)]
        session.save()
    monkeypatch.setattr(
        "storefront.views.recover_retail_payment",
        lambda **kwargs: RetailPaymentRecovery(attempt=attempt, action=action),
    )
    response = client.get(reverse(
        "storefront:payment_return", kwargs={"checkout_id": checkout.pk}
    ))
    assert response.status_code == 200
    html = response.content.decode()
    assert ('class="payment-confirmation"' in html) is shows_receipt
    for private_value in [
        "Private Buyer", "private@example.com", "12 Private Street",
        "Bought sweets — 200 g",
    ]:
        assert (private_value in html) is shows_receipt
    if shows_receipt:
        assert "€25.00" in html
        assert "2 × €12.50" in html
        assert "Renamed sweets" not in html

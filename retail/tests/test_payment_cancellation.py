from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from inventory.services import create_batch
from orders.models import Order
from payments.contracts import HostedPaymentRequest
from payments.models import PaymentAttempt
from payments.providers.fake import (
    FakeHostedPaymentProvider,
    complete_fake_payment,
)
from payments.services import payment_reference
from reservations.models import Allocation
from retail.payments import (
    RetailPaymentRecoveryAction,
    begin_retail_hosted_payment,
    cancel_open_retail_payment,
    recover_retail_payment,
    resolve_unconfirmed_retail_payment,
)
from retail.services import (
    AnonymousBuyerInput,
    RetailOrderLineInput,
    create_pending_retail_order,
    start_retail_payment,
)
from retail.tests.factories import (
    retail_buyer_data,
    retail_postal_area_factory,
    retail_product_price_factory,
)


@pytest.fixture
def fake_provider(settings):
    settings.PAYMENT_PROVIDER = "fake"


@pytest.fixture
def checkout(db):
    retail_postal_area_factory()

    offer = retail_product_price_factory(
        enabled=True,
        price=Decimal("12.50"),
    )
    create_batch(
        batch_id="CANCEL-001",
        product=offer.product,
        quantity=10,
        best_before=timezone.localdate() + timedelta(days=60),
        location="Shelf A1",
    )

    return create_pending_retail_order(
        buyer=AnonymousBuyerInput(
            **retail_buyer_data()
        ),
        lines=[
            RetailOrderLineInput(
                commercial_price_id=offer.pk,
                quantity=2,
            ),
        ],
    )


def _begin(checkout) -> PaymentAttempt:
    return begin_retail_hosted_payment(
        checkout=checkout,
        customer_return_url="http://testserver/return/",
        webhook_url="http://testserver/webhook/",
    ).attempt


@pytest.mark.django_db
def test_cancelling_open_payment_releases_reservations(fake_provider, checkout):
    attempt = _begin(checkout)

    recovery = cancel_open_retail_payment(
        attempt=attempt,
    )

    attempt.refresh_from_db()
    checkout.order.refresh_from_db()

    assert recovery.action == RetailPaymentRecoveryAction.PAYMENT_CANCELLED
    assert attempt.status in {
        PaymentAttempt.Status.FAILED,
        PaymentAttempt.Status.CANCELLED,
    }
    assert checkout.order.status == Order.Status.DRAFT
    assert not checkout.order.allocations.filter(
        status=Allocation.Status.RESERVED,
    ).exists()


@pytest.mark.django_db
def test_cancelling_after_buyer_paid_places_the_order(fake_provider, checkout):
    attempt = _begin(checkout)
    complete_fake_payment(
        attempt.provider_payment_id,
        succeeded=True,
    )

    recovery = cancel_open_retail_payment(
        attempt=attempt,
    )

    checkout.order.refresh_from_db()

    assert recovery.action == RetailPaymentRecoveryAction.CONFIRMED
    assert checkout.order.status == Order.Status.PLACED


@pytest.mark.django_db
def test_unconfirmed_attempt_without_external_payment_is_cancelled(checkout):
    attempt = start_retail_payment(
        checkout=checkout,
    )

    resolved = resolve_unconfirmed_retail_payment(
        attempt=attempt,
        provider=FakeHostedPaymentProvider(),
    )

    assert resolved.status == PaymentAttempt.Status.CANCELLED


@pytest.mark.django_db
def test_unconfirmed_attempt_is_linked_to_existing_external_payment(checkout):
    provider = FakeHostedPaymentProvider()
    attempt = start_retail_payment(
        checkout=checkout,
    )

    # The provider created the payment, but its id never reached us.
    session = provider.create_payment(
        request=HostedPaymentRequest(
            reference=payment_reference(attempt),
            amount=attempt.amount,
            currency=attempt.currency,
            description="test",
            customer_return_url="http://testserver/return/",
            webhook_url="http://testserver/webhook/",
        ),
    )

    resolved = resolve_unconfirmed_retail_payment(
        attempt=attempt,
        provider=provider,
    )

    assert resolved.status == PaymentAttempt.Status.PENDING
    assert resolved.provider_payment_id == session.provider_payment_id


@pytest.mark.django_db
def test_recovery_leaves_fresh_unconfirmed_attempt_alone(fake_provider, checkout):
    attempt = start_retail_payment(
        checkout=checkout,
    )

    recovery = recover_retail_payment(
        attempt=attempt,
    )

    attempt.refresh_from_db()

    assert recovery.action == RetailPaymentRecoveryAction.NEEDS_SUPPORT
    assert attempt.status == PaymentAttempt.Status.PENDING


@pytest.mark.django_db
def test_recovery_resolves_old_unconfirmed_attempt(fake_provider, checkout):
    attempt = start_retail_payment(
        checkout=checkout,
    )
    PaymentAttempt.objects.filter(pk=attempt.pk).update(
        created_at=timezone.now() - timedelta(minutes=5),
    )

    recovery = recover_retail_payment(
        attempt=attempt,
    )

    attempt.refresh_from_db()

    assert recovery.action == RetailPaymentRecoveryAction.PAYMENT_FAILED
    assert attempt.status == PaymentAttempt.Status.CANCELLED

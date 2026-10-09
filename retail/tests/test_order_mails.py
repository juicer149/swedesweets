"""A paid shop order mails the buyer (in the language they used) and
the shop owner (orders/notifications.py)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.test import override_settings
from django.utils import timezone, translation

from inventory.services import create_batch
from retail.services import (
    AnonymousBuyerInput,
    RetailOrderLineInput,
    complete_retail_payment,
    create_pending_retail_order,
    start_retail_payment,
)
from retail.tests.factories import (
    retail_buyer_data,
    retail_postal_area_factory,
    retail_product_price_factory,
)


def _paid_checkout(*, language: str = "en"):
    retail_postal_area_factory()
    offer = retail_product_price_factory(
        enabled=True,
        price=Decimal("12.50"),
    )
    create_batch(
        batch_id="A-001",
        product=offer.product,
        quantity=10,
        best_before=timezone.localdate() + timedelta(days=60),
        location="Shelf A1",
    )

    with translation.override(language):
        checkout = create_pending_retail_order(
            buyer=AnonymousBuyerInput(**retail_buyer_data()),
            lines=[
                RetailOrderLineInput(
                    commercial_price_id=offer.pk,
                    quantity=2,
                ),
            ],
        )

    return start_retail_payment(checkout=checkout)


@pytest.mark.django_db
@override_settings(ORDER_NOTIFICATION_EMAILS=["info@swedesweets.se"])
def test_paid_order_mails_the_buyer_and_the_owner(
    mailoutbox,
    django_capture_on_commit_callbacks,
):
    attempt = _paid_checkout()

    with django_capture_on_commit_callbacks(execute=True):
        order = complete_retail_payment(attempt=attempt)

    buyer_mail, staff_mail = mailoutbox

    assert buyer_mail.to == [order.buyer_email]
    assert f"#{order.pk}" in buyer_mail.subject
    assert "€25.00" in buyer_mail.body
    assert staff_mail.to == ["info@swedesweets.se"]


@pytest.mark.django_db
def test_the_order_remembers_the_language_the_buyer_used():
    attempt = _paid_checkout(language="fr")

    assert attempt.order.buyer_language_snapshot == "fr"


@pytest.mark.django_db
def test_no_mail_before_the_payment_goes_through(mailoutbox):
    _paid_checkout()

    assert mailoutbox == []

"""A shop that places its cart gets a confirmation, and the shop owner a
note about the new order (orders/notifications.py)."""

from __future__ import annotations

import pytest
from django.test import override_settings

from business.cart_services import add_catalog_offer_to_cart
from business.services import place_customer_cart
from business.tests.factories import standard_business_offer_factory
from business.tests.test_cart_placement import _add_eur_price, _create_stock


@pytest.mark.django_db
@override_settings(
    ORDER_NOTIFICATION_EMAILS=["info@swedesweets.se"],
    SITE_URL="https://www.swedesweets.se",
)
def test_placing_the_cart_mails_the_shop_and_the_owner(
    customer,
    apple,
    mailoutbox,
    django_capture_on_commit_callbacks,
):
    _create_stock(product=apple, quantity=10)
    offer = standard_business_offer_factory(product=apple)
    _add_eur_price(offer=offer, price="9.50")
    add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=offer.pk,
        quantity=3,
    )

    with django_capture_on_commit_callbacks(execute=True):
        order = place_customer_cart(customer=customer)

    buyer_mail, staff_mail = mailoutbox

    assert buyer_mail.to == [order.buyer_email]
    assert f"#{order.pk}" in buyer_mail.subject
    assert "€28.50" in buyer_mail.body
    assert "https://www.swedesweets.se/" in buyer_mail.body

    assert staff_mail.to == ["info@swedesweets.se"]
    assert f"#{order.pk}" in staff_mail.subject
    assert f"/{order.pk}/" in staff_mail.body


@pytest.mark.django_db
@override_settings(ORDER_NOTIFICATION_EMAILS=[], SITE_URL="")
def test_without_settings_only_the_shop_is_mailed_and_without_links(
    customer,
    apple,
    mailoutbox,
    django_capture_on_commit_callbacks,
):
    _create_stock(product=apple, quantity=10)
    offer = standard_business_offer_factory(product=apple)
    _add_eur_price(offer=offer, price="9.50")
    add_catalog_offer_to_cart(
        customer=customer,
        product=apple,
        commercial_price_id=offer.pk,
        quantity=1,
    )

    with django_capture_on_commit_callbacks(execute=True):
        place_customer_cart(customer=customer)

    (buyer_mail,) = mailoutbox

    assert "http" not in buyer_mail.body

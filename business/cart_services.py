from __future__ import annotations

from django.db import transaction

from business.models import BusinessCart
from carts.models import Cart
from carts.services import create_cart
from common.channels import SalesChannel
from customers.models import Customer


@transaction.atomic
def get_or_create_customer_cart(
    *,
    customer: Customer,
) -> Cart:
    """Return the customer's active BUSINESS cart, creating one if needed."""

    business_cart = (
        BusinessCart.objects
        .select_related(
            "cart",
        )
        .filter(
            customer_id=customer.pk,
        )
        .first()
    )

    if business_cart is not None:
        return _require_business_cart(
            cart=business_cart.cart,
        )

    # Serialize creation per customer. Without this lock, two concurrent
    # requests could both observe that no BusinessCart exists yet.
    customer = (
        Customer.objects
        .select_for_update()
        .get(pk=customer.pk)
    )

    # Another transaction may have created the association before this
    # transaction acquired the customer lock.
    business_cart = (
        BusinessCart.objects
        .select_related(
            "cart",
        )
        .filter(
            customer_id=customer.pk,
        )
        .first()
    )

    if business_cart is not None:
        return _require_business_cart(
            cart=business_cart.cart,
        )

    cart = create_cart(
        channel=SalesChannel.BUSINESS,
    )

    BusinessCart.objects.create(
        cart=cart,
        customer=customer,
    )

    return cart


def _require_business_cart(
    *,
    cart: Cart,
) -> Cart:
    if cart.channel != SalesChannel.BUSINESS:
        raise RuntimeError(
            "business cart invariant violated: "
            "cart does not belong to business channel"
        )

    return cart

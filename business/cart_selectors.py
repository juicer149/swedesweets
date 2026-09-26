from __future__ import annotations

from business.models import BusinessCart
from carts.models import Cart
from common.channels import SalesChannel
from customers.models import Customer


def get_customer_cart(
    *,
    customer: Customer,
) -> Cart | None:
    """Return the customer's BUSINESS cart without creating one."""

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

    if business_cart is None:
        return None

    cart = business_cart.cart

    if cart.channel != SalesChannel.BUSINESS:
        raise RuntimeError(
            "business cart invariant violated: "
            "cart does not belong to business channel"
        )

    return cart

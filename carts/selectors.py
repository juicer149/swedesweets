from __future__ import annotations

from django.db.models import Sum

from carts.models import Cart, CartLine


def units_in_cart_by_product_id(*, cart: Cart | None) -> dict[int, int]:
    """How many of each product a cart holds, all its offers together (the
    catalog card's in-cart badge)."""

    if cart is None:
        return {}

    rows = (
        CartLine.objects
        .filter(cart=cart)
        .values("commercial_price__product_id")
        .annotate(units=Sum("quantity"))
    )

    return {
        row["commercial_price__product_id"]: row["units"]
        for row in rows
    }

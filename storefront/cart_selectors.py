from __future__ import annotations

from uuid import UUID

from carts.models import (
    Cart,
    CartLine,
)
from common.channels import SalesChannel


def get_retail_cart(
    *,
    cart_id: UUID | None,
) -> Cart | None:
    if cart_id is None:
        return None

    return (
        Cart.objects
        .prefetch_related(
            "lines__commercial_price__product",
        )
        .filter(
            pk=cart_id,
            channel=SalesChannel.RETAIL,
        )
        .first()
    )


def get_retail_cart_line(
    *,
    cart: Cart,
    line_id: int,
) -> CartLine | None:
    return (
        CartLine.objects
        .select_related(
            "commercial_price__product",
        )
        .filter(
            pk=line_id,
            cart=cart,
        )
        .first()
    )

from __future__ import annotations

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from carts.models import Cart
from common.navbar_cart import (
    NavbarCart,
)
from retail.selectors import get_retail_checkout_with_open_payment
from storefront.cart_viewmodels import build_retail_cart_context


def build_retail_navbar_cart(
    *,
    cart: Cart | None,
) -> NavbarCart:
    if cart is None:
        return _empty_retail_navbar_cart()

    summary = build_retail_cart_context(cart=cart)
    if not summary.cart_lines:
        return _empty_retail_navbar_cart()
    lines = tuple(line.presentation for line in summary.cart_lines)
    open_checkout = get_retail_checkout_with_open_payment(cart=cart)
    payment_url = (
        reverse("storefront:checkout")
        if open_checkout
        else None
    )

    return NavbarCart(
        aria_label=_("Shopping cart"),
        title=_("Your cart"),
        line_count=len(lines),
        subtotal_label=summary.subtotal_label,
        is_retail=True,
        payment_url=payment_url,
        lines=lines,
        fragment_url=reverse("storefront:navbar_cart_fragment"),
        proceed_label=_("Go to cart"),
        proceed_url=reverse("storefront:cart"),
        empty_message=_("Your cart is empty."),
        empty_action_label=_("Browse shop"),
        empty_action_url=reverse("storefront:product_list"),
    )


def _empty_retail_navbar_cart() -> NavbarCart:
    return NavbarCart(
        aria_label=_("Shopping cart"),
        title=_("Your cart"),
        line_count=0,
        is_retail=True,
        lines=(),
        fragment_url=reverse("storefront:navbar_cart_fragment"),
        proceed_label=_("Continue shopping"),
        proceed_url=reverse("storefront:product_list"),
        empty_message=_("Your cart is empty."),
        empty_action_label=_("Browse shop"),
        empty_action_url=reverse("storefront:product_list"),
    )

from __future__ import annotations

from django.db import models


class BusinessCart(models.Model):
    """Associate one business customer with their active generic cart.

    Cart owns mutable purchase intent. This model owns only the
    business-customer identity attached to that cart.
    """

    cart = models.OneToOneField(
        "carts.Cart",
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="business_context",
    )

    customer = models.OneToOneField(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="business_cart",
    )

    def __str__(self) -> str:
        return (
            f"Business cart {self.cart_id} "
            f"for customer {self.customer_id}"
        )

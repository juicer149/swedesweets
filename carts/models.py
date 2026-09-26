from __future__ import annotations

import uuid

from django.db import models
from django.db.models import Q

from common.channels import SalesChannel


class Cart(models.Model):
    """Mutable purchase intent before an Order exists.

    A cart deliberately stores little durable business state. Buyer snapshots,
    prices, reservations, payment state and fulfillment belong to later stages.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    channel = models.CharField(
        max_length=20,
        choices=SalesChannel.choices,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    channel__in=SalesChannel.values,
                ),
                name="cart_channel_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.channel} cart {self.pk}"


class CartLine(models.Model):
    """One commercial selection and quantity in a mutable cart."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="lines",
    )

    commercial_price = models.ForeignKey(
        "pricing.CommercialPrice",
        on_delete=models.CASCADE,
        related_name="cart_lines",
    )

    quantity = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="cart_line_quantity_positive",
            ),
            models.UniqueConstraint(
                fields=[
                    "cart",
                    "commercial_price",
                ],
                name="unique_commercial_price_per_cart",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Cart {self.cart_id}: {self.quantity} "
            f"× commercial price {self.commercial_price_id}"
        )

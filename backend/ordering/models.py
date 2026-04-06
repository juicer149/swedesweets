import uuid
from django.db import models

from accounts.models import Store


class Order(models.Model):
    """
    Order placed by one store.

    DESIGN:
    - Order is the aggregate root for ordering history
    - It belongs to exactly one Store
    - Its line items are immutable historical snapshots
    - Status is currently simple but intended to express fulfillment progress

    STATUS MEANING:
    - pending: received but not yet packed
    - packed: prepared for delivery
    - delivered: completed and historically closed
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PACKED = "packed", "Packed"
        DELIVERED = "delivered", "Delivered"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order {self.id} ({self.store.name})"


class OrderItem(models.Model):
    """
    Immutable historical snapshot of one ordered product line.

    DESIGN:
    - An OrderItem must remain stable even if the catalog changes later
    - It snapshots the business-relevant product data needed to understand
      what was ordered at that point in time
    - `boxes` means number of boxes ordered, not number of individual units

    SNAPSHOT FIELDS:
    - product_code: business-facing catalog code used by stores
    - product_name: product name at order time
    - product_category_name: category label at order time
    - product_weight_grams: optional weight metadata at order time
    - product_units_per_box: optional packaging metadata at order time
    - boxes: number of boxes ordered
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product_code = models.PositiveIntegerField()
    product_name = models.CharField(max_length=200)
    product_category_name = models.CharField(max_length=100, blank=True)
    product_weight_grams = models.PositiveIntegerField(null=True, blank=True)
    product_units_per_box = models.PositiveIntegerField(null=True, blank=True)

    boxes = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product_code"],
                name="uniq_product_per_order",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product_name} x{self.boxes} box(es)"

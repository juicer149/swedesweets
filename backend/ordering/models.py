import uuid

from django.db import models

from accounts.models import Store


class Order(models.Model):
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

    def __str__(self) -> str:
        return f"Order {self.id} ({self.store.name})"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product_code = models.PositiveIntegerField()
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product_code"],
                name="uniq_product_per_order",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product_name} x{self.quantity}"

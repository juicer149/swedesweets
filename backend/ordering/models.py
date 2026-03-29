import uuid
from django.db import models

from accounts.models import Store
from catalog.models import Product


class RequestedOrder(models.Model):
    id = models.UUIDField(
            primary_key=True, 
            default=uuid.uuid4, 
            editable=False
            )
    store = models.ForeignKey(
            Store, 
            on_delete=models.PROTECT, 
            related_name="requested_orders"
            )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.store.name} {self.created_at.isoformat()}"


class RequestedOrderItem(models.Model):
    requested_order = models.ForeignKey(
            RequestedOrder, 
            on_delete=models.CASCADE, 
            related_name="items"
            )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)

    # snapshots for traceability
    product_code = models.PositiveIntegerField()
    product_name = models.CharField(max_length=200)

    requested_qty = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["requested_order", "product"],
                name="uniq_requested_item_per_product",
            )
        ]


class FulfilledOrder(models.Model):
    id = models.UUIDField(
            primary_key=True, 
            default=uuid.uuid4, 
            editable=False
            )

    requested_order = models.OneToOneField(
        RequestedOrder,
        on_delete=models.PROTECT,
        related_name="fulfilled_order",
    )

    packed_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    packing_notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Fulfilled {self.requested_order_id}"


class FulfilledOrderItem(models.Model):
    fulfilled_order = models.ForeignKey(
            FulfilledOrder, 
            on_delete=models.CASCADE, 
            related_name="items"
            )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)

    # snapshots
    product_code = models.PositiveIntegerField()
    product_name = models.CharField(max_length=200)

    fulfilled_qty = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fulfilled_order", "product"],
                name="uniq_fulfilled_item_per_product",
            )
        ]

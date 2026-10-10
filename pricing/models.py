from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from pricing.errors import InvalidCommercialPrice
from products.models import ProductVariant


class CommercialPrice(models.Model):
    """Current commercial pricing policy for one product scope and sales channel.

    A row without a batch applies to the product's ordinary eligible stock pool.

    A row with a batch applies only to that exact physical batch and may
    override the product-wide price for the same channel.

    `reason` describes why the current selling price differs from the ordinary
    price. A blank reason represents ordinary pricing.

    Every offer is for one variant of its product (docs/product-variants.md):
    a batch offer's is its batch's, and a product with only one variant fills
    it in on its own (hence blank=True: it is never left empty when saved).
    `product` stays beside it and always equals `variant.product`.
    """

    class Channel(models.TextChoices):
        BUSINESS = "business", "Business"
        RETAIL = "retail", "Retail"

    class Reason(models.TextChoices):
        SHORT_DATED = "short_dated", "Short dated"
        DAMAGED_PACKAGE = "damaged_package", "Damaged package"
        PROMOTION = "promotion", "Promotion"
        OTHER = "other", "Other"

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="commercial_prices",
    )

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="commercial_prices",
        blank=True,
    )

    batch = models.ForeignKey(
        "inventory.InventoryBatch",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="commercial_prices",
    )

    channel = models.CharField(
        max_length=20,
        choices=Channel.choices,
    )

    reason = models.CharField(
        max_length=30,
        choices=Reason.choices,
        blank=True,
    )

    enabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["channel", "enabled"]),
            models.Index(fields=["product", "channel"]),
            models.Index(fields=["batch", "channel"]),
        ]
        constraints = [
            # One standard offer per product and channel, until the code
            # that looks it up by product reads it by variant (steps 5-6).
            models.UniqueConstraint(
                fields=["product", "channel"],
                condition=Q(batch__isnull=True),
                name="unique_product_price_per_channel",
            ),
            models.UniqueConstraint(
                fields=["variant", "channel"],
                condition=Q(batch__isnull=True),
                name="unique_variant_price_per_channel",
            ),
            models.UniqueConstraint(
                fields=["batch", "channel"],
                condition=Q(batch__isnull=False),
                name="unique_batch_price_per_channel",
            ),
        ]

    @property
    def is_batch_specific(self) -> bool:
        return self.batch_id is not None

    def clean(self) -> None:
        super().clean()

        if self.batch_id is None:
            return

        batch_product_id = self.batch.product_id

        if batch_product_id != self.product_id:
            raise ValidationError(
                {
                    "batch": (
                        "Batch must belong to the same product as the "
                        "commercial price."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        update_fields = kwargs.get("update_fields")

        if update_fields is None or {
            "product",
            "variant",
            "batch",
        } & set(update_fields):
            self._resolve_variant()

            if update_fields is not None:
                kwargs["update_fields"] = {
                    *update_fields,
                    "product",
                    "variant",
                }

        super().save(*args, **kwargs)

    def _resolve_variant(self) -> None:
        """Fill in the variant (the batch's, or the only one of the
        product) and the product of a given variant, and keep the three in
        step."""

        if self.variant_id is None:
            if self.batch_id is not None:
                self.variant_id = self.batch.variant_id
            elif self.product_id is not None:
                variant = self.product.only_variant()

                if variant is None:
                    raise InvalidCommercialPrice(
                        "choose which variant of the product this price is for"
                    )

                self.variant = variant
            else:
                raise InvalidCommercialPrice(
                    "a commercial price needs a product or a variant"
                )

        if type(self).variant.is_cached(self):
            variant_product_id = self.variant.product_id
        else:
            variant_product_id = (
                ProductVariant.objects
                .values_list("product_id", flat=True)
                .get(pk=self.variant_id)
            )

        if self.product_id is None:
            self.product_id = variant_product_id

        if variant_product_id != self.product_id:
            raise InvalidCommercialPrice(
                "the variant belongs to another product"
            )

        if (
            self.batch_id is not None
            and self.batch.variant_id != self.variant_id
        ):
            raise InvalidCommercialPrice(
                "a batch price is for the batch's own variant"
            )

    def __str__(self) -> str:
        scope = (
            f"batch {self.batch_id}"
            if self.batch_id is not None
            else f"product {self.product_id}"
        )

        return f"{scope}: {self.channel} pricing"


class PriceAmount(models.Model):
    """One currency-specific amount for a CommercialPrice.

    `price` is always the amount charged to the buyer.

    `original_price` is optional comparison pricing used when the current
    amount represents a discount. It is not a second payable price.
    """

    class Currency(models.TextChoices):
        EUR = "EUR", "Euro"
        SEK = "SEK", "Swedish krona"

    commercial_price = models.ForeignKey(
        CommercialPrice,
        on_delete=models.CASCADE,
        related_name="amounts",
    )

    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "currency",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "commercial_price",
                    "currency",
                ],
                name="unique_price_amount_per_currency",
            ),
            models.CheckConstraint(
                condition=Q(price__gt=Decimal("0.00")),
                name="price_amount_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(original_price__isnull=True)
                    | Q(original_price__gt=Decimal("0.00"))
                ),
                name="original_price_positive_or_null",
            ),
            models.CheckConstraint(
                condition=(
                    Q(original_price__isnull=True)
                    | Q(original_price__gte=F("price"))
                ),
                name="original_price_not_below_price",
            ),
        ]

    @property
    def is_discounted(self) -> bool:
        return (
            self.original_price is not None
            and self.original_price > self.price
        )

    def __str__(self) -> str:
        return f"{self.price} {self.currency}"

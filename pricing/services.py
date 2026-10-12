from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from inventory.models import InventoryBatch
from pricing.errors import InvalidCommercialPrice
from pricing.models import CommercialPrice, PriceAmount
from products.models import Product, ProductVariant


def _to_decimal(
    value: Decimal | int | float | str,
) -> Decimal:
    if isinstance(value, Decimal):
        return value

    return Decimal(str(value))


def _validate_amounts(
    *,
    price: Decimal,
    original_price: Decimal | None,
) -> None:
    if price <= Decimal("0.00"):
        raise InvalidCommercialPrice(
            "price must be greater than zero"
        )

    if original_price is None:
        return

    if original_price <= Decimal("0.00"):
        raise InvalidCommercialPrice(
            "original price must be greater than zero"
        )

    if original_price < price:
        raise InvalidCommercialPrice(
            "original price cannot be below current price"
        )


@transaction.atomic
def create_commercial_price(
    *,
    product: Product,
    channel: str,
    batch: InventoryBatch | None = None,
    reason: str = "",
    variant: ProductVariant | None = None,
) -> CommercialPrice:
    """Create disabled commercial pricing for one scope: a batch, or a
    variant's standard offer (`variant`, or the product's only one)."""

    existing_prices = CommercialPrice.objects.filter(
        channel=channel,
    )

    if batch is None:
        variant = variant or _only_variant(product)
        duplicate_exists = existing_prices.filter(
            variant=variant,
            batch__isnull=True,
        ).exists()
    else:
        duplicate_exists = existing_prices.filter(
            batch=batch,
        ).exists()

    if duplicate_exists:
        raise InvalidCommercialPrice(
            "commercial price already exists for this scope and channel"
        )

    commercial_price = CommercialPrice(
        product=product,
        variant=variant if batch is None else None,
        batch=batch,
        channel=channel,
        reason=reason,
        enabled=False,
    )

    try:
        commercial_price.full_clean()
        commercial_price.save()
    except ValidationError as exc:
        raise InvalidCommercialPrice(
            "invalid commercial price configuration"
        ) from exc
    except IntegrityError as exc:
        raise InvalidCommercialPrice(
            "commercial price already exists for this scope and channel"
        ) from exc

    return commercial_price


@transaction.atomic
def set_price_amount(
    *,
    commercial_price: CommercialPrice,
    currency: str,
    price: Decimal | int | float | str,
    original_price: Decimal | int | float | str | None = None,
) -> PriceAmount:
    """Create or replace one currency amount on a commercial price."""

    locked_price = (
        CommercialPrice.objects
        .select_for_update()
        .get(pk=commercial_price.pk)
    )

    normalized_price = _to_decimal(price)
    normalized_original = (
        None
        if original_price is None
        else _to_decimal(original_price)
    )

    _validate_amounts(
        price=normalized_price,
        original_price=normalized_original,
    )

    amount, _created = PriceAmount.objects.update_or_create(
        commercial_price=locked_price,
        currency=currency,
        defaults={
            "price": normalized_price,
            "original_price": normalized_original,
        },
    )

    try:
        amount.full_clean()
    except ValidationError as exc:
        raise InvalidCommercialPrice(
            "invalid price amount"
        ) from exc

    return amount


@transaction.atomic
def remove_price_amount(
    *,
    commercial_price: CommercialPrice,
    currency: str,
) -> None:
    """Remove one configured currency amount from a commercial price."""

    locked_price = (
        CommercialPrice.objects
        .select_for_update()
        .get(pk=commercial_price.pk)
    )

    PriceAmount.objects.filter(
        commercial_price=locked_price,
        currency=currency,
    ).delete()


@transaction.atomic
def set_commercial_price_reason(
    *,
    commercial_price: CommercialPrice,
    reason: str,
) -> CommercialPrice:
    """Update why the current pricing differs from ordinary pricing."""

    commercial_price = (
        CommercialPrice.objects
        .select_for_update()
        .get(pk=commercial_price.pk)
    )

    commercial_price.reason = reason

    try:
        commercial_price.full_clean()
    except ValidationError as exc:
        raise InvalidCommercialPrice(
            "invalid commercial price reason"
        ) from exc

    commercial_price.save(
        update_fields=[
            "reason",
            "updated_at",
        ],
    )

    return commercial_price


@transaction.atomic
def set_commercial_price_enabled(
    *,
    commercial_price: CommercialPrice,
    enabled: bool,
) -> CommercialPrice:
    """Enable or disable a commercial pricing definition.

    Enabled means the pricing definition is active for its channel and scope.
    It does not guarantee that a concrete PriceAmount exists; channel-specific
    application policy decides whether the definition is currently sellable.
    """

    commercial_price = (
        CommercialPrice.objects
        .select_for_update()
        .get(pk=commercial_price.pk)
    )

    commercial_price.enabled = enabled
    commercial_price.save(
        update_fields=[
            "enabled",
            "updated_at",
        ],
    )

    return commercial_price


@transaction.atomic
def ensure_standard_offer(
    *,
    channel: str,
    product: Product | None = None,
    variant: ProductVariant | None = None,
) -> CommercialPrice:
    """Return a variant's standard offer for a channel, creating it if
    missing. The variant is `variant`, or the only one of `product`.

    Idempotent. A newly created standard offer is enabled, because before
    explicit offers existed every active product with stock was orderable in
    the business channel without any CommercialPrice row. Creating it
    disabled would silently make those products unorderable.

    An existing offer is returned unchanged: enabled, reason and amounts are
    never modified here. Availability changes go through
    `set_commercial_price_enabled`.

    Offer identity and price are separate concepts, so no PriceAmount is
    created.

    Only the business channel gets standard offers automatically. Retail
    offers remain explicit, priced commercial decisions.
    """

    if channel != CommercialPrice.Channel.BUSINESS:
        raise InvalidCommercialPrice(
            "standard offers are only created automatically "
            "for the business channel"
        )

    if variant is None:
        if product is None:
            raise InvalidCommercialPrice(
                "a standard offer needs a product or a variant"
            )

        variant = _only_variant(product)

    existing = (
        CommercialPrice.objects
        .filter(
            variant=variant,
            channel=channel,
            batch__isnull=True,
        )
        .first()
    )

    if existing is not None:
        return existing

    try:
        with transaction.atomic():
            return CommercialPrice.objects.create(
                product_id=variant.product_id,
                variant=variant,
                batch=None,
                channel=channel,
                reason="",
                enabled=True,
            )
    except IntegrityError:
        # A concurrent caller created it between the read and the insert;
        # unique_variant_price_per_channel guarantees there is exactly one.
        return CommercialPrice.objects.get(
            variant=variant,
            channel=channel,
            batch__isnull=True,
        )


def _only_variant(product: Product) -> ProductVariant:
    """The variant a product-wide call means: the product's only one."""

    variant = product.only_variant()

    if variant is None:
        raise InvalidCommercialPrice(
            "choose which variant of the product this price is for"
        )

    return variant

"""Standard prices from the ops product form, per variant.

A product's variants each have their own standard offer per channel: its
switch (sold in that channel or not) and its amounts.
`update_variants_pricing` sets each variant's;
`update_product_standard_pricing` gives every variant the same (a new
product, which has one variant).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from pricing.errors import InvalidCommercialPrice
from pricing.models import CommercialPrice, PriceAmount
from pricing.selectors import get_variant_commercial_price
from pricing.services import (
    create_commercial_price,
    ensure_standard_offer,
    remove_price_amount,
    set_commercial_price_enabled,
    set_price_amount,
)
from products.models import Product, ProductVariant


@dataclass(frozen=True, slots=True)
class VariantPrices:
    """One variant's standard amounts; None removes that amount."""

    business_eur: Decimal | None = None
    business_sek: Decimal | None = None
    retail_eur: Decimal | None = None
    retail_sek: Decimal | None = None


@dataclass(frozen=True, slots=True)
class VariantPricing:
    """One variant's standard pricing: in which channels it is sold, and its
    amounts (None: leave them as they are)."""

    retail_enabled: bool
    business_enabled: bool
    prices: VariantPrices | None = None


@transaction.atomic
def update_variants_pricing(
    *,
    product: Product,
    pricing: Mapping[int, VariantPricing],
) -> None:
    """Apply each variant's pricing (`pricing`, by variant id; a variant
    left out is not changed).

    BUSINESS: the variant keeps a standard offer (it may be unpriced); its
    switch is whether it is sold to business customers.

    RETAIL: a variant sold in retail needs an amount.
    """

    variants = {variant.pk: variant for variant in product.variants.all()}
    unknown = set(pricing) - set(variants)

    if unknown:
        raise InvalidCommercialPrice(
            "prices given for a variant of another product"
        )

    for variant_id, variant_pricing in pricing.items():
        variant = variants[variant_id]

        if variant_pricing.retail_enabled and not _retail_amount_after(
            variant=variant,
            prices=variant_pricing.prices,
        ):
            raise InvalidCommercialPrice(
                f"{variant.display_name} is sold in retail: give it a "
                "retail price."
            )

        prices = variant_pricing.prices

        _update_channel_pricing(
            variant=variant,
            channel=CommercialPrice.Channel.BUSINESS,
            enabled=variant_pricing.business_enabled,
            amounts=(
                None
                if prices is None
                else {
                    PriceAmount.Currency.EUR: prices.business_eur,
                    PriceAmount.Currency.SEK: prices.business_sek,
                }
            ),
        )

        _update_channel_pricing(
            variant=variant,
            channel=CommercialPrice.Channel.RETAIL,
            enabled=variant_pricing.retail_enabled,
            amounts=(
                None
                if prices is None
                else {
                    PriceAmount.Currency.EUR: prices.retail_eur,
                    PriceAmount.Currency.SEK: prices.retail_sek,
                }
            ),
        )


@transaction.atomic
def update_product_standard_pricing(
    *,
    product: Product,
    business_eur: Decimal | None,
    business_sek: Decimal | None,
    business_enabled: bool,
    retail_eur: Decimal | None,
    retail_sek: Decimal | None,
    retail_enabled: bool,
) -> None:
    """The same standard pricing for every variant of a product (a new
    product: its only variant).

    BUSINESS: `business_enabled` is channel availability of the business
    standard offer. Amounts are optional.

    RETAIL: `retail_enabled` activates retail pricing, which requires at
    least one amount (validated by the form).
    """

    same = VariantPricing(
        retail_enabled=retail_enabled,
        business_enabled=business_enabled,
        prices=VariantPrices(
            business_eur=business_eur,
            business_sek=business_sek,
            retail_eur=retail_eur,
            retail_sek=retail_sek,
        ),
    )

    update_variants_pricing(
        product=product,
        pricing={variant.pk: same for variant in product.variants.all()},
    )


def _retail_amount_after(
    *,
    variant: ProductVariant,
    prices: VariantPrices | None,
) -> bool:
    """Whether the variant has a retail amount once the form is applied."""

    if prices is not None:
        return prices.retail_eur is not None or prices.retail_sek is not None

    offer = get_variant_commercial_price(
        variant=variant,
        channel=CommercialPrice.Channel.RETAIL,
    )

    return offer is not None and offer.amounts.exists()


def _update_channel_pricing(
    *,
    variant: ProductVariant,
    channel: str,
    enabled: bool,
    amounts: dict[str, Decimal | None] | None,
) -> None:
    """One variant's offer in one channel: its switch, and its amounts
    (None: leave them as they are)."""

    commercial_price = get_variant_commercial_price(
        variant=variant,
        channel=channel,
    )

    if commercial_price is None:
        if channel == CommercialPrice.Channel.BUSINESS:
            # Every variant should already have its business standard offer
            # (data migration + product creation); recreate it with the
            # correct semantics if it is somehow missing.
            commercial_price = ensure_standard_offer(
                variant=variant,
                channel=channel,
            )
        else:
            has_amount = amounts is not None and any(
                amount is not None
                for amount in amounts.values()
            )

            if not has_amount and not enabled:
                return

            if not has_amount:
                # Retail on for the product, but this variant has no
                # price: nothing of it to sell, nothing to create.
                return

            commercial_price = create_commercial_price(
                product=variant.product,
                variant=variant,
                channel=channel,
            )

    for currency, amount in (amounts or {}).items():
        if amount is None:
            remove_price_amount(
                commercial_price=commercial_price,
                currency=currency,
            )
            continue

        set_price_amount(
            commercial_price=commercial_price,
            currency=currency,
            price=amount,
        )

    set_commercial_price_enabled(
        commercial_price=commercial_price,
        enabled=enabled,
    )

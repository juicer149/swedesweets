from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.utils.translation import gettext_lazy as _

from carts.models import CartLine
from orders.models import Order, OrderLine
from pricing.models import (
    CommercialPrice,
    PriceAmount,
)
from products.catalog import variant_display_name
from products.localization import translated_product_name
from products.models import Product, ProductVariant

_REASON_LABELS = {
    CommercialPrice.Reason.SHORT_DATED: _("Short dated"),
    CommercialPrice.Reason.DAMAGED_PACKAGE: _("Damaged package"),
    CommercialPrice.Reason.PROMOTION: _("Promotion"),
    CommercialPrice.Reason.OTHER: _("Other"),
}


@dataclass(frozen=True, slots=True)
class BusinessOrderLinePresentation:
    catalog_label: str
    offer_label: str | None
    price_label: str | None
    unit_price: Decimal | None = None

    def total_label(self, quantity: int) -> str | None:
        if self.unit_price is None:
            return None
        return f"€{self.unit_price * quantity:.2f}"


def business_variant_catalog_label(
    variant: ProductVariant,
    *,
    product: Product,
    language_code: str,
) -> str:
    """One variant as a customer reads it in a cart or an order: the name
    with its label and its own weight ("Hoodie — M · 400 g"); a product's
    only variant reads as the product ("Rambo — Twist · 2000 g"). The
    internal number and the stock unit are for ops (their pages use
    Product.catalog_label)."""

    # The product given (not variant.product): its translations are the
    # ones the caller prefetched.
    name = translated_product_name(
        product,
        language_code=language_code,
    )

    return (
        f"{variant_display_name(name, variant.label)} · "
        + _("%(weight)s g") % {"weight": variant.weight_per_unit}
    )


def business_order_line_presentation(
    line: OrderLine,
    *,
    language_code: str,
    currency: str,
) -> BusinessOrderLinePresentation:
    return BusinessOrderLinePresentation(
        catalog_label=business_variant_catalog_label(
            line.variant,
            product=line.product,
            language_code=language_code,
        ),
        offer_label=_business_order_offer_label(
            line
        ),
        price_label=_business_price_label(
            line.unit_price_snapshot,
            currency=currency,
        ),
    )


def business_cart_line_presentation(
    line: CartLine,
    *,
    language_code: str,
) -> BusinessOrderLinePresentation:
    """Present one mutable BUSINESS cart line using current offer data."""

    commercial_price = line.commercial_price

    amount = _find_price_amount(
        commercial_price=commercial_price,
        currency=PriceAmount.Currency.EUR,
    )

    return BusinessOrderLinePresentation(
        catalog_label=business_variant_catalog_label(
            commercial_price.variant,
            product=commercial_price.product,
            language_code=language_code,
        ),
        offer_label=_commercial_price_offer_label(
            commercial_price
        ),
        unit_price=amount.price if amount is not None else None,
        price_label=_business_price_label(
            (
                amount.price
                if amount is not None
                else None
            ),
            currency=PriceAmount.Currency.EUR,
        ),
    )


def _business_order_offer_label(
    line: OrderLine,
) -> str | None:
    return _commercial_price_offer_label(
        line.commercial_offer
    )


def _commercial_price_offer_label(
    commercial_price: CommercialPrice,
) -> str | None:
    if commercial_price.reason:
        return str(
            _REASON_LABELS.get(
                commercial_price.reason,
                _("Special offer"),
            )
        )

    if commercial_price.is_batch_specific:
        return str(
            _("Special offer")
        )

    return None


def _find_price_amount(
    *,
    commercial_price: CommercialPrice,
    currency: str,
) -> PriceAmount | None:
    for amount in commercial_price.amounts.all():
        if amount.currency == currency:
            return amount

    return None


def _business_price_label(
    price: Decimal | None,
    *,
    currency: str,
) -> str | None:
    if price is None:
        return None

    if currency == Order.Currency.EUR:
        return f"€{price:.2f}"

    return f"{price:.2f} {currency}"


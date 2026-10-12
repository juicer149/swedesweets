from __future__ import annotations

from decimal import Decimal

from django import forms

from common.form_layout import set_form_field_layout
from pricing.models import CommercialPrice, PriceAmount
from pricing.product_configuration import VariantPrices

PRICE_DECIMAL_PLACES = 2
PRICE_MAX_DIGITS = 10

BUSINESS_STATUS_HELP_TEXT = (
    "Active means the product can be ordered in the B2B portal. "
    "A price is optional; inactive hides the product from B2B ordering."
)

RETAIL_STATUS_HELP_TEXT = (
    "Active retail pricing needs at least one currency amount."
)


def price_field(
    *,
    label: str,
) -> forms.DecimalField:
    return forms.DecimalField(
        required=False,
        min_value=Decimal("0.01"),
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        label=label,
        error_messages={
            "invalid": "Enter a valid price.",
            "min_value": "Price must be greater than zero.",
            "max_digits": "Price is too large.",
            "max_decimal_places": (
                "Use at most two decimal places."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "inputmode": "decimal",
                "autocomplete": "off",
                "placeholder": "0.00",
            }
        ),
    )


def _active_toggle(
    *,
    help_text: str,
) -> forms.BooleanField:
    """A channel's status as one switch (green on, muted off), like the
    product's own."""

    field = forms.BooleanField(
        required=False,
        label="Status",
        help_text=help_text,
        widget=forms.CheckboxInput(
            attrs={"class": "product-tag-toggle__input"},
        ),
    )
    field.tag_toggle = True
    field.tag_toggle_label = "Active"
    field.tag_toggle_icon = "check"
    field.tag_toggle_class = (
        "product-tag-toggle "
        "product-tag-toggle--status"
    )

    return field


# A variant's prices: (field, channel, currency). The product's price on
# the edit form has the same fields with "product_" before them.
PRICE_FIELDS = (
    ("retail_eur", CommercialPrice.Channel.RETAIL, PriceAmount.Currency.EUR),
    ("retail_sek", CommercialPrice.Channel.RETAIL, PriceAmount.Currency.SEK),
    ("business_eur", CommercialPrice.Channel.BUSINESS, PriceAmount.Currency.EUR),
    ("business_sek", CommercialPrice.Channel.BUSINESS, PriceAmount.Currency.SEK),
)


class ProductPricesForm(forms.Form):
    """The product's price over the variants on the edit form: saved as the
    price of every variant without its own (a row's price tag switched off;
    variant_forms.VariantForm.own_price), and of every field a variant with
    its own leaves empty. An empty field here removes that price from
    them."""

    product_retail_eur = price_field(label="Retail price in EUR")
    product_retail_sek = price_field(label="Retail price in SEK")
    product_business_eur = price_field(label="Business price in EUR")
    product_business_sek = price_field(label="Business price in SEK")

    def prices_for(self, row) -> VariantPrices:
        """A variant's prices once saved: with its own price on, each price
        it was given, the product's for the fields it left empty; off, the
        product's."""

        own = row.cleaned_data.get("own_price")

        return VariantPrices(
            **{
                field_name: (
                    row.cleaned_data.get(field_name) if own else None
                )
                or self.cleaned_data.get(f"product_{field_name}")
                for field_name, _channel, _currency in PRICE_FIELDS
            }
        )


def variant_amounts(
    *,
    prices_by_channel: dict[str, dict[int, CommercialPrice]],
    variant_id: int,
) -> dict[str, Decimal | None]:
    """A variant's standard prices, by field (PRICE_FIELDS)."""

    return {
        field_name: offer_amount(
            prices_by_channel.get(channel, {}).get(variant_id),
            currency=currency,
        )
        for field_name, channel, currency in PRICE_FIELDS
    }


def product_amounts(
    *,
    prices_by_channel: dict[str, dict[int, CommercialPrice]],
    variant_ids: list[int],
) -> dict[str, Decimal | None]:
    """The product's price as the page shows it: per price, the one most
    variants share (on a tie, the first variant's). Nothing stores it
    apart: a variant with a price unlike it has its own."""

    per_variant = [
        variant_amounts(prices_by_channel=prices_by_channel, variant_id=pk)
        for pk in variant_ids
    ]
    product: dict[str, Decimal | None] = {}

    for field_name, _channel, _currency in PRICE_FIELDS:
        values = [amounts[field_name] for amounts in per_variant]
        product[field_name] = max(
            values,
            key=values.count,
            default=None,
        )

    return product


def build_product_prices_initial_data(
    *,
    prices_by_channel: dict[str, dict[int, CommercialPrice]],
    variant_ids: list[int],
) -> dict[str, object]:
    return {
        f"product_{field_name}": value
        for field_name, value in product_amounts(
            prices_by_channel=prices_by_channel,
            variant_ids=variant_ids,
        ).items()
    }


def offer_amount(
    offer: CommercialPrice | None,
    *,
    currency: str,
) -> Decimal | None:
    if offer is None:
        return None

    return next(
        (
            amount.price
            for amount in offer.amounts.all()
            if amount.currency == currency
        ),
        None,
    )


class ProductPricingForm(forms.Form):
    # Each channel's switch first, then its prices.
    business_active = _active_toggle(
        help_text=BUSINESS_STATUS_HELP_TEXT,
    )
    business_eur = price_field(
        label="EUR",
    )
    business_sek = price_field(
        label="SEK",
    )

    retail_active = _active_toggle(
        help_text=RETAIL_STATUS_HELP_TEXT,
    )
    retail_eur = price_field(
        label="EUR",
    )
    retail_sek = price_field(
        label="SEK",
    )

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        # A new product is sold to business customers unless switched off
        # (as the business standard offer starts enabled).
        self.fields["business_active"].initial = True

        set_form_field_layout(
            self,
            full=(
                "business_active",
                "retail_active",
            ),
            half=(
                "business_eur",
                "business_sek",
                "retail_eur",
                "retail_sek",
            ),
        )

    def clean(self) -> dict[str, object]:
        cleaned_data = super().clean()

        # BUSINESS status is channel availability, and the business standard
        # offer may be unpriced, so an active business status needs no amount.
        # RETAIL checkout requires a concrete price, so active retail pricing
        # still needs at least one amount.
        self._validate_active_channel_has_amount(
            channel=CommercialPrice.Channel.RETAIL,
            status_field="retail_active",
            amount_fields=(
                "retail_eur",
                "retail_sek",
            ),
        )

        return cleaned_data

    @property
    def business_enabled(self) -> bool:
        return bool(self.cleaned_data["business_active"])

    @property
    def retail_enabled(self) -> bool:
        return bool(self.cleaned_data["retail_active"])

    def pricing_values(self) -> dict[str, object]:
        """Translate presentation values into the pricing service contract."""

        return {
            "business_eur": (
                self.cleaned_data["business_eur"]
            ),
            "business_sek": (
                self.cleaned_data["business_sek"]
            ),
            "business_enabled": (
                self.business_enabled
            ),
            "retail_eur": (
                self.cleaned_data["retail_eur"]
            ),
            "retail_sek": (
                self.cleaned_data["retail_sek"]
            ),
            "retail_enabled": (
                self.retail_enabled
            ),
        }

    def _validate_active_channel_has_amount(
        self,
        *,
        channel: str,
        status_field: str,
        amount_fields: tuple[str, str],
    ) -> None:
        if not self.cleaned_data.get(status_field):
            return

        has_amount = any(
            self.cleaned_data.get(field_name)
            is not None
            for field_name in amount_fields
        )

        if has_amount:
            return

        channel_label = CommercialPrice.Channel(
            channel
        ).label

        self.add_error(
            status_field,
            (
                f"{channel_label} pricing needs at least "
                "one configured currency amount."
            ),
        )

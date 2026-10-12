"""Variants and prices on the product edit form (docs/product-variants.md).

Each existing variant is a row (label, weight, its sales channels, its coin:
its own retail and business prices in EUR and SEK, or the product's;
delete), in the order shown
everywhere; new rows are added in the page (variant_editor.js) and
everything is saved with "Update product". The sales channels say where
the variant is sold: with neither, it is paused. The section sits behind a
lock: a hands-off guard in the page (its fields are inert, still sent as
they were), not a rule the server enforces.
"""

from __future__ import annotations

from dataclasses import dataclass

from django import forms
from django.forms import BaseFormSet, formset_factory

from ops_portal.products.pricing_forms import (
    PRICE_FIELDS,
    price_field,
    product_amounts,
    variant_amounts,
)
from pricing.models import CommercialPrice
from pricing.product_configuration import VariantPrices
from products.catalog import (
    MAX_VARIANT_LABEL_LENGTH,
    MAX_WEIGHT_PER_UNIT,
    MIN_WEIGHT_PER_UNIT,
)
from products.models import Product, ProductVariant
from products.services import VariantChange, variant_has_history

VARIANT_FORMSET_PREFIX = "variants"


SUGGESTED_VARIANT_LABELS = (
    "XS",
    "S",
    "M",
    "L",
    "XL",
    "XXL",
    "One size",
)

LABEL_SUGGESTIONS_ID = "variant-label-suggestions"


@dataclass(frozen=True, slots=True)
class VariantState:
    """What a row needs to know about its saved variant."""

    variant: ProductVariant
    has_history: bool
    is_stocked_or_ordered: bool


class VariantForm(forms.Form):
    variant_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-variant-id": "true"}),
    )

    # The row's place in the list; variant_editor.js numbers the rows.
    position = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-variant-position": "true"}),
    )

    label = forms.CharField(
        required=False,
        max_length=MAX_VARIANT_LABEL_LENGTH,
        label="Label",
        widget=forms.TextInput(
            attrs={
                "list": LABEL_SUGGESTIONS_ID,
                "autocomplete": "off",
                "placeholder": "e.g. M, 60 g",
            }
        ),
    )

    weight_per_unit = forms.IntegerField(
        min_value=MIN_WEIGHT_PER_UNIT,
        max_value=MAX_WEIGHT_PER_UNIT,
        label="Weight (g)",
        error_messages={
            "required": "Enter the weight in grams.",
            "invalid": "Enter a whole number of grams.",
        },
        widget=forms.NumberInput(attrs={"inputmode": "numeric"}),
    )

    # Its sales channels: sold in the shop, sold to business customers.
    # Neither: the variant is paused (rule 6, docs/product-variants.md).
    retail = forms.BooleanField(
        required=False,
        label="Retail",
        widget=forms.CheckboxInput(
            attrs={"class": "product-tag-toggle__input"}
        ),
    )

    business = forms.BooleanField(
        required=False,
        label="Business",
        widget=forms.CheckboxInput(
            attrs={"class": "product-tag-toggle__input"}
        ),
    )

    # The row's coin: on, the variant has its own prices (the fields under
    # it); off, it is sold at the product's price (ProductPricesForm).
    own_price = forms.BooleanField(
        required=False,
        label="Own price",
        widget=forms.CheckboxInput(
            attrs={
                "class": "variant-coin__input",
                "data-variant-own-price": "true",
            }
        ),
    )

    retail_eur = price_field(label="Retail EUR")
    retail_sek = price_field(label="Retail SEK")
    business_eur = price_field(label="Business EUR")
    business_sek = price_field(label="Business SEK")

    # Set by the row's trash (variant_editor.js), after the question.
    delete = forms.BooleanField(
        required=False,
        label="Delete",
        widget=forms.HiddenInput(attrs={"data-variant-delete": "true"}),
    )

    def __init__(
        self,
        *args,
        states_by_id: dict[int, VariantState] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.states_by_id = states_by_id or {}

        for field_name, _channel, _currency in PRICE_FIELDS:
            self.fields[field_name].widget.attrs["placeholder"] = "0.00"

        state = self.state

        if state is not None and state.is_stocked_or_ordered:
            # Rule 5: shown, sent, but not to be changed.
            self.fields["weight_per_unit"].widget.attrs["readonly"] = True

    @property
    def state(self) -> VariantState | None:
        try:
            variant_id = int(self["variant_id"].value())
        except (TypeError, ValueError):
            return None

        return self.states_by_id.get(variant_id)

    @property
    def can_delete(self) -> bool:
        state = self.state

        return state is None or not state.has_history

    @property
    def is_sold(self) -> bool:
        return bool(
            self.cleaned_data.get("retail")
            or self.cleaned_data.get("business")
        )

    def prices(self) -> VariantPrices:
        return VariantPrices(
            **{
                field_name: self.cleaned_data.get(field_name)
                for field_name, _channel, _currency in PRICE_FIELDS
            }
        )


class BaseVariantFormSet(BaseFormSet):
    def __init__(
        self,
        *args,
        product: Product,
        new_row_channels: dict[str, bool] | None = None,
        **kwargs,
    ) -> None:
        self.product = product
        self.new_row_channels = new_row_channels or {
            "retail": False,
            "business": True,
        }
        self.states_by_id = {
            variant.pk: VariantState(
                variant=variant,
                has_history=variant_has_history(variant),
                is_stocked_or_ordered=(
                    variant.batches.exists()
                    or variant.order_lines.exists()
                ),
            )
            for variant in product.variants.all()
        }

        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["states_by_id"] = self.states_by_id

        if index is None:
            # The template row the page copies for "Add variant": the
            # product's weight and the first variant's channels to start
            # from.
            kwargs["initial"] = {
                "weight_per_unit": self.product.weight_per_unit,
                **self.new_row_channels,
            }

        return kwargs

    @property
    def ordered_forms_by_position(self) -> list[VariantForm]:
        """The rows in the order the page left them."""

        def sort_key(indexed):
            index, form = indexed
            position = form.cleaned_data.get("position")

            return (position is None, position or 0, index)

        return [
            form
            for _index, form in sorted(
                enumerate(self.forms),
                key=sort_key,
            )
            if form.has_changed() or form.cleaned_data.get("variant_id")
        ]

    def clean(self) -> None:
        super().clean()

        if any(form.errors for form in self.forms):
            return

        rows = self.ordered_forms_by_position
        kept: list[VariantForm] = []

        for form in rows:
            data = form.cleaned_data
            state = form.state
            variant_id = data.get("variant_id")

            if variant_id is not None and state is None:
                raise forms.ValidationError(
                    "The variants changed meanwhile: reload the page."
                )

            if data.get("delete"):
                if state is not None and state.has_history:
                    form.add_error(
                        "delete",
                        "Used before: switch its channels off instead.",
                    )
                continue

            if (
                state is not None
                and state.is_stocked_or_ordered
                and data["weight_per_unit"]
                != state.variant.weight_per_unit
            ):
                form.add_error(
                    "weight_per_unit",
                    "Has stock or orders: the weight is fixed.",
                )

            kept.append(form)

        saved_ids = set(self.states_by_id)
        named_ids = {
            form.cleaned_data["variant_id"]
            for form in rows
            if form.cleaned_data.get("variant_id") is not None
        }

        if named_ids != saved_ids:
            raise forms.ValidationError(
                "The variants changed meanwhile: reload the page."
            )

        if not kept:
            raise forms.ValidationError(
                "A product keeps at least one variant."
            )

        seen_labels: set[str] = set()

        for form in kept:
            label = " ".join(form.cleaned_data["label"].split())

            if len(kept) > 1 and not label:
                form.add_error(
                    "label",
                    "With more than one variant, each needs a label.",
                )
            elif label.casefold() in seen_labels:
                form.add_error("label", "Another variant has this label.")

            seen_labels.add(label.casefold())

        if self.product.active and not any(form.is_sold for form in kept):
            raise forms.ValidationError(
                "An active product needs a variant in a sales channel: "
                "switch one on, or set the product inactive."
            )

    def changes(self) -> list[VariantChange]:
        """The rows as the service takes them, in order; a new row deleted
        before saving is just dropped."""

        return [
            VariantChange(
                variant_id=form.cleaned_data.get("variant_id"),
                label=form.cleaned_data["label"],
                weight_per_unit=form.cleaned_data["weight_per_unit"],
                # Sold in no channel: paused.
                active=form.is_sold,
                delete=form.cleaned_data.get("delete", False),
            )
            for form in self.ordered_forms_by_position
            if form.cleaned_data.get("variant_id") is not None
            or not form.cleaned_data.get("delete")
        ]


VariantFormSet = formset_factory(
    VariantForm,
    formset=BaseVariantFormSet,
    extra=0,
)


def build_variant_formset(
    *,
    product: Product,
    data=None,
    prices_by_channel: dict[str, dict[int, CommercialPrice]] | None = None,
) -> BaseVariantFormSet:
    """The rows, filled with each variant and its standard prices
    (`prices_by_channel`: channel → variant id → offer)."""

    prices_by_channel = prices_by_channel or {}
    variants = list(product.variants.all())
    shared = product_amounts(
        prices_by_channel=prices_by_channel,
        variant_ids=[variant.pk for variant in variants],
    )
    initial = []

    for index, variant in enumerate(variants, start=1):
        amounts = variant_amounts(
            prices_by_channel=prices_by_channel,
            variant_id=variant.pk,
        )
        initial.append(
            {
                "variant_id": variant.pk,
                "position": index,
                "label": variant.label,
                "weight_per_unit": variant.weight_per_unit,
                "retail": variant.active and _enabled(
                    prices_by_channel.get(CommercialPrice.Channel.RETAIL, {}),
                    variant,
                ),
                "business": variant.active and _enabled(
                    prices_by_channel.get(CommercialPrice.Channel.BUSINESS, {}),
                    variant,
                ),
                # Prices unlike the product's are the variant's own.
                "own_price": amounts != shared,
                "delete": False,
                **amounts,
            }
        )

    return VariantFormSet(
        data=data,
        initial=None if data is not None else initial,
        prefix=VARIANT_FORMSET_PREFIX,
        product=product,
        # A new variant starts in the first one's channels.
        new_row_channels=(
            {
                "retail": initial[0]["retail"],
                "business": initial[0]["business"],
            }
            if initial
            else None
        ),
    )


def _enabled(
    offers: dict[int, CommercialPrice],
    variant: ProductVariant,
) -> bool:
    offer = offers.get(variant.pk)

    return offer is not None and offer.enabled

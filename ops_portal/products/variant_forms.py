"""The Variants tab of the product edit form (docs/product-variants.md).

Each existing variant is a row (label, weight, on sale, delete), in the
order shown everywhere; new rows are added in the page (variant_editor.js)
and the whole tab is saved with the form's Save. The tab sits behind a
lock: until it is opened, its fields are not sent and nothing changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from django import forms
from django.forms import BaseFormSet, formset_factory

from products.catalog import (
    MAX_VARIANT_LABEL_LENGTH,
    MAX_WEIGHT_PER_UNIT,
    MIN_WEIGHT_PER_UNIT,
)
from products.models import Product, ProductVariant
from products.services import VariantChange, variant_has_history

VARIANT_FORMSET_PREFIX = "variants"

# Sent only when the lock is open (it sits inside the disabled fieldset).
VARIANTS_UNLOCKED_FIELD = "variants-unlocked"

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

    active = forms.BooleanField(
        required=False,
        label="On sale",
        widget=forms.CheckboxInput(
            attrs={"class": "product-tag-toggle__input"}
        ),
    )

    delete = forms.BooleanField(
        required=False,
        label="Delete",
        widget=forms.CheckboxInput(
            attrs={
                "class": "product-tag-toggle__input",
                "data-variant-delete": "true",
            }
        ),
    )

    def __init__(
        self,
        *args,
        states_by_id: dict[int, VariantState] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.states_by_id = states_by_id or {}

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


class BaseVariantFormSet(BaseFormSet):
    def __init__(
        self,
        *args,
        product: Product,
        **kwargs,
    ) -> None:
        self.product = product
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
            # The template row the page copies for "Add variant": on sale,
            # the product's weight to start from.
            kwargs["initial"] = {
                "weight_per_unit": self.product.weight_per_unit,
                "active": True,
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
                        "Used before: pause it instead.",
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

        if self.product.active and not any(
            form.cleaned_data.get("active") for form in kept
        ):
            raise forms.ValidationError(
                "Keep one variant on sale, or pause the product instead."
            )

    def changes(self) -> list[VariantChange]:
        """The rows as the service takes them, in order; a new row deleted
        before saving is just dropped."""

        return [
            VariantChange(
                variant_id=form.cleaned_data.get("variant_id"),
                label=form.cleaned_data["label"],
                weight_per_unit=form.cleaned_data["weight_per_unit"],
                active=form.cleaned_data.get("active", False),
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
) -> BaseVariantFormSet:
    initial = [
        {
            "variant_id": variant.pk,
            "position": index,
            "label": variant.label,
            "weight_per_unit": variant.weight_per_unit,
            "active": variant.active,
            "delete": False,
        }
        for index, variant in enumerate(product.variants.all(), start=1)
    ]

    return VariantFormSet(
        data=data,
        initial=None if data is not None else initial,
        prefix=VARIANT_FORMSET_PREFIX,
        product=product,
    )

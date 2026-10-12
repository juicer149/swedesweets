from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

from django import forms

from common.form_layout import set_form_field_layout
from inventory.models import InventoryBatch
from products.models import Product, ProductVariant


class ProductChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, product: Product) -> str:
        return product.catalog_label


@dataclass(frozen=True, slots=True)
class VariantChoice:
    pk: int
    text: str
    checked: bool


@dataclass(frozen=True, slots=True)
class VariantGroup:
    """The variants to choose from for one product with several."""

    product_id: int
    choices: tuple[VariantChoice, ...]
    shown: bool


class BatchForm(forms.Form):
    product = ProductChoiceField(
        queryset=Product.objects.filter(active=True).order_by(
            "internal_number",
            "brand",
            "name",
            "weight_per_unit",
        ),
        label="Product",
        empty_label="Choose product",
        error_messages={
            "required": "Choose a product.",
            "invalid_choice": "Choose a valid active product.",
        },
        widget=forms.Select(
            attrs={
                "data-enhanced-select": "true",
                "data-enhanced-select-search": "true",
            }
        ),
    )

    # Only for a product with several variants (a size, a weight); the page
    # shows that product's variants under the product (batch_variant.js).
    variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.filter(
            active=True,
            product__active=True,
        ),
        required=False,
        label="Variant",
        error_messages={
            "invalid_choice": "Choose one of the product's variants.",
        },
        widget=forms.RadioSelect,
    )

    quantity = forms.IntegerField(
        min_value=1,
        label="Physical quantity",
        help_text="Number of product stock units received for this batch.",
        error_messages={
            "required": "Enter quantity.",
            "invalid": "Enter a whole number.",
            "min_value": "A new batch must contain at least 1 unit.",
        },
        widget=forms.NumberInput(
            attrs={
                "min": "1",
                "step": "1",
                "inputmode": "numeric",
            }
        ),
    )

    best_before = forms.DateField(
        label="Best before",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
            },
        ),
        error_messages={
            "required": "Enter a best-before date.",
            "invalid": "Enter a valid date.",
        },
    )

    location = forms.CharField(
        max_length=120,
        label="Location",
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Shelf A1",
                "autocomplete": "off",
            }
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        set_form_field_layout(
            self,
            full=("product",),
            half=("quantity", "best_before", "location"),
        )

    @cached_property
    def variant_groups(self) -> tuple[VariantGroup, ...]:
        """For each active product with several variants, its variants on
        sale; the chosen product's group is shown."""

        chosen_product = str(self["product"].value() or "")
        chosen_variant = str(self["variant"].value() or "")
        variants_by_product: dict[int, list[ProductVariant]] = {}

        for variant in ProductVariant.objects.filter(
            product__active=True,
        ).order_by("product_id", "position", "pk"):
            variants_by_product.setdefault(variant.product_id, []).append(
                variant
            )

        return tuple(
            VariantGroup(
                product_id=product_id,
                choices=tuple(
                    VariantChoice(
                        pk=variant.pk,
                        text=variant.label,
                        checked=str(variant.pk) == chosen_variant,
                    )
                    for variant in variants
                    if variant.active
                ),
                shown=str(product_id) == chosen_product,
            )
            for product_id, variants in variants_by_product.items()
            if len(variants) > 1
        )

    @property
    def shows_variant_choice(self) -> bool:
        return bool(self["variant"].errors) or any(
            group.shown for group in self.variant_groups
        )

    def clean(self) -> dict:
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        variant = cleaned_data.get("variant")

        if product is None:
            return cleaned_data

        if variant is not None and variant.product_id != product.pk:
            self.add_error("variant", "Choose one of the product's variants.")
            return cleaned_data

        if variant is None and product.only_variant() is None:
            on_sale = list(product.variants.filter(active=True)[:2])

            if len(on_sale) == 1:
                cleaned_data["variant"] = on_sale[0]
            else:
                self.add_error(
                    "variant",
                    "Choose which variant this batch is.",
                )

        return cleaned_data


class BatchEditForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=0,
        label="Quantity",
        help_text="Set the physical stock-unit count after stock correction.",
        error_messages={
            "required": "Enter quantity.",
            "invalid": "Enter a whole number.",
            "min_value": "Quantity cannot be negative.",
        },
        widget=forms.NumberInput(
            attrs={
                "min": "0",
                "step": "1",
                "inputmode": "numeric",
            }
        ),
    )

    best_before = forms.DateField(
        label="Best before",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
            },
        ),
        error_messages={
            "required": "Enter a best-before date.",
            "invalid": "Enter a valid date.",
        },
    )

    location = forms.CharField(
        max_length=120,
        label="Location",
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Shelf A1",
                "autocomplete": "off",
            }
        ),
    )

    def __init__(self, *args, batch: InventoryBatch | None = None, **kwargs) -> None:
        self.batch = batch
        super().__init__(*args, **kwargs)

        set_form_field_layout(
            self,
            half=("quantity", "best_before", "location"),
        )


def build_batch_edit_initial_data(batch: InventoryBatch) -> dict[str, object]:
    return {
        "quantity": batch.quantity,
        "best_before": batch.best_before,
        "location": batch.location,
    }

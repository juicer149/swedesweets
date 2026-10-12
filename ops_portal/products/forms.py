from __future__ import annotations

from django import forms

from common.form_layout import (
    set_form_field_layout,
)
from products.catalog import (
    MAX_NAME_LENGTH,
    MAX_WEIGHT_PER_UNIT,
    MIN_WEIGHT_PER_UNIT,
)
from products.models import (
    Product,
)


def _configure_vegan_toggle(
    form: forms.BaseForm,
) -> None:
    field = form.fields["vegan"]

    field.tag_toggle = True
    field.tag_toggle_label = "Vegan"
    field.tag_toggle_icon = "leaf"
    field.tag_toggle_class = (
        "product-tag-toggle "
        "product-tag-toggle--vegan"
    )


def _configure_status_toggle(
    form: forms.BaseForm,
) -> None:
    field = form.fields["active"]

    field.tag_toggle = True
    field.tag_toggle_label = "Active"
    field.tag_toggle_icon = "check"
    field.tag_toggle_class = (
        "product-tag-toggle "
        "product-tag-toggle--status"
    )


class ProductForm(forms.Form):
    internal_number = forms.IntegerField(
        required=False,
        min_value=1,
        label="Catalog ID",
        help_text=(
            "Optional product number used "
            "in the customer catalog."
        ),
        error_messages={
            "invalid": (
                "Enter a whole number."
            ),
            "min_value": (
                "Catalog ID must be positive."
            ),
        },
        # Typed, never stepped: a text field that takes digits.
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. 23",
                "inputmode": "numeric",
                "pattern": "[0-9]*",
                "autocomplete": "off",
            }
        ),
    )

    manufacturer = forms.CharField(
        required=False,
        max_length=MAX_NAME_LENGTH,
        label="Manufacturer",
        help_text=(
            "Optional producer, e.g. "
            "Fazer, Cloetta, BUBS."
        ),
        error_messages={
            "max_length": (
                "Manufacturer cannot exceed "
                f"{MAX_NAME_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Fazer",
                "autocomplete": "organization",
            }
        ),
    )

    brand = forms.CharField(
        max_length=MAX_NAME_LENGTH,
        label="Brand",
        error_messages={
            "required": (
                "Please enter the brand "
                "of the product."
            ),
            "max_length": (
                "Brand name cannot exceed "
                f"{MAX_NAME_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "organization",
                "placeholder": (
                    "e.g. Tutti Frutti"
                ),
            }
        ),
    )

    name = forms.CharField(
        max_length=MAX_NAME_LENGTH,
        label="Product name",
        help_text=(
            "Swedish/internal MVP product name."
        ),
        error_messages={
            "required": (
                "Please enter the name "
                "of the product."
            ),
            "max_length": (
                "Product name cannot exceed "
                f"{MAX_NAME_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": (
                    "e.g. TYRKISK PEBER"
                ),
            }
        ),
    )

    stock_unit = forms.ChoiceField(
        choices=Product.StockUnit.choices,
        initial=Product.StockUnit.BOX,
        label="Stock unit",
        help_text=(
            "How this product is counted "
            "in inventory and orders."
        ),
        error_messages={
            "required": (
                "Choose a stock unit."
            ),
            "invalid_choice": (
                "Choose a valid stock unit."
            ),
        },
        widget=forms.RadioSelect(
            attrs={
                "class": (
                    "radio-chip-group"
                ),
            }
        ),
    )

    weight_per_unit = forms.IntegerField(
        min_value=MIN_WEIGHT_PER_UNIT,
        max_value=MAX_WEIGHT_PER_UNIT,
        label="Weight per unit",
        help_text=(
            "Stored in grams. Cannot be "
            "changed after creation."
        ),
        error_messages={
            "required": (
                "Please enter the weight "
                "per unit in grams."
            ),
            "min_value": (
                "Weight per unit must be at least "
                f"{MIN_WEIGHT_PER_UNIT} grams."
            ),
            "max_value": (
                "Weight per unit must be at most "
                f"{MAX_WEIGHT_PER_UNIT} grams."
            ),
            "invalid": (
                "Please enter a valid number "
                "for weight per unit."
            ),
        },
        widget=forms.NumberInput(
            attrs={
                "placeholder": "e.g. 3000",
                "inputmode": "numeric",
                "pattern": "[0-9]+",
                "autocomplete": "off",
            }
        ),
    )

    vegan = forms.BooleanField(
        required=False,
        label="Product attributes",
        widget=forms.CheckboxInput(
            attrs={
                "class": (
                    "product-tag-toggle__input"
                ),
            }
        ),
    )

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            **kwargs,
        )

        _configure_vegan_toggle(
            self
        )

        # The attributes have the last row to themselves (more may come).
        set_form_field_layout(
            self,
            full=(
                "vegan",
            ),
            half=(
                "internal_number",
                "manufacturer",
                "brand",
                "name",
                "stock_unit",
                "weight_per_unit",
            ),
        )


class ProductEditForm(forms.Form):
    internal_number = forms.IntegerField(
        required=False,
        min_value=1,
        label="Catalog ID",
        help_text=(
            "Optional product number used "
            "in the customer catalog."
        ),
        error_messages={
            "invalid": "Enter a whole number.",
            "min_value": (
                "Catalog ID must be positive."
            ),
        },
        # Typed, never stepped: a text field that takes digits.
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. 23",
                "inputmode": "numeric",
                "pattern": "[0-9]*",
                "autocomplete": "off",
            }
        ),
    )

    manufacturer = forms.CharField(
        required=False,
        max_length=MAX_NAME_LENGTH,
        label="Manufacturer",
        error_messages={
            "max_length": (
                "Manufacturer cannot exceed "
                f"{MAX_NAME_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Fazer",
                "autocomplete": "organization",
            }
        ),
    )

    brand = forms.CharField(
        max_length=MAX_NAME_LENGTH,
        label="Brand",
        error_messages={
            "required": (
                "Please enter the brand "
                "of the product."
            ),
            "max_length": (
                "Brand name cannot exceed "
                f"{MAX_NAME_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "autocomplete": "organization",
                "placeholder": (
                    "e.g. Tutti Frutti"
                ),
            }
        ),
    )

    name = forms.CharField(
        max_length=MAX_NAME_LENGTH,
        label="Product name",
        help_text=(
            "Swedish/internal MVP product name."
        ),
        error_messages={
            "required": (
                "Please enter the name "
                "of the product."
            ),
            "max_length": (
                "Product name cannot exceed "
                f"{MAX_NAME_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": (
                    "e.g. TYRKISK PEBER"
                ),
            }
        ),
    )

    # One switch: on (green) is active, off (muted) is inactive.
    active = forms.BooleanField(
        required=False,
        label="Product status",
        widget=forms.CheckboxInput(
            attrs={
                "class": (
                    "product-tag-toggle__input"
                ),
            }
        ),
    )

    vegan = forms.BooleanField(
        required=False,
        label="Product attributes",
        widget=forms.CheckboxInput(
            attrs={
                "class": (
                    "product-tag-toggle__input"
                ),
            }
        ),
    )

    def __init__(
        self,
        *args,
        product: Product | None = None,
        **kwargs,
    ) -> None:
        self.product = product

        super().__init__(
            *args,
            **kwargs,
        )

        _configure_vegan_toggle(
            self
        )
        _configure_status_toggle(
            self
        )

        # The status on the first row and the attributes on the last, each
        # on its own.
        set_form_field_layout(
            self,
            full=(
                "active",
                "vegan",
            ),
            half=(
                "internal_number",
                "manufacturer",
                "brand",
                "name",
            ),
        )

    @property
    def active_value(self) -> bool:
        return bool(
            self.cleaned_data["active"]
        )


def build_product_edit_initial_data(
    product: Product,
) -> dict[str, object]:
    return {
        "internal_number": (
            product.internal_number
        ),
        "manufacturer": (
            product.manufacturer
        ),
        "brand": product.brand,
        "name": product.name,
        "active": product.active,
        "vegan": product.vegan,
    }

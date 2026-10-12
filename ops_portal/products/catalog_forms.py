"""The catalog form: what the shop shows of a product.

CatalogForm holds what is the same in every language (category, picture);
one CatalogTextForm per language (prefix: its code) holds the name,
description and ingredients in that language. A field left empty falls back
in the shop (products/localization.py), and the form says to what.
"""

from __future__ import annotations

from dataclasses import dataclass

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from common.form_layout import set_form_field_layout
from products.catalog import MAX_NAME_LENGTH
from products.localization import (
    FALLBACK_LANGUAGE_CODE,
    catalog_languages,
    own_catalog_text,
)
from products.models import Product, ProductProfile
from products.services import CatalogTextChange

MAX_PRODUCT_IMAGE_BYTES = 10 * 1024 * 1024

ALLOWED_PRODUCT_IMAGE_FORMATS = frozenset({"JPEG", "PNG"})


class CatalogForm(forms.Form):
    category = forms.ChoiceField(
        required=False,
        choices=(
            ("", "Select category"),
            *ProductProfile.Category.choices,
        ),
        label="Category",
        help_text="Where the shop lists the product.",
    )

    image = forms.ImageField(
        required=False,
        label="Product image",
        help_text="Optional JPEG or PNG. Maximum file size: 10 MB.",
        widget=forms.ClearableFileInput(
            attrs={"accept": "image/jpeg,image/png"},
        ),
    )

    remove_image = forms.BooleanField(
        required=False,
        label="Remove current image",
        help_text="Remove the current product image without replacing it.",
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        set_form_field_layout(
            self,
            full=("image", "remove_image"),
            half=("category",),
        )

    def clean_image(self) -> UploadedFile | None:
        return _clean_product_image(self.cleaned_data["image"])

    def clean(self) -> dict[str, object]:
        cleaned_data = super().clean()

        if cleaned_data.get("image") and cleaned_data.get("remove_image"):
            self.add_error(
                "remove_image",
                "Choose either a new image or remove the current image.",
            )

        return cleaned_data


class CatalogTextForm(forms.Form):
    name = forms.CharField(
        required=False,
        max_length=MAX_NAME_LENGTH,
        label="Shop name",
        error_messages={
            "max_length": (
                f"The shop name cannot exceed {MAX_NAME_LENGTH} characters."
            ),
        },
        widget=forms.TextInput(
            attrs={"placeholder": "e.g. Tutti Frutti Acidulé"},
        ),
    )

    description = forms.CharField(
        required=False,
        label="Description",
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    ingredients = forms.CharField(
        required=False,
        label="Ingredients",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(
        self,
        *args,
        product: Product,
        language_code: str,
        **kwargs,
    ) -> None:
        super().__init__(*args, prefix=language_code, **kwargs)

        self.fields["name"].help_text = (
            f"Empty: the shop shows the product's own name, "
            f"{product.display_name}."
        )

        if language_code != FALLBACK_LANGUAGE_CODE:
            fallback = dict(catalog_languages())[FALLBACK_LANGUAGE_CODE]

            for field_name in ("description", "ingredients"):
                self.fields[field_name].help_text = (
                    f"Empty: the shop shows the {fallback} text."
                )

        set_form_field_layout(
            self,
            full=("name", "description", "ingredients"),
        )

    def change(self) -> CatalogTextChange:
        return CatalogTextChange(
            name=self.cleaned_data["name"],
            description=self.cleaned_data["description"],
            ingredients=self.cleaned_data["ingredients"],
        )


@dataclass(frozen=True, slots=True)
class CatalogLanguage:
    """One language tab of the catalog form."""

    code: str
    name: str
    form: CatalogTextForm

    @property
    def has_errors(self) -> bool:
        return bool(self.form.errors)


def build_catalog_languages(
    *,
    product: Product,
    data=None,
) -> tuple[CatalogLanguage, ...]:
    """A text form for each catalog language, the first language first,
    filled with what that language itself says."""

    languages = []

    for code, name in catalog_languages():
        text = own_catalog_text(product, language_code=code)

        languages.append(
            CatalogLanguage(
                code=code,
                name=name,
                form=CatalogTextForm(
                    data,
                    product=product,
                    language_code=code,
                    initial={
                        "name": text.name,
                        "description": text.description,
                        "ingredients": text.ingredients,
                    },
                ),
            )
        )

    return tuple(languages)


def build_catalog_initial_data(product: Product) -> dict[str, object]:
    profile = getattr(product, "profile", None)

    return {
        "category": profile.category if profile is not None else "",
    }


def _clean_product_image(
    image: UploadedFile | None,
) -> UploadedFile | None:
    if image is None:
        return None

    if image.size > MAX_PRODUCT_IMAGE_BYTES:
        raise ValidationError("Product image must be 10 MB or smaller.")

    pillow_image = getattr(image, "image", None)
    image_format = (getattr(pillow_image, "format", "") or "").upper()

    if image_format not in ALLOWED_PRODUCT_IMAGE_FORMATS:
        raise ValidationError("Product image must be a JPEG or PNG.")

    return image

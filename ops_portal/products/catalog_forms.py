"""The shop text form: what the shop says of a product, per language.

One CatalogTextForm per language (prefix: its code) holds the name,
description and ingredients in that language. A field left empty falls back
in the shop (products/localization.py), and the form says to what. What is
the same in every language (category, picture) is on the product form
(forms.py).
"""

from __future__ import annotations

from dataclasses import dataclass

from django import forms

from common.form_layout import set_form_field_layout
from products.catalog import MAX_NAME_LENGTH
from products.localization import (
    FALLBACK_LANGUAGE_CODE,
    catalog_languages,
    own_catalog_text,
)
from products.models import Product
from products.services import CatalogTextChange


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

"""The product page's Shop text tab: what the product's text says in each
language, to read (detail_tab_text.html).

Per language its own name, description and ingredients; a field it leaves
empty says what the shop shows instead (products/localization.py: the
product's own name, the French text). A language with no text of its own
says so, with what the shop shows, and offers to add it (the shop text
page, open on that language).
"""

from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from products.localization import (
    FALLBACK_LANGUAGE_CODE,
    catalog_languages,
    own_catalog_text,
)
from products.models import Product


@dataclass(frozen=True, slots=True)
class ShopTextField:
    label: str
    value: str
    # Empty: what the shop shows instead.
    fallback: str


@dataclass(frozen=True, slots=True)
class LanguageText:
    code: str
    name: str
    fields: tuple[ShopTextField, ...]
    # The shop text page, open on this language.
    edit_href: str

    @property
    def has_own_text(self) -> bool:
        return any(field.value for field in self.fields)

    @property
    def fallback_note(self) -> str:
        """For a language with no text of its own: what the shop shows."""

        if self.code == FALLBACK_LANGUAGE_CODE:
            return "The shop shows the product's own name, nothing more."

        fallback_name = dict(catalog_languages())[FALLBACK_LANGUAGE_CODE]

        return (
            "The shop shows the product's own name and the "
            f"{fallback_name} text."
        )


def build_language_texts(product: Product) -> tuple[LanguageText, ...]:
    """Each catalog language, the first language first."""

    languages = dict(catalog_languages())
    fallback_text = own_catalog_text(
        product,
        language_code=FALLBACK_LANGUAGE_CODE,
    )
    edit_url = reverse(
        "ops_products:edit_catalog",
        kwargs={"product_pk": product.pk},
    )
    texts = []

    for code, name in languages.items():
        own = own_catalog_text(product, language_code=code)

        texts.append(
            LanguageText(
                code=code,
                name=name,
                fields=(
                    ShopTextField(
                        label="Shop name",
                        value=own.name,
                        fallback=(
                            "The shop shows the product's own name, "
                            f"{product.display_name}."
                        ),
                    ),
                    ShopTextField(
                        label="Description",
                        value=own.description,
                        fallback=_falls_back_to(
                            code=code,
                            fallback_value=fallback_text.description,
                        ),
                    ),
                    ShopTextField(
                        label="Ingredients",
                        value=own.ingredients,
                        fallback=_falls_back_to(
                            code=code,
                            fallback_value=fallback_text.ingredients,
                        ),
                    ),
                ),
                edit_href=f"{edit_url}#{code}",
            )
        )

    return tuple(texts)


def _falls_back_to(*, code: str, fallback_value: str) -> str:
    """What the shop shows for a description or ingredients a language
    leaves empty: the French text when there is one, else none."""

    if code != FALLBACK_LANGUAGE_CODE and fallback_value:
        fallback_name = dict(catalog_languages())[FALLBACK_LANGUAGE_CODE]

        return f"The shop shows the {fallback_name} text."

    return "The shop shows none."

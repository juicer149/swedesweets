"""A product's catalog text in the language a customer reads.

Each language has its own name, description and ingredients
(ProductTranslation). Where a language has none of its own:

- the name is the product's own name (Swedish candy keeps its real name);
- the description and ingredients are those of the catalog's first
  language, French, the language they are written in first.

Languages come from settings.LANGUAGES: adding one there adds it to the
ops catalog form.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from products.models import Product, ProductTranslation

# The language the catalog is written in first: the others fall back to it.
FALLBACK_LANGUAGE_CODE = "fr"


@dataclass(frozen=True, slots=True)
class CatalogText:
    name: str
    description: str
    ingredients: str


def catalog_languages() -> tuple[tuple[str, str], ...]:
    """(code, name) of each catalog language, the first language first."""

    return tuple(
        sorted(
            settings.LANGUAGES,
            key=lambda language: language[0] != FALLBACK_LANGUAGE_CODE,
        )
    )


def own_catalog_text(
    product: Product,
    *,
    language_code: str,
) -> CatalogText:
    """What the language itself says, without falling back (the ops form)."""

    translation = _translation(product, language_code=language_code)

    if translation is None:
        return CatalogText(name="", description="", ingredients="")

    return CatalogText(
        name=translation.name,
        description=translation.description,
        ingredients=translation.ingredients,
    )


def catalog_text(
    product: Product,
    *,
    language_code: str,
) -> CatalogText:
    """What a customer reading the language sees, with the fallbacks."""

    own = own_catalog_text(product, language_code=language_code)
    fallback = (
        own_catalog_text(product, language_code=FALLBACK_LANGUAGE_CODE)
        if language_code != FALLBACK_LANGUAGE_CODE
        else own
    )

    return CatalogText(
        name=own.name or product.display_name,
        description=own.description or fallback.description,
        ingredients=own.ingredients or fallback.ingredients,
    )


def translated_product_name(
    product: Product,
    *,
    language_code: str,
) -> str:
    """Return the customer-facing product name for a language.

    Prefer prefetched translations when available to avoid per-product queries.
    Fall back to the product's normal display name when the language has no
    name of its own.
    """

    translation = _translation(product, language_code=language_code)

    if translation is None or not translation.name:
        return product.display_name

    return translation.name


def _translation(
    product: Product,
    *,
    language_code: str,
) -> ProductTranslation | None:
    prefetched_translations = getattr(
        product,
        "prefetched_translations",
        None,
    )

    if prefetched_translations is None:
        # product.translations.all() reads a prefetch_related("translations")
        # cache when there is one.
        prefetched_translations = product.translations.all()

    for translation in prefetched_translations:
        if translation.language_code == language_code:
            return translation

    return None

"""What a customer reading a language sees of a product's catalog text."""

from __future__ import annotations

import pytest

from products.localization import (
    catalog_languages,
    catalog_text,
    own_catalog_text,
    translated_product_name,
)
from products.services import CatalogTextChange, update_product_catalog
from products.tests.factories import product_factory


def _write(product, **texts):
    update_product_catalog(
        product=product,
        category="",
        texts={
            code: CatalogTextChange(**fields)
            for code, fields in texts.items()
        },
    )


def test_french_comes_first():
    assert [code for code, _name in catalog_languages()][0] == "fr"


@pytest.mark.django_db
def test_a_language_shows_its_own_text():
    product = product_factory(brand="Fazer", name="Tyrkisk Peber")
    _write(
        product,
        fr={"name": "Poivre turc", "description": "Salé.", "ingredients": "Sucre."},
        en={"name": "Turkish pepper", "description": "Salty.", "ingredients": "Sugar."},
    )

    text = catalog_text(product, language_code="en")

    assert (text.name, text.description, text.ingredients) == (
        "Turkish pepper",
        "Salty.",
        "Sugar.",
    )


@pytest.mark.django_db
def test_without_its_own_text_a_language_falls_back():
    """The name to the product's own (Swedish) name, the description and
    ingredients to French."""

    product = product_factory(brand="Fazer", name="Tyrkisk Peber")
    _write(
        product,
        fr={"name": "Poivre turc", "description": "Salé.", "ingredients": "Sucre."},
    )

    text = catalog_text(product, language_code="en")

    assert text.name == product.display_name
    assert text.description == "Salé."
    assert text.ingredients == "Sucre."
    assert own_catalog_text(product, language_code="en").description == ""


@pytest.mark.django_db
def test_a_language_with_only_a_description_keeps_the_product_name():
    product = product_factory(brand="Fazer", name="Tyrkisk Peber")
    _write(product, en={"description": "Salty."})

    assert translated_product_name(product, language_code="en") == (
        product.display_name
    )
    assert catalog_text(product, language_code="fr").description == ""

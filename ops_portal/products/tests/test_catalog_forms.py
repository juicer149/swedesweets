from __future__ import annotations

import pytest

from ops_portal.products.catalog_forms import build_catalog_languages
from products.models import ProductProfile
from products.services import CatalogTextChange, update_product_catalog
from products.tests.factories import product_factory


@pytest.mark.django_db
def test_each_language_has_its_own_form_french_first():
    product = product_factory(brand="Fazer", name="Tyrkisk Peber")
    update_product_catalog(
        product=product,
        category=ProductProfile.Category.CANDY,
        texts={
            "fr": CatalogTextChange(name="Poivre turc", description="Salé."),
        },
    )

    languages = build_catalog_languages(product=product)

    assert [language.code for language in languages] == ["fr", "en"]
    french, english = languages
    assert french.form.initial == {
        "name": "Poivre turc",
        "description": "Salé.",
        "ingredients": "",
    }
    # English has no text of its own: the form says what the shop shows.
    assert english.form.initial["description"] == ""
    assert "French text" in english.form.fields["description"].help_text
    assert product.display_name in english.form.fields["name"].help_text


@pytest.mark.django_db
def test_language_forms_read_their_own_prefixed_fields():
    product = product_factory()

    languages = build_catalog_languages(
        product=product,
        data={
            "fr-name": "Chips grill",
            "fr-description": "Croustillantes.",
            "fr-ingredients": "",
            "en-name": "",
            "en-description": "Crispy.",
            "en-ingredients": "",
        },
    )

    assert all(language.form.is_valid() for language in languages)
    assert {language.code: language.form.change() for language in languages} == {
        "fr": CatalogTextChange(
            name="Chips grill",
            description="Croustillantes.",
        ),
        "en": CatalogTextChange(description="Crispy."),
    }

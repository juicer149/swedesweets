from __future__ import annotations

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from ops_portal.products.catalog_forms import (
    CatalogForm,
    build_catalog_initial_data,
    build_catalog_languages,
)
from products.models import Product, ProductProfile
from products.services import CatalogTextChange, update_product_catalog
from products.tests.factories import product_factory


def uploaded_image(
    *,
    name: str = "product.png",
    image_format: str = "PNG",
) -> SimpleUploadedFile:
    output = BytesIO()
    Image.new("RGB", (40, 40)).save(output, format=image_format)

    return SimpleUploadedFile(
        name,
        output.getvalue(),
        content_type="image/jpeg" if image_format == "JPEG" else "image/png",
    )


def test_catalog_form_accepts_a_category_and_no_picture():
    form = CatalogForm(data={"category": ProductProfile.Category.CANDY})

    assert form.is_valid(), form.errors
    assert form.cleaned_data["category"] == ProductProfile.Category.CANDY
    assert form.cleaned_data["image"] is None
    assert form.cleaned_data["remove_image"] is False


def test_catalog_form_accepts_an_empty_category():
    form = CatalogForm(data={"category": ""})

    assert form.is_valid(), form.errors


def test_catalog_form_rejects_an_unknown_category():
    form = CatalogForm(data={"category": "drinks"})

    assert not form.is_valid()
    assert "category" in form.errors


@pytest.mark.parametrize(
    ("name", "image_format"),
    [("product.png", "PNG"), ("product.jpg", "JPEG")],
)
def test_catalog_form_accepts_png_and_jpeg(name, image_format):
    form = CatalogForm(
        data={"category": ""},
        files={"image": uploaded_image(name=name, image_format=image_format)},
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["image"].name == name


def test_catalog_form_rejects_a_file_that_is_not_a_picture():
    form = CatalogForm(
        data={"category": ""},
        files={
            "image": SimpleUploadedFile(
                "product.txt",
                b"not an image",
                content_type="text/plain",
            ),
        },
    )

    assert not form.is_valid()
    assert "image" in form.errors


def test_catalog_form_rejects_a_new_picture_and_remove_together():
    form = CatalogForm(
        data={"category": "", "remove_image": "on"},
        files={"image": uploaded_image()},
    )

    assert not form.is_valid()
    assert "remove_image" in form.errors


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
    # The page reads the product afresh, with its saved profile.
    product = Product.objects.get(pk=product.pk)
    assert build_catalog_initial_data(product) == {
        "category": ProductProfile.Category.CANDY,
    }


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

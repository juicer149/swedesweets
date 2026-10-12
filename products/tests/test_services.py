from __future__ import annotations

import pytest

from products.errors import InvalidProductData
from products.models import Product, ProductProfile, ProductTranslation
from products.services import (
    CatalogTextChange,
    create_product,
    update_product,
    update_product_active,
    update_product_catalog,
)
from products.tests.factories import product_factory


@pytest.mark.django_db
def test_create_product_creates_product_and_profile():
    result = create_product(
        internal_number=23,
        manufacturer="  Fazer   Finland ",
        brand="  Fazer ",
        name="  Tyrkisk   Peber ",
        weight_per_unit=3000,
        stock_unit=Product.StockUnit.BOX,
        vegan=True,
    )

    product = result.item

    assert result.created is True
    assert (
        result.message
        == "Product added to the catalog."
    )

    assert product.internal_number == 23
    assert product.manufacturer == "Fazer Finland"
    assert product.brand == "Fazer"
    assert product.name == "Tyrkisk Peber"
    assert product.weight_per_unit == 3000
    assert (
        product.stock_unit
        == Product.StockUnit.BOX
    )
    assert product.vegan is True
    assert product.sku == "SS-023"

    # An empty profile: the catalog is filled in on its own page.
    profile = ProductProfile.objects.get(
        product=product,
    )

    assert profile.category == ""
    assert not profile.image
    assert not profile.thumbnail


@pytest.mark.django_db
def test_create_product_accepts_piece_stock_unit():
    result = create_product(
        internal_number=24,
        brand="Cloetta",
        name="Kexchoklad",
        weight_per_unit=60,
        stock_unit=Product.StockUnit.PIECE,
    )

    assert result.created is True
    assert (
        result.item.stock_unit
        == Product.StockUnit.PIECE
    )
    assert result.item.weight_per_unit == 60


@pytest.mark.django_db
def test_create_product_accepts_empty_profile_category():
    result = create_product(
        brand="OLW",
        name="Grill Chips",
        weight_per_unit=275,
        category="",
    )

    assert result.created is True
    assert result.item.profile.category == ""


@pytest.mark.django_db
def test_create_product_rejects_invalid_profile_category():
    with pytest.raises(
        InvalidProductData,
        match="Unsupported product category",
    ):
        create_product(
            brand="Generic",
            name="Drink",
            weight_per_unit=500,
            category="drinks",
        )


@pytest.mark.django_db
def test_create_product_returns_existing_product_with_same_sku():
    first = create_product(
        brand="OLW",
        name="Grill Chips",
        weight_per_unit=275,
    )

    second = create_product(
        brand="  olw ",
        name="  Grill   Chips ",
        weight_per_unit=275,
    )

    assert second.created is False
    assert second.item == first.item
    assert (
        second.message
        == "Product already exists in the catalog."
    )
    assert Product.objects.count() == 1


@pytest.mark.django_db
def test_create_product_returns_existing_product_with_same_internal_number():
    existing = create_product(
        internal_number=11,
        brand="OLW",
        name="Grill Chips",
        weight_per_unit=275,
    )

    duplicate_number = create_product(
        internal_number=11,
        brand="Fazer",
        name="Tyrkisk Peber",
        weight_per_unit=3000,
    )

    assert duplicate_number.created is False
    assert duplicate_number.item == existing.item
    assert Product.objects.count() == 1


@pytest.mark.django_db
def test_create_product_rejects_invalid_data():
    with pytest.raises(
        InvalidProductData,
        match="brand must not be empty",
    ):
        create_product(
            brand="",
            name="Apple",
            weight_per_unit=5000,
        )

    with pytest.raises(
        InvalidProductData,
        match="weight_per_unit must be at least",
    ):
        create_product(
            brand="Generic",
            name="Apple",
            weight_per_unit=0,
        )

    with pytest.raises(
        InvalidProductData,
        match="Unsupported stock unit",
    ):
        create_product(
            brand="Generic",
            name="Apple",
            weight_per_unit=5000,
            stock_unit="pallet",
        )


@pytest.mark.django_db
def test_update_product_updates_editable_product_fields():
    product = product_factory(
        internal_number=1,
        brand="Old Brand",
        name="Old Name",
        weight_per_unit=1000,
    )

    updated = update_product(
        product=product,
        internal_number=2,
        manufacturer="  Fazer ",
        brand="  New Brand ",
        name="  New   Name ",
        active=False,
        vegan=True,
    )

    updated.refresh_from_db()

    assert updated.internal_number == 2
    assert updated.manufacturer == "Fazer"
    assert updated.brand == "New Brand"
    assert updated.name == "New Name"
    assert updated.active is False
    assert updated.vegan is True


@pytest.mark.django_db
def test_update_product_does_not_change_the_catalog():
    product = product_factory()
    update_product_catalog(
        product=product,
        category=ProductProfile.Category.CANDY,
        texts={"fr": CatalogTextChange(description="Bonbons.")},
    )
    profile = product.profile
    profile.image.name = "products/originals/example.png"
    profile.save(update_fields=["image"])

    update_product(
        product=product,
        internal_number=product.internal_number,
        manufacturer=product.manufacturer,
        brand=product.brand,
        name="Updated name",
        active=product.active,
        vegan=product.vegan,
    )

    profile.refresh_from_db()
    assert profile.category == ProductProfile.Category.CANDY
    assert profile.image.name == "products/originals/example.png"
    assert product.translations.get().description == "Bonbons."


@pytest.mark.django_db
def test_update_product_catalog_saves_category_and_text_per_language():
    product = product_factory()

    update_product_catalog(
        product=product,
        category=ProductProfile.Category.CHIPS,
        texts={
            "fr": CatalogTextChange(
                name="  Chips   Grill ",
                description="  Croustillantes.  ",
                ingredients="  Pommes de terre.  ",
            ),
            "en": CatalogTextChange(description="Crispy."),
        },
    )

    product.profile.refresh_from_db()
    assert product.profile.category == ProductProfile.Category.CHIPS

    by_language = {
        translation.language_code: translation
        for translation in ProductTranslation.objects.filter(product=product)
    }
    assert by_language["fr"].name == "Chips Grill"
    assert by_language["fr"].description == "Croustillantes."
    assert by_language["fr"].ingredients == "Pommes de terre."
    assert by_language["en"].name == ""
    assert by_language["en"].description == "Crispy."


@pytest.mark.django_db
def test_an_empty_language_has_no_text_of_its_own():
    product = product_factory()
    update_product_catalog(
        product=product,
        category="",
        texts={"en": CatalogTextChange(name="Grill crisps")},
    )

    update_product_catalog(
        product=product,
        category="",
        texts={"en": CatalogTextChange()},
    )

    assert not product.translations.exists()


@pytest.mark.django_db
def test_a_language_left_out_is_not_changed():
    product = product_factory()
    update_product_catalog(
        product=product,
        category="",
        texts={"fr": CatalogTextChange(description="Bonbons.")},
    )

    update_product_catalog(
        product=product,
        category="",
        texts={"en": CatalogTextChange(description="Sweets.")},
    )

    assert product.translations.get(language_code="fr").description == (
        "Bonbons."
    )


@pytest.mark.django_db
def test_update_product_catalog_rejects_an_unknown_language():
    product = product_factory()

    with pytest.raises(InvalidProductData, match="Unknown catalog language"):
        update_product_catalog(
            product=product,
            category="",
            texts={"de": CatalogTextChange(description="Süßigkeiten.")},
        )


@pytest.mark.django_db
def test_update_product_catalog_rejects_invalid_profile_category():
    product = product_factory()

    with pytest.raises(
        InvalidProductData,
        match="Unsupported product category",
    ):
        update_product_catalog(
            product=product,
            category="drinks",
            texts={},
        )


@pytest.mark.django_db
def test_update_product_does_not_change_sku():
    product = product_factory(
        internal_number=1,
        brand="Old Brand",
        name="Old Name",
        weight_per_unit=1000,
    )

    original_sku = product.sku

    updated = update_product(
        product=product,
        internal_number=2,
        manufacturer="",
        brand="New Brand",
        name="New Name",
        active=True,
        vegan=False,
    )

    assert updated.sku == original_sku


@pytest.mark.django_db
def test_update_product_rejects_duplicate_internal_number():
    product_factory(
        internal_number=1,
    )

    product = product_factory(
        internal_number=2,
        brand="Fazer",
        name="Tyrkisk Peber",
        weight_per_unit=3000,
    )

    with pytest.raises(
        InvalidProductData,
        match="Product number 1 already exists",
    ):
        update_product(
            product=product,
            internal_number=1,
            manufacturer="",
            brand="Fazer",
            name="Tyrkisk Peber",
            active=True,
            vegan=False,
        )


@pytest.mark.django_db
def test_update_product_active_updates_only_status():
    product = product_factory()

    assert product.active is True

    updated = update_product_active(
        product=product,
        active=False,
    )

    updated.refresh_from_db()

    assert updated.active is False

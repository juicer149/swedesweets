from __future__ import annotations

import pytest

from products.errors import InvalidProductData
from products.models import Product
from products.tests.factories import product_factory


@pytest.mark.django_db
def test_product_save_normalizes_fields_and_generates_sku():
    product = Product.objects.create(
        brand="  olw ",
        name="  Grill   Chips ",
        manufacturer="  Orkla   Snacks ",
        weight_per_unit=275,
    )

    assert product.brand == "olw"
    assert product.name == "Grill Chips"
    assert product.manufacturer == "Orkla Snacks"
    assert product.sku == "OLW-GRILL_CHIPS-275"
    assert product.stock_unit == Product.StockUnit.BOX


@pytest.mark.django_db
def test_product_save_generates_internal_number_sku():
    product = Product.objects.create(
        internal_number=7,
        brand="OLW",
        name="Grill Chips",
        weight_per_unit=275,
    )

    assert product.sku == "SS-007"


@pytest.mark.django_db
def test_product_weight_per_unit_cannot_change_after_creation():
    product = product_factory(weight_per_unit=275)

    product.weight_per_unit = 500

    with pytest.raises(
        InvalidProductData,
        match="weight_per_unit cannot be changed after product creation",
    ):
        product.save(update_fields=["weight_per_unit"])


@pytest.mark.django_db
def test_product_stock_unit_cannot_change_after_creation():
    product = product_factory(stock_unit=Product.StockUnit.BOX)

    product.stock_unit = Product.StockUnit.PIECE

    with pytest.raises(
        InvalidProductData,
        match="stock_unit cannot be changed after product creation",
    ):
        product.save(update_fields=["stock_unit"])


@pytest.mark.django_db
def test_product_sku_cannot_change_after_creation():
    product = product_factory()

    product.sku = "CUSTOM-SKU"

    with pytest.raises(
        InvalidProductData,
        match="sku cannot be changed after product creation",
    ):
        product.save(update_fields=["sku"])


@pytest.mark.django_db
def test_product_catalog_fields_can_change_without_changing_sku():
    product = product_factory(
        internal_number=12,
        brand="Old Brand",
        name="Old Name",
        weight_per_unit=1000,
    )

    original_sku = product.sku

    product.brand = "New Brand"
    product.name = "New Name"
    product.save(update_fields=["brand", "name"])

    product.refresh_from_db()

    assert product.brand == "New Brand"
    assert product.name == "New Name"
    assert product.sku == original_sku


@pytest.mark.django_db
def test_display_name_returns_brand_and_product_name():
    product = product_factory(brand="Tyrkisk Peber", name="Original")

    assert product.display_name == "Tyrkisk Peber — Original"


@pytest.mark.django_db
def test_catalog_label_includes_code_display_name_and_weight():
    product = product_factory(
        internal_number=23,
        brand="Tyrkisk Peber",
        name="Original",
        weight_per_unit=2200,
    )

    assert product.catalog_label == "#23 · Tyrkisk Peber — Original · 2200 g / Box"


@pytest.mark.django_db
def test_product_formats_stock_quantity_label_for_boxes():
    product = product_factory(stock_unit=Product.StockUnit.BOX)

    assert product.stock_quantity_label(1) == "1 box"
    assert product.stock_quantity_label(2) == "2 boxes"


@pytest.mark.django_db
def test_product_formats_stock_quantity_label_for_pieces():
    product = product_factory(stock_unit=Product.StockUnit.PIECE)

    assert product.stock_quantity_label(1) == "1 piece"
    assert product.stock_quantity_label(2) == "2 pieces"


@pytest.mark.django_db
def test_product_profile_string_uses_product_sku():
    product = product_factory(internal_number=9)

    assert str(product.profile) == "SS-009"

from __future__ import annotations

import pytest

from ops_portal.products.forms import (
    ProductEditForm,
    ProductForm,
    build_product_edit_initial_data,
)
from products.models import Product, ProductProfile
from products.tests.factories import product_factory


def valid_product_form_data(
    **overrides,
):
    data = {
        "internal_number": "",
        "manufacturer": "Fazer",
        "brand": "Fazer",
        "name": "Tyrkisk Peber",
        "stock_unit": (
            Product.StockUnit.BOX
        ),
        "weight_per_unit": "3000",
        "vegan": "on",
    }

    data.update(
        overrides
    )

    return data


def valid_product_edit_form_data(
    **overrides,
):
    data = {
        "internal_number": "23",
        "manufacturer": "Fazer",
        "brand": "Fazer",
        "name": "Tyrkisk Peber",
        "active": "on",
        "vegan": "on",
    }

    data.update(
        overrides
    )

    return data


def test_product_form_accepts_valid_data():
    form = ProductForm(
        data=valid_product_form_data(),
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data == {
        "internal_number": None,
        "manufacturer": "Fazer",
        "brand": "Fazer",
        "name": "Tyrkisk Peber",
        "stock_unit": Product.StockUnit.BOX,
        "weight_per_unit": 3000,
        "vegan": True,
    }


def test_the_product_forms_leave_the_shop_text_to_its_own_page():
    text_fields = {
        "customer_facing_name_fr",
        "description",
        "ingredients",
    }

    assert not text_fields & set(ProductForm().fields)
    assert not text_fields & set(ProductEditForm().fields)
    # Editing, the product's card also has its category and picture (a
    # picture is changed, never removed there); adding, not yet.
    assert {"category", "image"} <= set(ProductEditForm().fields)
    assert "remove_image" not in ProductEditForm().fields
    assert not {"category", "image"} & set(ProductForm().fields)


def _uploaded_image(*, name="product.png", image_format="PNG"):
    from io import BytesIO

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    output = BytesIO()
    Image.new("RGB", (40, 40)).save(output, format=image_format)

    return SimpleUploadedFile(
        name,
        output.getvalue(),
        content_type="image/jpeg" if image_format == "JPEG" else "image/png",
    )


@pytest.mark.parametrize(
    ("name", "image_format"),
    [("product.png", "PNG"), ("product.jpg", "JPEG")],
)
def test_product_edit_form_takes_a_png_or_jpeg_picture(name, image_format):
    form = ProductEditForm(
        data=valid_product_edit_form_data(),
        files={"image": _uploaded_image(name=name, image_format=image_format)},
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["image"].name == name


def test_product_edit_form_refuses_a_file_that_is_not_a_picture():
    from django.core.files.uploadedfile import SimpleUploadedFile

    form = ProductEditForm(
        data=valid_product_edit_form_data(),
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


def test_product_edit_form_category_is_optional_but_known():
    assert ProductEditForm(
        data=valid_product_edit_form_data(category=""),
    ).is_valid()
    assert ProductEditForm(
        data=valid_product_edit_form_data(category=ProductProfile.Category.CANDY),
    ).is_valid()

    form = ProductEditForm(data=valid_product_edit_form_data(category="drinks"))

    assert not form.is_valid()
    assert "category" in form.errors


def test_product_form_accepts_piece_stock_unit():
    form = ProductForm(
        data=valid_product_form_data(
            stock_unit=(
                Product.StockUnit.PIECE
            ),
        )
    )

    assert form.is_valid(), form.errors
    assert (
        form.cleaned_data["stock_unit"]
        == Product.StockUnit.PIECE
    )


def test_product_form_rejects_missing_required_fields():
    form = ProductForm(
        data=valid_product_form_data(
            brand="",
            name="",
        )
    )

    assert not form.is_valid()
    assert "brand" in form.errors
    assert "name" in form.errors


def test_product_form_rejects_invalid_weight_per_unit():
    form = ProductForm(
        data=valid_product_form_data(
            weight_per_unit="0",
        )
    )

    assert not form.is_valid()
    assert (
        "weight_per_unit"
        in form.errors
    )


def test_product_form_rejects_invalid_stock_unit():
    form = ProductForm(
        data=valid_product_form_data(
            stock_unit="pallet",
        )
    )

    assert not form.is_valid()
    assert "stock_unit" in form.errors


def test_product_form_configures_vegan_toggle_metadata():
    form = ProductForm()

    field = form.fields["vegan"]

    assert field.tag_toggle is True
    assert (
        field.tag_toggle_label
        == "Vegan"
    )
    assert (
        field.tag_toggle_icon
        == "leaf"
    )


def test_product_edit_form_switch_off_is_inactive():
    data = valid_product_edit_form_data()
    del data["active"]

    form = ProductEditForm(data=data)

    assert form.is_valid(), form.errors
    assert form.active_value is False


def test_product_edit_form_switch_on_is_active():
    form = ProductEditForm(data=valid_product_edit_form_data())

    assert form.is_valid(), form.errors
    assert form.active_value is True


def test_product_edit_form_accepts_valid_data():
    form = ProductEditForm(
        data=valid_product_edit_form_data(),
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["internal_number"] == 23
    assert form.active_value is True


@pytest.mark.django_db
def test_build_product_edit_initial_data():
    product = product_factory(
        internal_number=23,
        manufacturer="Fazer",
        brand="Fazer",
        name="Tyrkisk Peber",
        weight_per_unit=3000,
        vegan=True,
    )

    assert build_product_edit_initial_data(product) == {
        "internal_number": 23,
        "manufacturer": "Fazer",
        "brand": "Fazer",
        "name": "Tyrkisk Peber",
        "active": True,
        "vegan": True,
        # No category chosen yet.
        "category": "",
    }


def test_status_and_attributes_have_rows_of_their_own():
    from common.form_layout import FORM_FIELD_FULL, FORM_FIELD_HALF

    edit_form = ProductEditForm()

    assert edit_form.fields["active"].layout_class == FORM_FIELD_FULL
    assert edit_form.fields["vegan"].layout_class == FORM_FIELD_FULL
    assert edit_form.fields["internal_number"].layout_class == FORM_FIELD_HALF
    assert ProductForm().fields["vegan"].layout_class == FORM_FIELD_FULL

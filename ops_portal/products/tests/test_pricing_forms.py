from __future__ import annotations

from decimal import Decimal

import pytest

from ops_portal.products.pricing_forms import (
    ProductPricingForm,
)

# A switch that is on is sent as "on"; one that is off is not sent.
ON = "on"
OFF = None


def valid_pricing_form_data(
    **overrides,
) -> dict[str, str]:
    data = {
        "business_eur": "",
        "business_sek": "",
        "retail_eur": "",
        "retail_sek": "",
    }
    data.update(overrides)

    return {
        key: value
        for key, value in data.items()
        if value is not None
    }


def test_product_pricing_form_accepts_empty_pricing():
    form = ProductPricingForm(
        data=valid_pricing_form_data(),
    )

    assert form.is_valid(), form.errors

    assert form.cleaned_data["business_eur"] is None
    assert form.cleaned_data["business_sek"] is None
    assert form.cleaned_data["business_active"] is False
    assert form.business_enabled is False

    assert form.cleaned_data["retail_eur"] is None
    assert form.cleaned_data["retail_sek"] is None
    assert form.cleaned_data["retail_active"] is False
    assert form.retail_enabled is False


def test_product_pricing_form_accepts_disabled_configured_pricing():
    form = ProductPricingForm(
        data=valid_pricing_form_data(
            business_eur="7.50",
            business_active=OFF,
        )
    )

    assert form.is_valid(), form.errors

    assert (
        form.cleaned_data["business_eur"]
        == Decimal("7.50")
    )
    assert form.business_enabled is False


def test_product_pricing_form_accepts_enabled_business_pricing():
    form = ProductPricingForm(
        data=valid_pricing_form_data(
            business_eur="7.50",
            business_active=ON,
        )
    )

    assert form.is_valid(), form.errors

    assert (
        form.cleaned_data["business_eur"]
        == Decimal("7.50")
    )
    assert form.cleaned_data["business_active"] is True
    assert form.business_enabled is True


def test_product_pricing_form_accepts_enabled_retail_pricing():
    form = ProductPricingForm(
        data=valid_pricing_form_data(
            retail_sek="99.00",
            retail_active=ON,
        )
    )

    assert form.is_valid(), form.errors

    assert (
        form.cleaned_data["retail_sek"]
        == Decimal("99.00")
    )
    assert form.cleaned_data["retail_active"] is True
    assert form.retail_enabled is True


def test_product_pricing_form_accepts_multiple_currencies():
    form = ProductPricingForm(
        data=valid_pricing_form_data(
            business_eur="7.00",
            business_sek="79.00",
            business_active=ON,
            retail_eur="9.00",
            retail_sek="99.00",
            retail_active=ON,
        )
    )

    assert form.is_valid(), form.errors

    assert (
        form.cleaned_data["business_eur"]
        == Decimal("7.00")
    )
    assert (
        form.cleaned_data["business_sek"]
        == Decimal("79.00")
    )
    assert (
        form.cleaned_data["retail_eur"]
        == Decimal("9.00")
    )
    assert (
        form.cleaned_data["retail_sek"]
        == Decimal("99.00")
    )

    assert form.business_enabled is True
    assert form.retail_enabled is True


def test_product_pricing_form_accepts_active_business_without_amount():
    """Business status is B2B availability; the standard offer may be unpriced."""

    form = ProductPricingForm(
        data=valid_pricing_form_data(
            business_active=ON,
        )
    )

    assert form.is_valid(), form.errors
    assert form.business_enabled is True
    assert form.pricing_values()["business_eur"] is None


def test_a_new_product_starts_sold_to_business_only():
    form = ProductPricingForm()

    assert form["business_active"].value() is True
    assert not form["retail_active"].value()


def test_product_pricing_form_rejects_active_retail_without_amount():
    form = ProductPricingForm(
        data=valid_pricing_form_data(
            retail_active=ON,
        )
    )

    assert not form.is_valid()
    assert "retail_active" in form.errors


def test_product_pricing_form_exposes_service_values():
    form = ProductPricingForm(
        data=valid_pricing_form_data(
            business_eur="7.00",
            business_sek="79.00",
            business_active=ON,
            retail_eur="9.00",
            retail_active=OFF,
        )
    )

    assert form.is_valid(), form.errors

    assert form.pricing_values() == {
        "business_eur": Decimal("7.00"),
        "business_sek": Decimal("79.00"),
        "business_enabled": True,
        "retail_eur": Decimal("9.00"),
        "retail_sek": None,
        "retail_enabled": False,
    }


@pytest.mark.parametrize(
    "field_name",
    [
        "business_eur",
        "business_sek",
        "retail_eur",
        "retail_sek",
    ],
)
def test_product_pricing_form_rejects_zero_price(
    field_name,
):
    form = ProductPricingForm(
        data=valid_pricing_form_data(
            **{
                field_name: "0.00",
            }
        )
    )

    assert not form.is_valid()
    assert field_name in form.errors


@pytest.mark.parametrize(
    "field_name",
    [
        "business_eur",
        "business_sek",
        "retail_eur",
        "retail_sek",
    ],
)
def test_product_pricing_form_rejects_more_than_two_decimal_places(
    field_name,
):
    form = ProductPricingForm(
        data=valid_pricing_form_data(
            **{
                field_name: "9.999",
            }
        )
    )

    assert not form.is_valid()
    assert field_name in form.errors


def test_product_pricing_form_status_is_one_switch_per_channel():
    form = ProductPricingForm()

    for field_name in ("business_active", "retail_active"):
        field = form.fields[field_name]

        assert field.tag_toggle is True
        assert field.tag_toggle_label == "Active"
        assert field.widget.input_type == "checkbox"

    # The switch comes before the channel's prices.
    names = list(form.fields)
    assert names.index("business_active") < names.index("business_eur")
    assert names.index("retail_active") < names.index("retail_eur")

"""Variants and prices of an ops product: listed on the product page,
changed on the edit form (each saved row behind its own lock in the page)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.forms import CheckboxInput, FileInput
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from pricing.models import CommercialPrice, PriceAmount
from pricing.product_configuration import update_product_standard_pricing
from products.tests.factories import product_factory, variant_factory

RETAIL = CommercialPrice.Channel.RETAIL
BUSINESS = CommercialPrice.Channel.BUSINESS


def _price(variant, channel):
    return (
        variant.commercial_prices.get(batch__isnull=True, channel=channel)
        .amounts.get(currency=PriceAmount.Currency.EUR)
        .price
    )


def _detail_url(product):
    return reverse("ops_products:detail", kwargs={"product_pk": product.pk})


def _edit_url(product):
    return reverse("ops_products:edit", kwargs={"product_pk": product.pk})


def _form_values(form) -> dict[str, str]:
    """What the browser would send for a form as the page drew it."""

    data: dict[str, str] = {}

    for field in form:
        widget = field.field.widget
        value = field.value()

        if isinstance(widget, FileInput):
            continue

        if isinstance(widget, CheckboxInput):
            if value:
                data[field.html_name] = "on"
            continue

        data[field.html_name] = "" if value is None else str(value)

    return data


def _page_post_data(response) -> dict[str, str]:
    context = response.context
    formset = context["variant_formset"]

    data = {
        **_form_values(context["form"]),
        **_form_values(context["channels_form"]),
        **_form_values(formset.management_form),
    }

    for row in formset:
        data |= _form_values(row)

    return data


@pytest.mark.django_db
def test_the_product_page_lists_its_variants_with_their_stock(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=601)
    medium = variant_factory(product=product, label="M", first_label="S")
    batch_factory(
        product=product,
        variant=product.variants.get(label="S"),
        today=TODAY,
        batch_id="H-1",
        quantity=4,
    )
    medium.active = False
    medium.save(update_fields=["active"])

    response = client.get(_detail_url(product))
    lines = response.context["variant_lines"]

    assert [line.name for line in lines] == ["S", "M"]
    # S has the batch; M has none.
    assert [line.aside for line in lines] == ["4 boxes", "0 boxes"]
    assert "Paused" in [meta.text for meta in lines[1].metas]
    assert response.context["variant_labels"] == "S · M"
    assert response.context["has_several_variants"] is True


@pytest.mark.django_db
def test_a_product_with_one_variant_shows_it_as_one(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=602)

    response = client.get(_detail_url(product))

    assert [line.name for line in response.context["variant_lines"]] == [
        "One variant",
    ]
    assert "product-variants" in response.content.decode()


@pytest.mark.django_db
def test_saving_the_page_as_it_came_changes_nothing(client):
    """The locks keep hands off in the page; the fields are still sent as
    they were, so a save without changes leaves everything as it is."""

    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=603)
    update_product_standard_pricing(
        product=product,
        business_eur=Decimal("1.90"),
        business_sek=None,
        business_enabled=True,
        retail_eur=Decimal("2.50"),
        retail_sek=None,
        retail_enabled=True,
    )

    page = client.get(_edit_url(product))
    response = client.post(_edit_url(product), _page_post_data(page))

    assert response.status_code == 302
    assert response.url == _edit_url(product)
    variant = product.variants.get()
    assert variant.label == ""
    assert _price(variant, RETAIL) == Decimal("2.50")
    assert _price(variant, BUSINESS) == Decimal("1.90")


@pytest.mark.django_db
def test_the_page_opens_with_saved_rows_and_the_product_locked(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=607)
    variant_factory(product=product, label="M", first_label="S")

    response = client.get(_edit_url(product))
    content = response.content.decode()

    # The product's data and each saved variant behind a lock.
    assert content.count("data-lock-button") == 3
    assert content.count("data-lockable inert") == 3
    # Channel switches head the price columns; "All variants" under them.
    assert 'name="retail_active"' in content
    assert 'name="all_retail_eur"' in content
    assert 'data-currency-choice="sek"' in content
    assert [section.key for section in response.context["form_sections"]] == [
        "product",
        "variants",
    ]


@pytest.mark.django_db
def test_adding_a_variant_names_the_first_and_prices_both(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=604)

    page = client.get(_edit_url(product))
    data = _page_post_data(page)
    data |= {
        "variants-TOTAL_FORMS": "2",
        "variants-0-label": "M",
        "variants-0-position": "2",
        "variants-0-retail_eur": "4.50",
        "variants-1-label": "S",
        "variants-1-position": "1",
        "variants-1-weight_per_unit": "300",
        "variants-1-active": "on",
        "variants-1-retail_eur": "2.50",
        "retail_active": "on",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 302
    assert [
        (variant.label, variant.position, variant.weight_per_unit)
        for variant in product.variants.all()
    ] == [
        ("S", 1, 300),
        ("M", 2, product.weight_per_unit),
    ]
    small, medium = product.variants.all()
    assert _price(small, RETAIL) == Decimal("2.50")
    assert _price(medium, RETAIL) == Decimal("4.50")


@pytest.mark.django_db
def test_all_variants_overwrites_every_variants_price(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=608)
    variant_factory(product=product, label="M", first_label="S")

    page = client.get(_edit_url(product))
    data = _page_post_data(page)
    data |= {
        "variants-0-business_eur": "1.00",
        "variants-1-business_eur": "2.00",
        "all_business_eur": "3.40",
        "business_active": "on",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 302
    assert [
        _price(variant, BUSINESS) for variant in product.variants.all()
    ] == [Decimal("3.40"), Decimal("3.40")]

    # Never filled in: the next page starts with it empty.
    page = client.get(_edit_url(product))
    assert page.context["channels_form"]["all_business_eur"].value() is None


@pytest.mark.django_db
def test_retail_on_without_any_price_is_refused(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=609)

    page = client.get(_edit_url(product))
    data = _page_post_data(page) | {"retail_active": "on"}

    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    assert "at least one variant" in str(
        response.context["channels_form"].non_field_errors()
    )


@pytest.mark.django_db
def test_two_variants_need_a_label_each(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=605)

    page = client.get(_edit_url(product))
    data = _page_post_data(page)
    data |= {
        "variants-TOTAL_FORMS": "2",
        "variants-1-label": "L",
        "variants-1-weight_per_unit": "300",
        "variants-1-active": "on",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    (first, _second) = response.context["variant_formset"].forms
    assert "each needs a label" in str(first.errors)
    # The row with the error opens unlocked.
    assert first.starts_locked is False
    assert product.variants.count() == 1


@pytest.mark.django_db
def test_a_used_variant_cannot_be_deleted(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=606)
    variant_factory(product=product, label="M", first_label="S")
    batch_factory(
        product=product,
        variant=product.variants.get(label="S"),
        today=TODAY,
        batch_id="H-1",
    )

    page = client.get(_edit_url(product))
    data = _page_post_data(page)
    data |= {
        "variants-0-delete": "on",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    assert "pause it instead" in str(
        response.context["variant_formset"].forms[0].errors
    )
    assert product.variants.count() == 2


@pytest.mark.django_db
def test_the_product_page_shows_each_variants_prices(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=610)
    variant_factory(product=product, label="M", first_label="S")

    page = client.get(_edit_url(product))
    data = _page_post_data(page) | {
        "variants-0-retail_eur": "2.50",
        "variants-1-retail_eur": "4.50",
        "retail_active": "on",
    }
    client.post(_edit_url(product), data)

    response = client.get(_detail_url(product))
    small, medium = response.context["variant_lines"]
    meta_texts = [[meta.text for meta in line.metas] for line in (small, medium)]

    assert "Retail 2.50 EUR" in meta_texts[0]
    assert "Retail 4.50 EUR" in meta_texts[1]
    assert response.context["pricing"].retail.enabled is True

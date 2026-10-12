"""Variants and prices of an ops product: listed on the product page,
changed on the edit form; each variant at the product's price or, with
its price tag on, its own."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.forms import CheckboxInput, FileInput
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from pricing.models import CommercialPrice, PriceAmount
from pricing.product_configuration import (
    VariantPrices,
    VariantPricing,
    update_product_standard_pricing,
    update_variants_pricing,
)
from products.tests.factories import product_factory, variant_factory

RETAIL = CommercialPrice.Channel.RETAIL
BUSINESS = CommercialPrice.Channel.BUSINESS


def _price(variant, channel):
    return (
        variant.commercial_prices.get(batch__isnull=True, channel=channel)
        .amounts.get(currency=PriceAmount.Currency.EUR)
        .price
    )


def _enabled(variant, channel):
    return variant.commercial_prices.get(
        batch__isnull=True,
        channel=channel,
    ).enabled


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
        **_form_values(context["prices_form"]),
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
    """A save without changes leaves everything as it is (and asks for no
    password)."""

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
    assert variant.active is True
    assert _price(variant, RETAIL) == Decimal("2.50")
    assert _price(variant, BUSINESS) == Decimal("1.90")
    assert _enabled(variant, RETAIL) and _enabled(variant, BUSINESS)


@pytest.mark.django_db
def test_the_page_opens_with_its_sections_open(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=607)
    variant_factory(product=product, label="M", first_label="S")

    response = client.get(_edit_url(product))
    content = response.content.decode()

    # No locks: the sections open as they are.
    assert "data-lock" not in content
    assert " inert" not in content
    assert "Variants and offers" in content
    # Each row's sales channels, price and arrows; the product's price; the
    # EUR / SEK tabs.
    assert 'name="variants-1-retail"' in content
    assert 'name="variants-1-own_price"' in content
    # No SKU line on the cards (the product page has them).
    assert "variant-row__sku" not in content
    # Each price says its channel (hidden while that channel is off).
    assert 'data-price-channel="business"' in content
    # No template comment leaks into the page.
    assert "{#" not in content
    assert 'name="product_retail_eur"' in content
    assert 'role="tab" aria-selected="false" data-currency-choice="sek"' in content
    assert "individual_prices" not in content
    assert "data-variant-up" in content
    assert "data-variant-handle" not in content
    assert "data-variant-add" in content
    assert [section.key for section in response.context["form_sections"]] == [
        "product",
        "variants",
    ]


@pytest.mark.django_db
def test_one_price_for_the_product_is_every_variants(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=608)
    variant_factory(product=product, label="M", first_label="S")

    page = client.get(_edit_url(product))
    data = _page_post_data(page) | {
        "product_retail_eur": "4.50",
        "product_business_eur": "3.40",
        "variants-0-retail": "on",
        "variants-1-retail": "on",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 302
    for variant in product.variants.all():
        assert _price(variant, RETAIL) == Decimal("4.50")
        assert _price(variant, BUSINESS) == Decimal("3.40")

    page = client.get(_edit_url(product))
    assert page.context["prices_form"]["product_retail_eur"].value() == (
        Decimal("4.50")
    )
    assert [
        row["own_price"].value() for row in page.context["variant_formset"]
    ] == [False, False]


@pytest.mark.django_db
def test_a_variant_with_its_price_tag_on_keeps_its_own_price(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=609)
    variant_factory(product=product, label="M", first_label="S")

    page = client.get(_edit_url(product))
    data = _page_post_data(page) | {
        "product_retail_eur": "2.50",
        "product_business_eur": "3.40",
        "variants-0-retail": "on",
        "variants-1-retail": "on",
        "variants-1-own_price": "on",
        "variants-1-retail_eur": "4.50",
        "variants-1-business_eur": "2.00",
        # Typed while its tag was on, then switched off: not used.
        "variants-0-retail_eur": "9.99",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 302
    small, medium = product.variants.all()
    assert _price(small, RETAIL) == Decimal("2.50")
    assert _price(small, BUSINESS) == Decimal("3.40")
    assert _price(medium, RETAIL) == Decimal("4.50")
    assert _price(medium, BUSINESS) == Decimal("2.00")

    # The page opens the same: S at the product's price, M with its own.
    page = client.get(_edit_url(product))
    assert page.context["prices_form"]["product_retail_eur"].value() == (
        Decimal("2.50")
    )
    assert [
        row["own_price"].value() for row in page.context["variant_formset"]
    ] == [False, True]


@pytest.mark.django_db
def test_the_product_price_is_the_one_most_variants_share(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=614)
    medium = variant_factory(product=product, label="M", first_label="S")
    large = variant_factory(product=product, label="L")
    small = product.variants.get(label="S")

    def pricing(retail):
        return VariantPricing(
            retail_enabled=True,
            business_enabled=True,
            prices=VariantPrices(retail_eur=Decimal(retail)),
        )

    update_variants_pricing(
        product=product,
        pricing={
            small.pk: pricing("2.00"),
            medium.pk: pricing("3.00"),
            large.pk: pricing("3.00"),
        },
    )

    page = client.get(_edit_url(product))

    assert page.context["prices_form"]["product_retail_eur"].value() == (
        Decimal("3.00")
    )
    assert [
        row["own_price"].value() for row in page.context["variant_formset"]
    ] == [True, False, False]


@pytest.mark.django_db
def test_sales_channels_are_each_variants_and_neither_pauses_it(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=610)
    variant_factory(product=product, label="M", first_label="S")

    page = client.get(_edit_url(product))
    data = _page_post_data(page) | {
        "product_retail_eur": "4.50",
        "variants-0-retail": "on",
        "variants-0-business": "on",
    }
    data.pop("variants-1-retail", None)
    data.pop("variants-1-business", None)

    response = client.post(_edit_url(product), data)

    assert response.status_code == 302
    small, medium = product.variants.all()
    assert small.active is True
    assert _enabled(small, RETAIL) and _enabled(small, BUSINESS)
    assert medium.active is False
    assert not _enabled(medium, BUSINESS)


@pytest.mark.django_db
def test_an_active_product_needs_a_variant_in_a_channel(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=611)

    page = client.get(_edit_url(product))
    data = _page_post_data(page)
    data.pop("variants-0-retail", None)
    data.pop("variants-0-business", None)

    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    assert "needs a variant in a sales channel" in str(
        response.context["variant_formset"].non_form_errors()
    )


@pytest.mark.django_db
def test_sold_in_retail_needs_a_price(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=612)
    variant_factory(product=product, label="M", first_label="S")

    # At the product's price: said on the product's price.
    page = client.get(_edit_url(product))
    data = _page_post_data(page) | {"variants-0-retail": "on"}
    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    assert "product_retail_eur" in response.context["prices_form"].errors

    # With its own price (and none for the product to fall back on): said
    # on the variant's own line.
    data |= {"variants-0-own_price": "on"}
    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    first, _second = response.context["variant_formset"].forms
    assert "retail_eur" in first.errors


@pytest.mark.django_db
def test_adding_a_variant_names_the_first(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=604)

    page = client.get(_edit_url(product))
    data = _page_post_data(page)
    data |= {
        "variants-TOTAL_FORMS": "2",
        "variants-0-label": "M",
        "variants-0-position": "2",
        "variants-1-label": "S",
        "variants-1-position": "1",
        "variants-1-weight_per_unit": "300",
        "variants-1-business": "on",
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
    assert _enabled(product.variants.get(label="S"), BUSINESS)


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
        "variants-1-business": "on",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    (first, _second) = response.context["variant_formset"].forms
    assert "each needs a label" in str(first.errors)
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

    assert "Weight fixed: S has stock or orders." in page.content.decode()

    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    assert "switch its channels off instead" in str(
        response.context["variant_formset"].forms[0].errors
    )
    assert product.variants.count() == 2


@pytest.mark.django_db
def test_the_product_page_shows_each_variants_prices(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=613)
    variant_factory(product=product, label="M", first_label="S")

    page = client.get(_edit_url(product))
    data = _page_post_data(page) | {
        "variants-0-own_price": "on",
        "variants-0-retail": "on",
        "variants-0-retail_eur": "2.50",
        "variants-1-own_price": "on",
        "variants-1-retail": "on",
        "variants-1-retail_eur": "4.50",
    }
    client.post(_edit_url(product), data)

    response = client.get(_detail_url(product))
    small, medium = response.context["variant_lines"]
    meta_texts = [[meta.text for meta in line.metas] for line in (small, medium)]

    assert "Retail 2.50 EUR" in meta_texts[0]
    assert "Retail 4.50 EUR" in meta_texts[1]
    assert response.context["pricing"].retail.enabled is True


@pytest.mark.django_db
def test_an_empty_own_price_is_the_products(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Hoodie", internal_number=615)
    variant_factory(product=product, label="M", first_label="S")

    page = client.get(_edit_url(product))
    data = _page_post_data(page) | {
        "product_retail_eur": "2.50",
        "product_business_eur": "3.40",
        "variants-1-retail": "on",
        # M: its own retail price; business left empty, so the product's.
        "variants-1-own_price": "on",
        "variants-1-retail_eur": "4.50",
        "variants-1-business_eur": "",
    }

    response = client.post(_edit_url(product), data)

    assert response.status_code == 302
    medium = product.variants.get(label="M")
    assert _price(medium, RETAIL) == Decimal("4.50")
    assert _price(medium, BUSINESS) == Decimal("3.40")

    # It opens with only what is its own filled in.
    page = client.get(_edit_url(product))
    _small_row, medium_row = page.context["variant_formset"]
    assert medium_row["own_price"].value() is True
    assert medium_row["retail_eur"].value() == Decimal("4.50")
    assert medium_row["business_eur"].value() is None


def _priced_apple():
    product = product_factory(name="Apple", internal_number=616)
    update_product_standard_pricing(
        product=product,
        business_eur=Decimal("1.90"),
        business_sek=None,
        business_enabled=True,
        retail_eur=Decimal("2.50"),
        retail_sek=None,
        retail_enabled=True,
    )

    return product


@pytest.mark.django_db
def test_changing_a_price_asks_for_the_password_first(client):
    client.force_login(full_staff_user_factory())
    product = _priced_apple()
    page = client.get(_edit_url(product))
    data = _page_post_data(page) | {"product_retail_eur": "2.60"}

    # Asked, not saved.
    response = client.post(_edit_url(product), data)

    assert response.status_code == 200
    (change,) = response.context["price_check"].changes
    assert (change.old, change.new, change.percent_label) == (
        Decimal("2.50"),
        Decimal("2.60"),
        "+4 %",
    )
    assert "data-password-again" in response.content.decode()
    assert _price(product.variants.get(), RETAIL) == Decimal("2.50")

    # A wrong password: asked again.
    response = client.post(
        _edit_url(product),
        data | {"password_again": "wrong"},
    )

    assert response.status_code == 200
    assert "not your password" in str(
        response.context["price_check"].form.errors
    )
    assert _price(product.variants.get(), RETAIL) == Decimal("2.50")

    # The right one: saved.
    response = client.post(
        _edit_url(product),
        data | {"password_again": "password"},
    )

    assert response.status_code == 302
    assert _price(product.variants.get(), RETAIL) == Decimal("2.60")


@pytest.mark.django_db
def test_without_the_check_a_price_changes_at_once(client, settings):
    settings.PRICE_CHANGE_CHECK = False
    client.force_login(full_staff_user_factory())
    product = _priced_apple()
    page = client.get(_edit_url(product))

    response = client.post(
        _edit_url(product),
        _page_post_data(page) | {"product_retail_eur": "3.00"},
    )

    assert response.status_code == 302
    assert _price(product.variants.get(), RETAIL) == Decimal("3.00")

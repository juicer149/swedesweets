"""The catalog page of an ops product: category, picture and the text per
language, apart from the product form."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from products.models import Product, ProductProfile, ProductTranslation
from products.tests.factories import product_factory


def _catalog_url(product):
    return reverse("ops_products:edit_catalog", kwargs={"product_pk": product.pk})


def _post_data(**overrides):
    data = {
        "category": ProductProfile.Category.CANDY,
        "fr-name": "Poivre turc",
        "fr-description": "Salé.",
        "fr-ingredients": "Sucre.",
        "en-name": "",
        "en-description": "",
        "en-ingredients": "",
    }
    data.update(overrides)

    return data


@pytest.mark.django_db
def test_the_catalog_page_has_a_tab_per_language(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=701)

    response = client.get(_catalog_url(product))
    content = response.content.decode()

    assert response.status_code == 200
    assert [language.code for language in response.context["languages"]] == [
        "fr",
        "en",
    ]
    assert 'data-tab="fr"' in content
    assert 'data-tab="en"' in content
    assert 'name="fr-description"' in content
    assert 'name="en-description"' in content
    assert 'name="category"' in content
    assert 'enctype="multipart/form-data"' in content


@pytest.mark.django_db
def test_saving_the_catalog_page(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=702)

    response = client.post(
        _catalog_url(product),
        _post_data(**{"en-description": "Salty."}),
    )

    detail_url = reverse("ops_products:detail", kwargs={"product_pk": product.pk})
    assert response.status_code == 302
    assert response.url == f"{detail_url}#catalog"

    product.profile.refresh_from_db()
    assert product.profile.category == ProductProfile.Category.CANDY
    texts = {
        translation.language_code: (
            translation.name,
            translation.description,
            translation.ingredients,
        )
        for translation in ProductTranslation.objects.filter(product=product)
    }
    assert texts == {
        "fr": ("Poivre turc", "Salé.", "Sucre."),
        "en": ("", "Salty.", ""),
    }


@pytest.mark.django_db
def test_an_error_in_a_language_keeps_the_page(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=703)

    response = client.post(
        _catalog_url(product),
        _post_data(**{"en-name": "x" * 500}),
    )

    assert response.status_code == 200
    english = response.context["languages"][1]
    assert english.has_errors
    assert not ProductTranslation.objects.filter(product=product).exists()


@pytest.mark.django_db
def test_a_new_product_goes_on_to_its_catalog_page(client):
    client.force_login(full_staff_user_factory())

    response = client.post(
        reverse("ops_products:create"),
        {
            "internal_number": "704",
            "manufacturer": "Fazer",
            "brand": "Fazer",
            "name": "Tyrkisk Peber",
            "stock_unit": Product.StockUnit.BOX,
            "weight_per_unit": "3000",
            "business_eur": "",
            "business_sek": "",
            "business_active": "on",
            "retail_eur": "",
            "retail_sek": "",
        },
    )

    assert response.status_code == 302
    product = Product.objects.get(internal_number=704)
    assert response.url == _catalog_url(product)

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from products.tests.factories import product_factory


@pytest.mark.django_db
def test_product_detail_shows_variants_with_stock_pricing_and_edit(client):
    client.force_login(full_staff_user_factory())

    product = product_factory(
        name="Apple",
        internal_number=501,
    )
    batch_factory(
        product=product,
        today=TODAY,
        batch_id="B-501",
        quantity=12,
    )

    response = client.get(
        reverse("ops_products:detail", kwargs={"product_pk": product.pk}),
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["status_key"] == "active"
    # Two tabs: the Product tab's variants show the stock.
    assert [tab.key for tab in response.context["page_tabs"]] == [
        "product",
        "catalog",
    ]
    (line,) = response.context["variant_lines"]
    assert line.aside == product.stock_quantity_label(12)
    # The heading says no stock (the variants do).
    assert "available" not in content.split("</header>")[0]
    # Business and Retail as tags in Pricing.
    assert 'class="product-tag pricing-tag pricing-tag--' in content
    assert "demand" not in response.context

    edit_url = reverse("ops_products:edit", kwargs={"product_pk": product.pk})
    catalog_url = reverse(
        "ops_products:edit_catalog",
        kwargs={"product_pk": product.pk},
    )
    assert f'href="{edit_url}#product"' in content
    assert f'href="{catalog_url}"' in content

    add_batch_url = f"{reverse('ops_inventory:create')}?product={product.pk}"
    assert f'href="{add_batch_url}"' in content
    assert f'href="{reverse("ops_products:index")}"' in content


@pytest.mark.django_db
def test_add_batch_link_preselects_the_product(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=502)

    response = client.get(
        reverse("ops_inventory:create"),
        {"product": product.pk},
    )

    assert response.status_code == 200
    assert response.context["form"].initial["product"] == product.pk


@pytest.mark.django_db
def test_product_edit_form_is_one_page_of_sections(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=503)

    response = client.get(
        reverse("ops_products:edit", kwargs={"product_pk": product.pk}),
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert "page_tabs" not in response.context
    assert [section.key for section in response.context["form_sections"]] == [
        "product",
        "pricing",
        "variants",
    ]
    # The product page's buttons link to the sections by id.
    assert 'id="product"' in content
    # The catalog has its own page.
    assert 'name="fr-description"' not in content
    assert 'name="category"' not in content
    # The status switch and the catalog ID come first.
    assert content.index('name="active"') < content.index('name="internal_number"')
    assert content.index('name="internal_number"') < content.index('name="brand"')
    assert content.index('name="name"') < content.index('name="vegan"')
    # Each pricing channel: its switch, then one price field with EUR / SEK
    # chips (buttons, not sent with the form) beside the two prices.
    assert 'type="checkbox" name="business_active"' in content
    assert content.index('name="business_active"') < content.index(
        'name="business_eur"'
    )
    assert content.count("data-price-field") == 2
    assert 'name="business_sek"' in content
    assert 'type="button" aria-pressed="true" data-price-currency="eur"' in content
    # The sections are rows that open one at a time, the first open.
    assert content.count("data-form-section") == 3
    assert 'data-smooth-group="form-sections" open' in content
    # "Edit" over the name.
    assert '<span class="page__kicker">Edit</span>' in content
    assert "data-tabs" not in content
    assert "data-dirty-form" in content
    assert 'name="business_eur"' in content
    # Catalog ID is typed, not stepped; status is one switch.
    assert "Catalog ID" in content
    assert 'type="number" name="internal_number"' not in content
    assert 'type="checkbox" name="active"' in content


@pytest.mark.django_db
def test_product_create_form_renders(client):
    client.force_login(full_staff_user_factory())

    response = client.get(reverse("ops_products:create"))

    assert response.status_code == 200
    assert 'name="weight_per_unit"' in response.content.decode()


@pytest.mark.django_db
def test_product_list_shows_table_and_phone_rows(client):
    client.force_login(full_staff_user_factory())
    product = product_factory(name="Apple", internal_number=504)

    response = client.get(reverse("ops_products:index"))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'class="data-table product-table"' in content
    assert "mobile-lines" in content

    row = next(
        row for row in response.context["product_rows"] if row.product == product
    )
    assert row.meta.startswith(product.code_label)

    detail_url = reverse("ops_products:detail", kwargs={"product_pk": product.pk})
    # Table row (data-href) and phone row (href) both open the product.
    assert content.count(f'"{detail_url}"') >= 2


@pytest.mark.django_db
def test_product_list_table_has_picture_circle_and_no_unit(client):
    client.force_login(full_staff_user_factory())
    product_factory(name="Apple", internal_number=504)

    response = client.get(reverse("ops_products:index"))
    content = response.content.decode()

    assert response.status_code == 200
    (row,) = response.context["product_rows"]
    assert row.image_url is None
    assert 'class="table-product"' in content
    assert "line__image--empty" in content
    assert "Unit" not in [sort.label for sort in response.context["table_sorts"]]


@pytest.mark.django_db
def test_catalog_tab_previews_the_shop_page_in_each_language(client):
    from products.services import CatalogTextChange, update_product_catalog

    client.force_login(full_staff_user_factory())
    product = product_factory(brand="Fazer", name="Tyrkisk Peber")
    update_product_catalog(
        product=product,
        category="candy",
        texts={
            "fr": CatalogTextChange(
                name="Poivre turc",
                description="Salé.",
                ingredients="Sucre.",
            ),
        },
    )

    response = client.get(
        reverse("ops_products:detail", kwargs={"product_pk": product.pk}),
    )
    content = response.content.decode()

    french, english = response.context["catalog_previews"]
    assert (french.language_code, french.product_name) == ("fr", "Poivre turc")
    # English has no text of its own: the shop's fallbacks.
    assert english.product_name == product.display_name
    assert english.description == "Salé."
    assert [tab.key for tab in english.page_tabs] == [
        "description",
        "ingredients",
    ]
    # In each language's own words (the category, the shop's labels).
    assert (french.category_label, english.category_label) == (
        "Bonbons",
        "Candy",
    )
    assert "Ajouter au panier" in content
    assert "Ingrédients" in content
    assert 'id="preview-fr-product-title"' in content
    assert 'id="preview-en-product-title"' in content
    # Not sold (no retail price): shown without a price, and said so.
    assert response.context["in_shop"] is False
    assert french.offers == ()
    assert "Not in the shop now" in content
    assert "data-product-add-form" in content and " inert" in content

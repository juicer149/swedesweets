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
    (card,) = response.context["variant_cards"]
    assert card.stock_label == product.stock_quantity_label(12)
    assert card.in_stock is True
    # The heading says no stock (the variants do).
    assert "available" not in content.split("</header>")[0]
    # The product's card, then Variants and offers with the product price
    # and a card per variant (its channels as chips), with its help.
    # The product is the page's hero, over the tabs (Product, Catalog).
    assert 'class="product-card product-hero"' in content
    assert content.index("product-hero") < content.index('role="tablist"')
    assert 'id="product-variants-title">Variants and offers</h2>' in content
    assert "variant-view__chip" in content
    assert 'data-help-open="variants-help"' in content
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
    # Open sections: the product's data, then its variants with prices.
    assert [section.key for section in response.context["form_sections"]] == [
        "product",
        "variants",
    ]
    assert "<details" not in content
    # The product page's buttons link to the sections by id.
    assert 'id="product"' in content
    assert 'id="variants"' in content
    # The catalog has its own page.
    assert 'name="fr-description"' not in content
    assert 'name="category"' not in content
    # The product as a card: catalog ID and the status switch at its top,
    # then brand and name; the section has its help.
    assert 'class="product-card product-card--form"' in content
    assert content.index('name="internal_number"') < content.index('name="active"')
    assert content.index('name="active"') < content.index('name="brand"')
    assert 'data-help-open="product-help"' in content
    assert content.index('name="name"') < content.index('name="vegan"')
    # Each variant's sales channels and price tag; its own prices (shown
    # with the tag on) and the product's price.
    assert 'type="checkbox" name="variants-0-business"' in content
    assert 'type="checkbox" name="variants-0-own_price"' in content
    assert 'name="variants-0-business_eur"' in content
    assert 'name="product_business_sek"' in content
    assert "Swedish/internal MVP" not in content
    # No hero: the Product card says which product (a hidden title).
    assert '<h1 id="page-title" class="visually-hidden">Edit ' in content
    assert "page__kicker" not in content
    # No picture yet: no circle by the name.
    assert "page__heading-picture" not in content
    # Back while nothing is changed; Cancel once something is (CSS).
    assert "back-or-cancel__back" in content
    assert "back-or-cancel__cancel" in content
    assert "data-tabs" not in content
    assert "data-dirty-form" in content
    # Catalog ID is typed, not stepped; status is one switch.
    assert "Catalog ID" in content
    assert 'type="number" name="internal_number"' not in content
    assert 'type="checkbox" name="active"' in content


@pytest.mark.django_db
def test_product_create_form_has_product_and_pricing(client):
    client.force_login(full_staff_user_factory())

    response = client.get(reverse("ops_products:create"))
    content = response.content.decode()

    assert [section.key for section in response.context["form_sections"]] == [
        "product",
        "pricing",
    ]
    # Its price with the EUR / SEK chips.
    assert content.count("data-price-field") == 2


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

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.tests.factories import full_staff_user_factory
from inventory.tests.conftest import TODAY
from inventory.tests.factories import batch_factory
from products.tests.factories import product_factory


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    """These view tests use force_login rather than password authentication."""
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]


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
    # The product and what is sold, its shop text, then its stock.
    assert [tab.key for tab in response.context["page_tabs"]] == [
        "product",
        "text",
        "inventory",
    ]
    (card,) = response.context["variant_cards"]
    assert [batch.quantity for batch in card.batches] == [12]
    # No hero: the product's card first in the Product tab, without stock.
    assert "product-hero" not in content
    assert 'class="product-card product-view"' in content
    assert content.index('role="tablist"') < content.index("product-view")
    assert content.index("product-view") < content.index("variant-view__card")
    assert "total_stock" not in response.context
    # A card per variant (its channels as chips with a tick or a cross,
    # Business over Retail, each with its price beside it when sold in it),
    # with the section's help.
    assert "variant-view__chip" in content
    assert "variant-view__chip-icon" in content
    assert [channel.label for channel in card.channels] == [
        "Business",
        "Retail",
    ]
    assert all(
        bool(channel.amounts) == channel.sold for channel in card.channels
    )
    assert 'data-help-open="variants-help"' in content
    assert "demand" not in response.context
    # Its batch on its card on the Inventory tab, to the batch's page.
    (batch_link,) = card.batches
    assert batch_link.batch_id == "B-501"
    assert batch_link.expired is False
    batch = product.batches.get()
    batch_url = reverse("ops_inventory:detail", kwargs={"batch_pk": batch.pk})
    assert (
        content.index('id="panel-product"')
        < content.index("variant-view__chip")
        < content.index('id="panel-inventory"')
        < content.index(f'href="{batch_url}"')
    )

    edit_url = reverse("ops_products:edit", kwargs={"product_pk": product.pk})
    catalog_url = reverse(
        "ops_products:edit_catalog",
        kwargs={"product_pk": product.pk},
    )
    assert f'href="{edit_url}#product"' in content
    assert f'href="{catalog_url}"' in content
    # At the page's foot, the open tab's action: Edit on Product and on
    # Shop text (their forms), Add batch on Inventory.
    add_batch_url = f"{reverse('ops_inventory:create')}?product={product.pk}"
    assert [
        (action.tab, action.label, action.href)
        for action in response.context["tab_actions"]
    ] == [
        ("product", "Edit", f"{edit_url}#product"),
        ("text", "Edit", catalog_url),
        ("inventory", "Add batch", add_batch_url),
    ]
    # No Edit product or Add batch at the tabs' feet.
    assert "Edit product</a>" not in content
    assert "product-actions" not in content
    # Back at the foot's left: to the page before (back_link.js), else the
    # product list; the old Back under the page goes.
    products_url = reverse("ops_products:index")
    assert (
        f'class="quiet-link tabs-foot__back" href="{products_url}"' in content
    )
    assert "data-back-link" in content
    assert "page__back" not in content
    # (Static files carry a hash in their names: js/back_link.<hash>.js.)
    assert "js/back_link." in content
    assert content.index('id="panel-inventory"') < content.index("tabs-foot")
    assert "tabs-foot__action" in content
    # No pencil on the product's card (Edit is at the foot).
    assert "product-card__edit" not in content
    assert f'href="{catalog_url}" data-tab-action="text" hidden' in content
    # The actions come after the tabs' panels (at the foot).
    assert content.index('id="panel-product"') < content.index(
        'data-tab-action="product"'
    )

    assert f'href="{add_batch_url}"' in content
    assert f'href="{reverse("ops_products:index")}"' in content


@pytest.mark.django_db
def test_variant_card_lists_its_batches_on_the_shelf(client):
    from datetime import timedelta

    from inventory.expiry import EXPIRY_SOON_DAYS
    from inventory.models import InventoryBatch

    client.force_login(full_staff_user_factory())
    product = product_factory(name="Pear", internal_number=503)
    later = batch_factory(
        product=product,
        today=TODAY,
        batch_id="B-LATER",
        quantity=4,
        best_before=TODAY + timedelta(days=EXPIRY_SOON_DAYS + 30),
    )
    soon = batch_factory(
        product=product,
        today=TODAY,
        batch_id="B-SOON",
        quantity=5,
        best_before=TODAY + timedelta(days=EXPIRY_SOON_DAYS - 1),
    )
    expired = batch_factory(
        product=product,
        today=TODAY,
        batch_id="B-OLD",
        quantity=3,
    )
    empty = batch_factory(
        product=product,
        today=TODAY,
        batch_id="B-EMPTY",
        quantity=2,
    )
    # Past its best-before and not closed; and one with none left.
    InventoryBatch.objects.filter(pk=expired.pk).update(
        best_before=TODAY - timedelta(days=1),
    )
    InventoryBatch.objects.filter(pk=empty.pk).update(quantity=0)

    response = client.get(
        reverse("ops_products:detail", kwargs={"product_pk": product.pk}),
    )
    content = response.content.decode()

    (card,) = response.context["variant_cards"]
    # The soonest best-before first; none with less than one unit.
    assert [batch.batch_id for batch in card.batches] == [
        "B-OLD",
        "B-SOON",
        "B-LATER",
    ]
    # Expired in red, soon (inventory/expiry.py) in orange, else plain.
    assert [batch.tone for batch in card.batches] == [
        "expired",
        "soon",
        "safe",
    ]
    # Plain numbers (no unit): in stock, and how many orders hold (none);
    # the heads over the first card say which is which.
    assert [(batch.quantity, batch.reserved) for batch in card.batches] == [
        (3, 0),
        (5, 0),
        (4, 0),
    ]
    assert "variant-views__head" in content
    assert ">Reserved<" in content
    # Each batch's best-before after its ID; heads over every column.
    for head in ("Label", "Weight", "Batch", "Best before", "In stock"):
        assert f">{head}<" in content
    expired_on = (TODAY - timedelta(days=1)).isoformat()
    assert f'<time datetime="{expired_on}">' in content
    assert "B-EMPTY" not in content
    assert "variant-batch--expired" in content
    assert "variant-batch--soon" in content
    for batch in (later, soon, expired):
        batch_url = reverse(
            "ops_inventory:detail",
            kwargs={"batch_pk": batch.pk},
        )
        assert f'href="{batch_url}"' in content


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
    # The shop text has its own page; the category is the product's.
    assert 'name="fr-description"' not in content
    assert 'name="category"' in content
    # The product as a card: catalog ID and the status switch at its top,
    # then brand and name; the section has its help.
    assert 'class="product-card product-card--form"' in content
    assert content.index('name="internal_number"') < content.index('name="active"')
    assert content.index('name="active"') < content.index('name="brand"')
    assert 'data-help-open="product-help"' in content
    assert content.index('name="name"') < content.index('name="vegan"')
    # Each variant's sales channels and its prices on its card.
    assert 'type="checkbox" name="variants-0-business"' in content
    assert 'name="variants-0-business_eur"' in content
    assert 'name="variants-0-business_sek"' in content
    assert "own_price" not in content
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
def test_shop_text_tab_shows_each_languages_own_text(client):
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
            ),
        },
    )

    response = client.get(
        reverse("ops_products:detail", kwargs={"product_pk": product.pk}),
    )
    content = response.content.decode()

    french, english = response.context["language_texts"]
    assert (french.code, english.code) == ("fr", "en")
    # French: its own text; an empty field says what the shop shows.
    assert french.has_own_text is True
    name, description, ingredients = french.fields
    assert (name.value, description.value) == ("Poivre turc", "Salé.")
    assert ingredients.value == ""
    assert ingredients.fallback == "The shop shows none."
    assert "Poivre turc" in content
    # English has none: said so, with what the shop shows and a way to
    # add it (the shop text page, open on English).
    assert english.has_own_text is False
    assert "No English text yet" in content
    assert "French text" in english.fallback_note
    catalog_url = reverse(
        "ops_products:edit_catalog",
        kwargs={"product_pk": product.pk},
    )
    assert english.edit_href == f"{catalog_url}#en"
    assert f'href="{catalog_url}#en"' in content
    assert "Add English text" in content
    # No preview of the shop's page (its price and buttons are the
    # Product tab's).
    assert "data-product-add-form" not in content
    assert "catalog_previews" not in response.context
    # The card says nothing of the shop or stock (the Inventory tab);
    # its category is among its facts.
    assert "product-view__shop" not in content
    category_label = response.context["profile"].category_label
    assert category_label
    assert f"Category <b>{category_label}</b>" in content


def _business_priced_product(internal_number):
    from decimal import Decimal

    from pricing.product_configuration import update_product_standard_pricing

    product = product_factory(name="Pear", internal_number=internal_number)
    update_product_standard_pricing(
        product=product,
        business_eur=Decimal("1.90"),
        business_sek=None,
        business_enabled=True,
        retail_eur=None,
        retail_sek=None,
        retail_enabled=False,
    )

    return product


@pytest.mark.django_db
def test_inventory_tab_warns_of_nothing_to_sell_and_expired_batches(client):
    from datetime import timedelta

    from inventory.models import InventoryBatch

    client.force_login(full_staff_user_factory())
    product = _business_priced_product(520)
    url = reverse("ops_products:detail", kwargs={"product_pk": product.pk})

    # Active, sold to business customers, no stock: out of stock, said
    # first on the Inventory tab.
    response = client.get(url)
    content = response.content.decode()

    assert response.context["inventory_notes"] == (
        "Out of stock: it is for sale, but there is nothing to sell.",
    )
    assert (
        content.index('id="panel-inventory"')
        < content.index("inventory-notes__note")
    )

    # Only a batch past its best-before: still nothing to sell.
    batch = batch_factory(product=product, today=TODAY, batch_id="P-OLD")
    InventoryBatch.objects.filter(pk=batch.pk).update(
        best_before=TODAY - timedelta(days=2),
    )

    response = client.get(url)

    assert response.context["inventory_notes"] == (
        "Out of stock: it is for sale, but there is nothing to sell.",
        "1 batch past best-before (in red): sell it off or close it.",
    )

    # A good batch: something to sell.
    batch_factory(product=product, today=TODAY, batch_id="P-NEW")
    response = client.get(url)

    # The expired one still warned about; no more out of stock.
    assert response.context["inventory_notes"] == (
        "1 batch past best-before (in red): sell it off or close it.",
    )


@pytest.mark.django_db
def test_an_inactive_product_is_not_out_of_stock(client):
    from products.services import update_product_active

    client.force_login(full_staff_user_factory())
    product = _business_priced_product(521)
    update_product_active(product=product, active=False)

    response = client.get(
        reverse("ops_products:detail", kwargs={"product_pk": product.pk}),
    )

    # Not for sale: nothing to warn about.
    assert response.context["inventory_notes"] == ()


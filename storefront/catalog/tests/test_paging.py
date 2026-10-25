from decimal import Decimal

import pytest
from django.urls import reverse

from products.tests.factories import product_factory
from retail.tests.factories import (
    retail_inventory_batch_factory,
    retail_product_price_factory,
)


@pytest.fixture
def catalog(db):
    products = []
    for index in range(15):
        product = product_factory(name=f"Paging {index:02}")
        retail_product_price_factory(
            product=product,
            enabled=True,
            price=Decimal("2.50"),
        )
        retail_inventory_batch_factory(product=product, batch_id=f"PAGING-{index}")
        products.append(product)
    return products


def test_first_page_keeps_full_search_index_but_only_twelve_cards(client, catalog):
    response = client.get(reverse("storefront:product_list"))
    html = response.content.decode()
    assert len(response.context["catalog_index"]) == 15
    assert html.count("data-catalog-product\n") == 12
    assert len(response.context["initial_product_cards"]) == 12
    assert response.context["catalog_next_page"] == 2
    second = client.get(reverse("storefront:product_list"), {"page": 2})
    assert second.content.decode().count("data-catalog-product\n") == 3


def test_batch_renders_requested_orderable_cards_with_private_cache(client, catalog):
    ids = [catalog[-1].pk, catalog[0].pk]
    response = client.get(
        reverse("storefront:product_list"),
        {
            "catalog_cards": "1",
            "ids": ",".join(map(str, ids)),
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["ids"] == ids
    assert payload["html"].count("data-catalog-product\n") == 2
    assert "csrfmiddlewaretoken" in payload["html"]
    assert "no-store" in response.headers["Cache-Control"]
    assert "private" in response.headers["Cache-Control"]
    # Disabling an offer after the index arrived cannot expose a stale card.
    catalog[-1].commercial_prices.update(enabled=False)
    refreshed = client.get(
        reverse("storefront:product_list"),
        {
            "catalog_cards": "1",
            "ids": str(ids[0]),
        },
    )
    assert refreshed.json()["ids"] == []


@pytest.mark.django_db
@pytest.mark.parametrize("ids", ["", "a", "0", "1,1", ",".join(map(str, range(1, 14)))])
def test_batch_rejects_invalid_or_unbounded_requests(client, ids):
    response = client.get(
        reverse("storefront:product_list"),
        {"catalog_cards": "1", "ids": ids},
    )
    assert response.status_code == 400

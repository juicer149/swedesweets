"""products/0009-0011 move the description and ingredients (written in
French so far) from the profile to the French translation."""

from __future__ import annotations

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = [("products", "0008_productvariant")]
AFTER = [("products", "0011_remove_productprofile_description_and_more")]

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def historical_apps():
    executor = MigrationExecutor(connection)
    latest_targets = executor.loader.graph.leaf_nodes()

    executor.migrate(BEFORE)
    apps = executor.loader.project_state(BEFORE).apps

    try:
        yield apps
    finally:
        MigrationExecutor(connection).migrate(latest_targets)


def _migrate(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)

    return executor.loader.project_state(targets).apps


def _product(apps, *, sku, description="", ingredients=""):
    Product = apps.get_model("products", "Product")
    ProductProfile = apps.get_model("products", "ProductProfile")

    product = Product.objects.create(
        sku=sku,
        brand="Brand",
        name=sku,
        weight_per_unit=1000,
    )
    ProductProfile.objects.create(
        product=product,
        description=description,
        ingredients=ingredients,
    )

    return product


def test_the_text_moves_to_french(historical_apps):
    ProductTranslation = historical_apps.get_model(
        "products", "ProductTranslation"
    )

    named = _product(
        historical_apps,
        sku="SS-001",
        description="Salé.",
        ingredients="Sucre.",
    )
    ProductTranslation.objects.create(
        product=named,
        language_code="fr",
        name="Poivre turc",
    )
    unnamed = _product(historical_apps, sku="SS-002", description="Doux.")
    _product(historical_apps, sku="SS-003")

    apps = _migrate(AFTER)
    ProductTranslation = apps.get_model("products", "ProductTranslation")

    texts = {
        translation.product_id: (
            translation.language_code,
            translation.name,
            translation.description,
            translation.ingredients,
        )
        for translation in ProductTranslation.objects.all()
    }

    assert texts == {
        named.pk: ("fr", "Poivre turc", "Salé.", "Sucre."),
        unnamed.pk: ("fr", "", "Doux.", ""),
    }


def test_backwards_the_french_text_goes_back(historical_apps):
    product = _product(historical_apps, sku="SS-001", description="Salé.")
    _migrate(AFTER)

    apps = _migrate(BEFORE)
    ProductProfile = apps.get_model("products", "ProductProfile")
    ProductTranslation = apps.get_model("products", "ProductTranslation")

    assert ProductProfile.objects.get(product_id=product.pk).description == (
        "Salé."
    )
    # A translation without a name could not exist before.
    assert not ProductTranslation.objects.exists()

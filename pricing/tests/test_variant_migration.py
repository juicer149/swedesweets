"""pricing/0003-0004 point every offer at its variant: a batch offer at its
batch's, any other at its product's only variant."""

from __future__ import annotations

from datetime import date

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = [("pricing", "0002_create_business_standard_offers")]
AFTER = [("pricing", "0004_alter_commercialprice_variant_and_more")]

# What the test writes with: pricing before, products and inventory with
# their variants.
DATA_STATE = [
    *BEFORE,
    ("products", "0008_productvariant"),
    ("inventory", "0004_alter_inventorybatch_variant"),
]

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def historical_apps():
    executor = MigrationExecutor(connection)
    latest_targets = executor.loader.graph.leaf_nodes()

    executor.migrate(BEFORE)
    apps = executor.loader.project_state(DATA_STATE).apps

    try:
        yield apps
    finally:
        MigrationExecutor(connection).migrate(latest_targets)


def _migrate(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)

    return executor.loader.project_state(targets).apps


def _product(apps, *, sku):
    Product = apps.get_model("products", "Product")
    ProductVariant = apps.get_model("products", "ProductVariant")

    product = Product.objects.create(
        sku=sku,
        brand="Brand",
        name=sku,
        weight_per_unit=1000,
    )
    variant = ProductVariant.objects.create(
        product=product,
        label="",
        position=1,
        sku=sku,
        weight_per_unit=1000,
    )

    return product, variant


def test_every_offer_gets_its_variant(historical_apps):
    InventoryBatch = historical_apps.get_model("inventory", "InventoryBatch")
    CommercialPrice = historical_apps.get_model("pricing", "CommercialPrice")

    apple, apple_variant = _product(historical_apps, sku="SS-001")
    pear, pear_variant = _product(historical_apps, sku="SS-002")

    batch = InventoryBatch.objects.create(
        batch_id="A-1",
        product=apple,
        variant=apple_variant,
        quantity=5,
        best_before=date(2030, 1, 1),
        location="Shelf A1",
    )

    standard = CommercialPrice.objects.create(
        product=apple,
        channel="business",
        enabled=True,
    )
    retail = CommercialPrice.objects.create(
        product=pear,
        channel="retail",
    )
    batch_offer = CommercialPrice.objects.create(
        product=apple,
        batch=batch,
        channel="retail",
    )

    apps = _migrate(AFTER)
    CommercialPrice = apps.get_model("pricing", "CommercialPrice")

    assert dict(CommercialPrice.objects.values_list("pk", "variant_id")) == {
        standard.pk: apple_variant.pk,
        retail.pk: pear_variant.pk,
        batch_offer.pk: apple_variant.pk,
    }

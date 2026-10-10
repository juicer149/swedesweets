"""inventory/0003-0004 point every batch at its product's only variant."""

from __future__ import annotations

from datetime import date

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = [
    (
        "inventory",
        "0002_inventorybatch_closed_at_inventorybatch_closed_by_and_more",
    ),
]
AFTER = [("inventory", "0004_alter_inventorybatch_variant")]

# What the test writes with: the inventory before, the products after
# products/0008 (variants exist).
DATA_STATE = [
    *BEFORE,
    ("products", "0008_productvariant"),
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


def _batch(apps, *, product, batch_id):
    InventoryBatch = apps.get_model("inventory", "InventoryBatch")

    return InventoryBatch.objects.create(
        batch_id=batch_id,
        product=product,
        quantity=5,
        best_before=date(2030, 1, 1),
        location="Shelf A1",
    )


def test_every_batch_gets_its_product_variant(historical_apps):
    apple, apple_variant = _product(historical_apps, sku="SS-001")
    pear, pear_variant = _product(historical_apps, sku="SS-002")

    first = _batch(historical_apps, product=apple, batch_id="A-1")
    second = _batch(historical_apps, product=apple, batch_id="A-2")
    third = _batch(historical_apps, product=pear, batch_id="P-1")

    apps = _migrate(AFTER)
    InventoryBatch = apps.get_model("inventory", "InventoryBatch")

    variant_by_batch = dict(
        InventoryBatch.objects.values_list("pk", "variant_id")
    )

    assert variant_by_batch == {
        first.pk: apple_variant.pk,
        second.pk: apple_variant.pk,
        third.pk: pear_variant.pk,
    }


def test_a_batch_whose_product_has_no_variant_stops_the_migration(
    historical_apps,
):
    Product = historical_apps.get_model("products", "Product")
    product = Product.objects.create(
        sku="SS-003",
        brand="Brand",
        name="No variant",
        weight_per_unit=1000,
    )
    batch = _batch(historical_apps, product=product, batch_id="N-1")

    with pytest.raises(RuntimeError, match="N-1"):
        _migrate(AFTER)

    # Let the fixture bring the database back to the latest state.
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM inventory_inventorybatch WHERE id = %s",
            [batch.pk],
        )

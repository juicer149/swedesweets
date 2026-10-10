"""products/0008 gives every existing product its only variant."""

from __future__ import annotations

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = [("products", "0007_productprofile_display")]
AFTER = [("products", "0008_productvariant")]

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


def test_every_product_gets_its_only_variant(historical_apps):
    Product = historical_apps.get_model("products", "Product")

    rows = [
        ("SS-001", 1, 2000, True),
        ("SS-002", 2, 275, True),
        ("OLW-GRILL_CHIPS-275", None, 275, False),
    ]

    for sku, internal_number, weight_per_unit, active in rows:
        Product.objects.create(
            sku=sku,
            internal_number=internal_number,
            brand="Brand",
            name=sku,
            weight_per_unit=weight_per_unit,
            active=active,
        )

    apps = _migrate(AFTER)
    Product = apps.get_model("products", "Product")
    ProductVariant = apps.get_model("products", "ProductVariant")

    assert ProductVariant.objects.count() == Product.objects.count() == 3

    for product in Product.objects.all():
        variant = ProductVariant.objects.get(product=product)

        assert variant.label == ""
        assert variant.position == 1
        assert variant.sku == product.sku
        assert variant.weight_per_unit == product.weight_per_unit
        # Active even when the product is not: the product's own switch
        # decides whether it is sold (a paused only variant would leave a
        # product with nothing to sell when it is switched back on).
        assert variant.active is True


def test_no_products_no_variants(historical_apps):
    apps = _migrate(AFTER)
    ProductVariant = apps.get_model("products", "ProductVariant")

    assert ProductVariant.objects.count() == 0

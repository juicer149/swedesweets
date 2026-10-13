"""Order lines keep a copy of what was bought (docs/roadmap.md): its name with
the size, SKU, label, weight and stock unit, taken when the line is first
saved, so an old order reads the same however the product changes later."""

from __future__ import annotations

import pytest

from business.services import create_order
from business.tests.factories import standard_business_offer_factory
from customers.tests.factories import customer_factory
from inventory.services import create_batch
from inventory.tests.conftest import STOCK_EARLY_BEST_BEFORE, TODAY
from orders.datatypes import OrderLineInput
from orders.models import Order
from orders.notifications import _mail_context
from orders.tests.factories import order_line_factory
from pricing.models import CommercialPrice
from products.models import Product, ProductVariant
from products.tests.factories import product_factory, variant_factory
from reservations.api import list_reserved_picks_for_order


def _medium_line():
    product = product_factory(brand="SwedeSweets", name="Hoodie")
    medium = variant_factory(product=product, label="M", weight_per_unit=450)
    offer = CommercialPrice.objects.create(
        variant=medium,
        channel=CommercialPrice.Channel.RETAIL,
    )
    order = Order.objects.create(channel=Order.Channel.RETAIL)

    return order_line_factory(
        order=order,
        product=product,
        commercial_offer=offer,
    )


@pytest.mark.django_db
def test_a_new_line_copies_what_is_bought():
    line = _medium_line()
    variant = line.variant

    assert line.name_snapshot == "SwedeSweets — Hoodie — M"
    assert line.sku_snapshot == variant.sku
    assert line.variant_label_snapshot == "M"
    assert line.weight_per_unit_snapshot == 450
    assert line.stock_unit_snapshot == line.product.stock_unit
    assert line.display_name == "SwedeSweets — Hoodie — M"
    assert line.unit_weight_label.startswith("450 g / ")


@pytest.mark.django_db
def test_a_line_reads_the_same_after_the_product_changes():
    line = _medium_line()
    # Renamed and relabelled behind the services' back.
    Product.objects.filter(pk=line.product_id).update(name="Sweater")
    ProductVariant.objects.filter(pk=line.variant_id).update(label="Medium")

    line = type(line).objects.get(pk=line.pk)
    line.quantity_in_units = 2
    line.save(update_fields=["quantity_in_units"])
    line.refresh_from_db()

    assert line.display_name == "SwedeSweets — Hoodie — M"
    assert line.variant_label_snapshot == "M"
    # The mails read the copy.
    (mailed,) = _mail_context(line.order)["lines"]
    assert mailed["name"] == "SwedeSweets — Hoodie — M"


@pytest.mark.django_db
def test_the_pick_list_names_what_was_ordered():
    product = product_factory(brand="Fazer", name="Apple", internal_number=1)
    standard_business_offer_factory(product=product)
    create_batch(
        batch_id="A-1",
        product=product,
        quantity=10,
        best_before=STOCK_EARLY_BEST_BEFORE,
        location="Shelf A1",
        today=TODAY,
    )
    order = create_order(
        customer=customer_factory(),
        lines=[OrderLineInput.units(product=product, quantity=2)],
    )
    Product.objects.filter(pk=product.pk).update(name="Pear")

    (pick,) = list_reserved_picks_for_order(order=order)

    assert "Fazer — Apple" in pick.product_name
    assert "Pear" not in pick.product_name
    assert pick.sku == product.variants.get().sku

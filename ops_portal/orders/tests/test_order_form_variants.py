"""The ops order form by variant (docs/product-variants.md, step 7): every
size its own row in the product search ("SwedeSweets — Hoodie — M"), with
its own weight and stock; a chosen line and Previous orders name the size."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.utils import timezone

from business.offer_choices import build_business_offer_choice_context
from customers.tests.factories import customer_factory
from inventory.tests.factories import batch_factory
from ops_portal.orders.forms import (
    AddOrderLineProductForm,
    OrderLineForm,
    OrderLineFormSet,
)
from ops_portal.orders.recent_orders import build_ops_recent_orders
from orders.models import Order
from orders.tests.factories import order_line_factory
from pricing.models import CommercialPrice, PriceAmount
from products.models import Product
from products.tests.factories import product_factory, variant_factory

TODAY = timezone.localdate()


def _offer(variant, price="20.00"):
    offer = CommercialPrice.objects.create(
        variant=variant,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=True,
    )
    PriceAmount.objects.create(
        commercial_price=offer,
        currency=PriceAmount.Currency.EUR,
        price=Decimal(price),
    )

    return offer


def _hoodie():
    product = product_factory(
        brand="SwedeSweets",
        name="Hoodie",
        weight_per_unit=400,
        internal_number=7,
    )
    medium = variant_factory(
        product=product,
        label="M",
        first_label="S",
        weight_per_unit=450,
    )
    small = product.variants.get(label="S")
    batch_factory(product=product, variant=small, today=TODAY, quantity=5)
    batch_factory(
        product=product,
        variant=medium,
        today=TODAY,
        quantity=3,
        batch_id="M-1",
    )

    return product, small, medium, _offer(small), _offer(medium)


def _options(form):
    field = form.fields["commercial_offer"]

    return [
        option
        for _group, options, _index in field.widget.optgroups(
            "offer",
            [],
        )
        for option in options
        if option["value"]
    ]


@pytest.mark.django_db
def test_every_size_is_its_own_row_with_its_weight_and_stock():
    _hoodie()
    context = build_business_offer_choice_context()

    form = AddOrderLineProductForm(
        offer_queryset=context.queryset,
        available_units_by_offer_id=context.available_units_by_offer_id,
    )
    options = _options(form)

    assert [
        (
            option["attrs"]["data-name"],
            option["attrs"]["data-weight"],
            option["attrs"]["data-stock"],
        )
        for option in options
    ] == [
        ("SwedeSweets — Hoodie — S", "400 g / Box", "5 left"),
        ("SwedeSweets — Hoodie — M", "450 g / Box", "3 left"),
    ]
    # A size can be searched for.
    assert " M " in f" {options[1]['attrs']['search']} "


@pytest.mark.django_db
def test_a_chosen_line_names_its_size():
    product, small, medium, small_offer, medium_offer = _hoodie()

    form = OrderLineForm(
        data={"commercial_offer": str(medium_offer.pk), "quantity": ""},
        offer_queryset=CommercialPrice.objects.filter(pk=medium_offer.pk),
    )
    form.is_valid()

    assert form.offer_view.name == "SwedeSweets — Hoodie — M"
    assert form.offer_view.meta == "#7 · 450 g / Box"


@pytest.mark.django_db
def test_too_many_of_a_size_names_the_size():
    product, small, medium, small_offer, medium_offer = _hoodie()

    formset = OrderLineFormSet(
        data={
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-0-commercial_offer": str(medium_offer.pk),
            "form-0-quantity": "4",
        },
    )

    assert not formset.is_valid()
    assert "SwedeSweets — Hoodie — M" in str(formset.non_form_errors())


@pytest.mark.django_db
def test_previous_orders_name_the_size_as_it_was_ordered():
    product, small, medium, small_offer, medium_offer = _hoodie()
    customer = customer_factory()
    order = Order.objects.create(customer=customer, status=Order.Status.PLACED)
    order_line_factory(
        order=order,
        product=product,
        quantity=2,
        commercial_offer=medium_offer,
    )
    Product.objects.filter(pk=product.pk).update(name="Sweater")

    (recent,) = build_ops_recent_orders(
        customer=customer,
        selectable_offer_ids={medium_offer.pk},
    )
    (line,) = recent.lines

    assert line.name == "SwedeSweets — Hoodie — M"
    assert line.commercial_price_id == medium_offer.pk

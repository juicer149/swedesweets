from __future__ import annotations

import importlib
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.apps import apps
from django.db.models import QuerySet
from django.utils import timezone

from inventory.tests.factories import batch_factory
from pricing.models import CommercialPrice, PriceAmount
from products.models import Product
from products.tests.factories import product_factory

TODAY = timezone.localdate()

migration = importlib.import_module(
    "pricing.migrations.0002_create_business_standard_offers"
)

SCHEMA_EDITOR = SimpleNamespace(connection=SimpleNamespace(alias="default"))


def _run():
    """Run the migration's function on the live models. It was written
    before offers had a variant (pricing/0003 fills that in), and its
    bulk_create skips save(), so the variant is filled in here as 0003
    would."""

    bulk_create = QuerySet.bulk_create

    def bulk_create_with_variants(queryset, objs, *args, **kwargs):
        objs = list(objs)

        if queryset.model is CommercialPrice:
            for offer in objs:
                offer.variant = Product.objects.get(
                    pk=offer.product_id,
                ).only_variant()

        return bulk_create(queryset, objs, *args, **kwargs)

    with patch.object(QuerySet, "bulk_create", bulk_create_with_variants):
        migration.create_business_standard_offers(apps, SCHEMA_EDITOR)


def _standard_offers(product):
    return CommercialPrice.objects.filter(
        product=product,
        channel=CommercialPrice.Channel.BUSINESS,
        batch__isnull=True,
    )


@pytest.mark.django_db
def test_creates_enabled_unpriced_standard_offer_for_each_product():
    first = product_factory(name="First", internal_number=1)
    second = product_factory(name="Second", internal_number=2)

    _run()

    for product in (first, second):
        (offer,) = _standard_offers(product)
        assert offer.enabled is True
        assert offer.reason == ""
        assert not offer.amounts.exists()


@pytest.mark.django_db
def test_includes_inactive_products():
    product = product_factory(name="Inactive", internal_number=1)
    product.active = False
    product.save(update_fields=["active"])

    _run()

    (offer,) = _standard_offers(product)
    assert offer.enabled is True


@pytest.mark.django_db
def test_leaves_existing_standard_offer_untouched():
    product = product_factory()
    existing = CommercialPrice.objects.create(
        product=product,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=False,
        reason=CommercialPrice.Reason.PROMOTION,
    )
    PriceAmount.objects.create(
        commercial_price=existing,
        currency=PriceAmount.Currency.EUR,
        price=Decimal("12.50"),
    )

    _run()

    (offer,) = _standard_offers(product)
    assert offer.pk == existing.pk
    assert offer.enabled is False
    assert offer.reason == CommercialPrice.Reason.PROMOTION
    assert offer.amounts.count() == 1


@pytest.mark.django_db
def test_batch_offer_does_not_count_as_standard_offer():
    product = product_factory()
    batch = batch_factory(product=product, today=TODAY)
    CommercialPrice.objects.create(
        product=product,
        batch=batch,
        channel=CommercialPrice.Channel.BUSINESS,
        enabled=True,
    )

    _run()

    assert _standard_offers(product).count() == 1


@pytest.mark.django_db
def test_retail_offer_does_not_count_and_no_retail_offer_is_created():
    product = product_factory()
    CommercialPrice.objects.create(
        product=product,
        channel=CommercialPrice.Channel.RETAIL,
        enabled=True,
    )

    _run()

    assert _standard_offers(product).count() == 1
    assert CommercialPrice.objects.filter(
        product=product,
        channel=CommercialPrice.Channel.RETAIL,
    ).count() == 1


@pytest.mark.django_db
def test_is_idempotent():
    product_factory()

    _run()
    _run()

    assert CommercialPrice.objects.count() == 1

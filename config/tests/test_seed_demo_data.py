from __future__ import annotations

from datetime import date

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from config.management.commands import _demo_data as demo
from customers.models import Customer
from inventory.models import InventoryBatch
from orders.models import Order
from pricing.models import CommercialPrice
from products.models import Product


@pytest.fixture
def debug(settings):
    settings.DEBUG = True


def _seed(**options):
    call_command("seed_demo_data", with_orders=True, **options)


@pytest.mark.django_db
def test_refuses_to_run_without_debug(settings):
    settings.DEBUG = False

    with pytest.raises(CommandError, match="DEBUG"):
        _seed()

    assert not Product.objects.exists()


@pytest.mark.django_db
def test_seeds_customers_stock_and_orders_in_every_state(debug):
    _seed()

    assert Customer.objects.count() == len(demo.CUSTOMERS)
    assert InventoryBatch.objects.exists()

    statuses = set(Order.objects.values_list("status", flat=True))
    assert statuses == {
        Order.Status.PLACED,
        Order.Status.PACKED,
        Order.Status.DELIVERED,
    }
    assert all(order.lines.exists() for order in Order.objects.all())


@pytest.mark.django_db
def test_order_timestamps_follow_their_status(debug):
    _seed()

    for order in Order.objects.all():
        assert order.placed_at is not None
        assert (order.packed_at is not None) == (
            order.status in (Order.Status.PACKED, Order.Status.DELIVERED)
        )
        assert (order.delivered_at is not None) == (
            order.status == Order.Status.DELIVERED
        )


@pytest.mark.django_db
def test_merch_has_enabled_retail_prices(debug):
    _seed()

    for item in demo.MERCH:
        product = Product.objects.get(internal_number=item.internal_number)
        offer = CommercialPrice.objects.get(
            product=product,
            channel=CommercialPrice.Channel.RETAIL,
        )
        assert offer.enabled
        assert offer.amounts.get().price == item.retail_price_eur


@pytest.mark.django_db
def test_refuses_existing_data_and_reset_recreates_it(debug):
    _seed()

    with pytest.raises(CommandError, match="--reset"):
        _seed()

    _seed(reset=True)

    assert Customer.objects.count() == len(demo.CUSTOMERS)


def test_customers_are_invented():
    for customer in demo.CUSTOMERS:
        assert customer.email.endswith("@example.com")
        # French numbers reserved for fiction: +33 1 99 00 xx xx
        assert customer.phone_number.startswith("+33199")


def test_orders_never_take_more_than_long_dated_stock():
    today = date(2026, 1, 15)
    batches = demo.build_batches(internal_numbers=list(range(1, 60)), today=today)
    orders = demo.build_orders(batches=batches, today=today)

    stock: dict[int, int] = {}
    for batch in batches:
        if (batch.best_before - today).days >= 60:
            number = batch.internal_number
            stock[number] = stock.get(number, 0) + batch.quantity

    for order in orders:
        for line in order.lines:
            stock[line.internal_number] -= line.quantity

    assert orders
    assert min(stock.values()) >= 1


@pytest.mark.django_db
def test_demo_accounts_log_in_with_their_username_as_password(debug, client):
    _seed(with_demo_accounts=True)

    for username in (
        "fullstaff",
        "restrictedstaff",
        "business",
        "business_incomplete",
    ):
        assert client.login(username=username, password=username), username
        client.logout()


@pytest.mark.django_db
def test_demo_accounts_have_the_right_roles(debug):
    from django.contrib.auth import get_user_model

    from accounts.roles import StaffAccessLevel

    _seed(with_demo_accounts=True)
    users = get_user_model().objects

    assert (
        users.get(username="fullstaff").staff_account.access_level
        == StaffAccessLevel.FULL
    )
    assert (
        users.get(username="restrictedstaff").staff_account.access_level
        == StaffAccessLevel.RESTRICTED
    )

    customer = users.get(username="business").customer_membership.customer
    assert Order.objects.filter(customer=customer).exists()
    assert customer.is_complete

    # A shop just invited: it has to fill in its details before ordering.
    new_shop = users.get(username="business_incomplete").customer_membership.customer
    assert not new_shop.is_complete
    assert not Order.objects.filter(customer=new_shop).exists()


@pytest.mark.django_db
def test_demo_accounts_survive_a_reset(debug):
    _seed(with_demo_accounts=True)
    _seed(with_demo_accounts=True, reset=True)

    from django.contrib.auth import get_user_model

    assert get_user_model().objects.filter(
        username__in=[
            "fullstaff",
            "restrictedstaff",
            "business",
            "business_incomplete",
        ]
    ).count() == 4


@pytest.mark.django_db
def test_business_catalogue_lists_candy_but_not_merch(debug):
    from business.selectors import list_business_catalog_products

    _seed()

    catalogue = list_business_catalog_products()
    numbers = {item.product.internal_number for item in catalogue}

    assert numbers
    assert not numbers & {item.internal_number for item in demo.MERCH}


@pytest.mark.django_db
def test_with_images_gives_every_product_a_picture_and_reset_removes_them(
    debug,
    settings,
    tmp_path,
    monkeypatch,
):
    from io import BytesIO

    from PIL import Image

    from config.management.commands import seed_demo_data
    from products.models import ProductProfile

    def tiny_picture(**_):
        output = BytesIO()
        Image.new("RGB", (8, 8), (236, 72, 90)).save(output, format="JPEG")
        return output.getvalue()

    # The plumbing is under test here, not the drawing (tested below).
    monkeypatch.setattr(seed_demo_data, "product_picture_jpeg", tiny_picture)
    settings.MEDIA_ROOT = tmp_path

    call_command("seed_demo_data", with_images=True)

    profiles = ProductProfile.objects.all()
    assert profiles.count() == Product.objects.count()
    assert all(profile.image and profile.thumbnail for profile in profiles)
    first_files = {path.name for path in tmp_path.rglob("*") if path.is_file()}
    assert first_files

    call_command("seed_demo_data", reset=True, with_images=True)

    # The previous run's pictures are gone, not left behind.
    files = {path.name for path in tmp_path.rglob("*") if path.is_file()}
    assert not files & first_files


def test_demo_pictures_follow_the_name():
    from config.management.commands._demo_images import product_picture_jpeg

    first = product_picture_jpeg(name="Hallon Lakrits Skalle", brand="BUBS")

    assert first[:2] == b"\xff\xd8"  # JPEG
    assert first == product_picture_jpeg(name="Hallon Lakrits Skalle", brand="BUBS")
    assert first != product_picture_jpeg(name="Cool Cola Skalle", brand="BUBS")

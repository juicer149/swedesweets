"""Seed a local database with synthetic demo data.

    python manage.py seed_demo_data --with-orders [--reset] [--with-demo-accounts]
        [--with-images]

Creates the product catalogue, six invented business customers, inbound
stock (including short-dated and low-stock batches), four retail merch
products with EUR prices, and, with --with-orders, about four weeks of
B2B orders in placed, packed and delivered states. With --with-demo-accounts
it also creates three logins whose password is their username:

    fullstaff        full staff access (ops portal, account management)
    restrictedstaff  restricted staff access (ops portal)
    business         B2B customer, linked to the demo customer with most orders

With --with-images every product gets a drawn picture (_demo_images.py),
stored through the normal product-image upload so thumbnails exist too.

All customers, batches and orders are invented (see _demo_data.py).
Orders go through the same services as the ops portal: business placement,
reservation-backed packing and delivery.

Refuses to run unless DEBUG is true: it is a local development tool and
--reset deletes every order, customer, batch and product.
"""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from accounts.models import CustomerMembership
from accounts.services import (
    create_customer_account,
    create_full_staff_account,
    create_restricted_staff_account,
)
from business.services import create_order
from carts.models import Cart
from customers.models import Customer
from customers.services import create_customer
from fulfillment.services import pack_order
from inventory.models import InventoryBatch
from inventory.services import create_batch
from orders.datatypes import OrderLineInput
from orders.models import Order, OrderLine
from orders.services import deliver_order
from payments.models import PaymentAttempt
from pricing.models import CommercialPrice, PriceAmount
from pricing.services import (
    create_commercial_price,
    ensure_standard_offer,
    set_commercial_price_enabled,
    set_price_amount,
)
from products.image_services import change_product_image
from products.models import Product, ProductProfile
from products.services import create_product
from reservations.models import Allocation

from . import _demo_data as demo
from ._demo_images import product_picture_jpeg

# username == password; local development only (the command needs DEBUG).
DEMO_STAFF_ACCOUNTS = (
    ("fullstaff", create_full_staff_account),
    ("restrictedstaff", create_restricted_staff_account),
)
DEMO_BUSINESS_USERNAME = "business"
DEMO_USERNAMES = tuple(name for name, _ in DEMO_STAFF_ACCOUNTS) + (
    DEMO_BUSINESS_USERNAME,
)

PRODUCT_CATALOG_PATH = Path(__file__).resolve().parent / "seed_demo_products.json"


class Command(BaseCommand):
    help = "Seed synthetic demo data (local development only)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing orders, customers, stock and products first.",
        )
        parser.add_argument(
            "--with-demo-accounts",
            action="store_true",
            help=(
                "Create logins fullstaff, restrictedstaff and business, "
                "each with its username as password."
            ),
        )
        parser.add_argument(
            "--with-orders",
            action="store_true",
            help="Seed B2B orders in placed, packed and delivered states.",
        )
        parser.add_argument(
            "--with-images",
            action="store_true",
            help="Give every product a drawn picture (written to MEDIA_ROOT).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "seed_demo_data only runs with DEBUG=True (local development)."
            )

        if options["reset"]:
            self._reset()
        elif self._data_exists():
            raise CommandError(
                "Data already exists. Run with --reset to recreate it."
            )

        today = timezone.localdate()
        user = None
        if options["with_demo_accounts"]:
            # Recreate rather than reuse: a previous run's logins may remain.
            get_user_model().objects.filter(
                email__in=[f"{name}@example.com" for name in DEMO_USERNAMES]
            ).delete()
            user = self._create_staff_accounts()

        products = self._create_products()
        customers = self._create_customers()

        candy_numbers = [
            number for number, product in products.items() if product.active
        ]
        batches = demo.build_batches(internal_numbers=candy_numbers, today=today)
        self._create_batches(batches, products)

        merch = self._create_merch()
        self._create_batches(demo.merch_batches(today=today), merch)

        summary = (
            f"{len(products)} products, {len(merch)} merch items, "
            f"{len(customers)} customers, {len(batches)} batches"
        )

        if options["with_images"]:
            self._add_images([*products.values(), *merch.values()])
            summary += ", product pictures"

        orders: list[demo.DemoOrder] = []
        if options["with_orders"]:
            orders = demo.build_orders(batches=batches, today=today)
            self._create_orders(orders, products, customers, user)
            summary += f", {len(orders)} orders"

        if options["with_demo_accounts"]:
            self._create_business_account(customers, orders)
            summary += f"; logins: {', '.join(DEMO_USERNAMES)} (password = username)"

        self.stdout.write(self.style.SUCCESS(f"Demo data seeded: {summary}."))

    # ------------------------------------------------------------------
    # reset
    # ------------------------------------------------------------------

    def _data_exists(self) -> bool:
        return (
            Product.objects.exists()
            or Customer.objects.exists()
            or InventoryBatch.objects.exists()
            or Order.objects.exists()
        )

    def _reset(self) -> None:
        # Product pictures are files: remove them first, or each reset
        # would leave the previous run's pictures behind in MEDIA_ROOT.
        for product in Product.objects.filter(profile__image__gt=""):
            change_product_image(product=product, remove_image=True).commit()

        # Children before parents: several relations are PROTECT.
        for model in (
            PaymentAttempt,
            Allocation,      # cascades ops pick-checklist marks
            OrderLine,
            Order,           # cascades retail checkout sessions
            Cart,            # cascades cart lines and business carts
            CustomerMembership,
            PriceAmount,
            CommercialPrice,
            InventoryBatch,
            Customer,
            Product,
        ):
            model.objects.all().delete()

        _reset_sequences(Order, OrderLine, InventoryBatch, Customer, Product)

    # ------------------------------------------------------------------
    # accounts
    # ------------------------------------------------------------------

    def _create_staff_accounts(self):
        """Create the demo staff logins; return the full staff user."""

        users = [
            _demo_login(create(email=f"{name}@example.com", password=name), name)
            for name, create in DEMO_STAFF_ACCOUNTS
        ]
        return users[0]

    def _create_business_account(
        self,
        customers: dict[str, Customer],
        orders: list[demo.DemoOrder],
    ) -> None:
        """A B2B login for the customer with the most orders, so its portal
        has order history to show."""

        keys = [order.customer_key for order in orders] or [demo.CUSTOMERS[0].key]
        key = max(sorted(set(keys)), key=keys.count)

        _demo_login(
            create_customer_account(
                email=f"{DEMO_BUSINESS_USERNAME}@example.com",
                password=DEMO_BUSINESS_USERNAME,
                customer=customers[key],
            ),
            DEMO_BUSINESS_USERNAME,
        )

    # ------------------------------------------------------------------
    # catalogue
    # ------------------------------------------------------------------

    def _create_products(self) -> dict[int, Product]:
        products: dict[int, Product] = {}

        for item in _load_product_catalog():
            result = create_product(
                internal_number=int(item["internal_number"]),
                manufacturer=str(item["manufacturer"]),
                brand=str(item["brand"]),
                name=str(item["name"]),
                weight_per_unit=int(item["weight_per_unit"]),
                stock_unit=str(item.get("stock_unit", Product.StockUnit.BOX)),
                vegan=bool(item["vegan"]),
            )
            product = getattr(result, "item", result)

            if not bool(item.get("active", True)):
                product.active = False
                product.save(update_fields=["active"])

            ensure_standard_offer(
                product=product,
                channel=CommercialPrice.Channel.BUSINESS,
            )
            products[product.internal_number] = product

        return products

    def _add_images(self, products: list[Product]) -> None:
        for product in products:
            ProductProfile.objects.get_or_create(product=product)
            picture = SimpleUploadedFile(
                "demo.jpg",
                product_picture_jpeg(name=product.name, brand=product.brand),
                content_type="image/jpeg",
            )
            change_product_image(product=product, uploaded_image=picture).commit()

    def _create_merch(self) -> dict[int, Product]:
        merch: dict[int, Product] = {}

        for item in demo.MERCH:
            result = create_product(
                internal_number=item.internal_number,
                manufacturer=demo.MERCH_BRAND,
                brand=demo.MERCH_BRAND,
                name=item.name,
                weight_per_unit=item.weight_per_unit,
                stock_unit=Product.StockUnit.PIECE,
            )
            product = getattr(result, "item", result)

            # Merch is sold to retail customers only: a RETAIL offer and no
            # BUSINESS offer, so it stays out of the business catalogue.
            offer = create_commercial_price(
                product=product,
                channel=CommercialPrice.Channel.RETAIL,
            )
            set_price_amount(
                commercial_price=offer,
                currency=PriceAmount.Currency.EUR,
                price=item.retail_price_eur,
            )
            set_commercial_price_enabled(commercial_price=offer, enabled=True)

            merch[item.internal_number] = product

        return merch

    def _create_customers(self) -> dict[str, Customer]:
        return {
            item.key: create_customer(
                name=item.name,
                email=item.email,
                phone_number=item.phone_number,
                country=item.country,
                city=item.city,
                address_line=item.address_line,
            )
            for item in demo.CUSTOMERS
        }

    def _create_batches(
        self,
        batches: list[demo.DemoBatch],
        products: dict[int, Product],
    ) -> None:
        for batch in batches:
            create_batch(
                product=products[batch.internal_number],
                quantity=batch.quantity,
                best_before=batch.best_before,
                location=batch.location,
                batch_id=batch.batch_id,
                today=batch.received,
            )

    # ------------------------------------------------------------------
    # orders
    # ------------------------------------------------------------------

    def _create_orders(
        self,
        orders: list[demo.DemoOrder],
        products: dict[int, Product],
        customers: dict[str, Customer],
        user,
    ) -> None:
        for index, data in enumerate(orders, start=1):
            try:
                order = create_order(
                    customer=customers[data.customer_key],
                    lines=[
                        OrderLineInput.units(
                            product=products[line.internal_number],
                            quantity=line.quantity,
                        )
                        for line in data.lines
                    ],
                    user=user,
                )
                if data.status in ("packed", "delivered"):
                    order = pack_order(order=order, user=user)
                if data.status == "delivered":
                    order = deliver_order(order=order, user=user)
            except Exception as error:
                raise CommandError(
                    f"Could not seed demo order #{index} "
                    f"({data.customer_key}, {data.placed_on}): {error}"
                ) from error

            _backdate(order=order, placed_on=data.placed_on, status=data.status)


# ======================================================================
# helpers
# ======================================================================


def _demo_login(created, username: str):
    """Accounts are created with the e-mail as username; demo logins use a
    short username so they are quick to type."""

    user = created.user
    user.username = username
    user.save(update_fields=["username"])
    return user


def _load_product_catalog() -> list[dict[str, Any]]:
    with PRODUCT_CATALOG_PATH.open(encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list) or not all(isinstance(i, dict) for i in data):
        raise CommandError(f"{PRODUCT_CATALOG_PATH.name} must be a list of objects.")

    return data


def _at(day: date, hour: int) -> datetime:
    return timezone.make_aware(datetime.combine(day, time(hour=hour)))


def _backdate(*, order: Order, placed_on: date, status: str) -> None:
    """Move an order's timestamps back to when the demo says it happened."""

    placed = _at(placed_on, 9)
    fields: dict[str, datetime] = {
        "created_at": placed,
        "placed_at": placed,
        "updated_at": placed,
    }

    if status in ("packed", "delivered"):
        packed = _at(placed_on + timedelta(days=demo.PACK_AFTER_DAYS), 14)
        fields["packed_at"] = packed
        fields["updated_at"] = packed

    if status == "delivered":
        delivered = _at(placed_on + timedelta(days=demo.DELIVER_AFTER_DAYS), 10)
        fields["delivered_at"] = delivered
        fields["updated_at"] = delivered

    Order.objects.filter(pk=order.pk).update(**fields)


def _reset_sequences(*models) -> None:
    """Restart primary keys at 1 so demo ids are stable between resets."""

    with connection.cursor() as cursor:
        for model in models:
            table = model._meta.db_table

            if connection.vendor == "sqlite":
                cursor.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' AND name = 'sqlite_sequence'"
                )
                if cursor.fetchone() is not None:
                    cursor.execute(
                        "DELETE FROM sqlite_sequence WHERE name = %s", [table]
                    )

            elif connection.vendor == "postgresql":
                cursor.execute(
                    "SELECT pg_get_serial_sequence(%s, %s)",
                    [table, model._meta.pk.column],
                )
                row = cursor.fetchone()
                if row and row[0]:
                    cursor.execute("SELECT setval(%s, 1, false)", [row[0]])

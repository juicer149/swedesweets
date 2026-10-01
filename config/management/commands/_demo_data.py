"""Synthetic demo data for `seed_demo_data`.

Everything here is invented: shop names, addresses, e-mail addresses,
phone numbers, batches and orders. Phone numbers use the French range
reserved for fiction (+33 1 99 00 xx xx) and e-mail addresses use
example.com. The product catalogue (seed_demo_products.json) lists
publicly sold candy and is the only real-world data.

The generator is deterministic for a given `today`: the same structure
every run, with dates relative to the day it runs, so expiry queues and
recent orders always look current.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

SEED = 20260101

# Days between placing, packing and delivering a demo order.
PACK_AFTER_DAYS = 1
DELIVER_AFTER_DAYS = 2

# Orders younger than PACKED_FROM_AGE days are placed, younger than
# DELIVERED_FROM_AGE are packed, older ones are delivered.
PACKED_FROM_AGE = 3
DELIVERED_FROM_AGE = 7


@dataclass(frozen=True, slots=True)
class DemoCustomer:
    key: str
    name: str
    email: str
    phone_number: str
    city: str
    address_line: str
    country: str = "FR"


@dataclass(frozen=True, slots=True)
class DemoMerch:
    internal_number: int
    name: str
    weight_per_unit: int
    retail_price_eur: Decimal
    quantity: int


@dataclass(frozen=True, slots=True)
class DemoBatch:
    internal_number: int
    batch_id: str
    quantity: int
    received: date
    best_before: date
    location: str


@dataclass(frozen=True, slots=True)
class DemoOrderLine:
    internal_number: int
    quantity: int


@dataclass(frozen=True, slots=True)
class DemoOrder:
    customer_key: str
    placed_on: date
    status: str  # "placed" | "packed" | "delivered"
    lines: tuple[DemoOrderLine, ...]


CUSTOMERS: tuple[DemoCustomer, ...] = (
    DemoCustomer(
        key="epicerie_du_col",
        name="Épicerie du Col",
        email="epicerie-du-col@example.com",
        phone_number="+33199000101",
        city="Chamonix-Mont-Blanc",
        address_line="14 rue des Glaciers",
    ),
    DemoCustomer(
        key="comptoir_sucre",
        name="Le Comptoir Sucré",
        email="comptoir-sucre@example.com",
        phone_number="+33199000102",
        city="Annecy",
        address_line="8 rue des Mésanges",
    ),
    DemoCustomer(
        key="bazar_des_cimes",
        name="Bazar des Cimes",
        email="bazar-des-cimes@example.com",
        phone_number="+33199000103",
        city="Megève",
        address_line="2 place du Torrent",
    ),
    DemoCustomer(
        key="superette_alpage",
        name="Supérette de l'Alpage",
        email="superette-alpage@example.com",
        phone_number="+33199000104",
        city="Sallanches",
        address_line="31 avenue des Sapins",
    ),
    DemoCustomer(
        key="cafe_lumiere",
        name="Café Lumière",
        email="cafe-lumiere@example.com",
        phone_number="+33199000105",
        city="Saint-Gervais-les-Bains",
        address_line="5 chemin du Belvédère",
    ),
    DemoCustomer(
        key="kiosque_du_lac",
        name="Kiosque du Lac",
        email="kiosque-du-lac@example.com",
        phone_number="+33199000106",
        city="Thonon-les-Bains",
        address_line="1 quai des Voiles",
    ),
)

# Retail merchandise: sold to consumers in the storefront, priced in EUR.
MERCH: tuple[DemoMerch, ...] = (
    DemoMerch(901, "Hoodie", 600, Decimal("55.00"), 20),
    DemoMerch(902, "T-shirt", 200, Decimal("25.00"), 30),
    DemoMerch(903, "Cap Classic", 150, Decimal("22.00"), 15),
    DemoMerch(904, "Cap Trucker", 150, Decimal("22.00"), 15),
)

MERCH_BRAND = "SwedeSweets"


def _location(index: int) -> str:
    return f"{'ABCD'[index % 4]}{1 + (index // 4) % 6}"


def build_batches(
    *,
    internal_numbers: list[int],
    today: date,
) -> list[DemoBatch]:
    """Inbound stock for every active candy product.

    Every product gets one long-dated batch. Every 7th product also has a
    small batch close to its best-before date (fills the expiry queue), and
    every 11th product's main batch is small (fills the low-stock queue).
    """

    rng = random.Random(SEED)
    batches: list[DemoBatch] = []

    for index, number in enumerate(sorted(internal_numbers)):
        low_stock = index % 11 == 5
        batches.append(
            DemoBatch(
                internal_number=number,
                batch_id=f"DEMO-{number:03d}-A",
                quantity=rng.randint(2, 4) if low_stock else rng.randint(12, 40),
                received=today - timedelta(days=rng.randint(20, 90)),
                best_before=today + timedelta(days=rng.randint(90, 300)),
                location=_location(index),
            )
        )

        if index % 7 == 3:
            batches.append(
                DemoBatch(
                    internal_number=number,
                    batch_id=f"DEMO-{number:03d}-B",
                    quantity=rng.randint(4, 10),
                    received=today - timedelta(days=rng.randint(120, 200)),
                    best_before=today + timedelta(days=rng.randint(5, 20)),
                    location=_location(index + 1),
                )
            )

    return batches


def merch_batches(*, today: date) -> list[DemoBatch]:
    return [
        DemoBatch(
            internal_number=item.internal_number,
            batch_id=f"DEMO-{item.internal_number:03d}-A",
            quantity=item.quantity,
            received=today - timedelta(days=30),
            best_before=today + timedelta(days=3650),
            location="M1",
        )
        for item in MERCH
    ]


def build_orders(
    *,
    batches: list[DemoBatch],
    today: date,
    count: int = 28,
    days: int = 56,
) -> list[DemoOrder]:
    """B2B orders spread over the last `days` days, oldest first.

    Quantities are drawn only from long-dated stock and never exceed what
    is left, so every order can be placed whatever order the stock pool
    takes batches in.
    """

    rng = random.Random(SEED + 1)

    available: dict[int, int] = {}
    for batch in batches:
        if (batch.best_before - today).days >= 60:
            available[batch.internal_number] = (
                available.get(batch.internal_number, 0) + batch.quantity
            )

    orders: list[DemoOrder] = []
    # A fixed handful still in progress, the rest delivered over the period.
    in_progress = [0, 0, 1, 2, 3, 4, 5, 6]
    delivered = [
        rng.randint(DELIVERED_FROM_AGE, days)
        for _ in range(count - len(in_progress))
    ]
    ages = sorted(delivered + in_progress, reverse=True)

    for age in ages:
        in_stock = sorted(number for number, left in available.items() if left >= 2)
        if len(in_stock) < 3:
            break

        picked = rng.sample(in_stock, k=min(len(in_stock), rng.randint(3, 7)))
        lines = []
        for number in sorted(picked):
            quantity = rng.randint(1, min(3, available[number] - 1))
            available[number] -= quantity
            lines.append(DemoOrderLine(internal_number=number, quantity=quantity))

        if age >= DELIVERED_FROM_AGE:
            status = "delivered"
        elif age >= PACKED_FROM_AGE:
            status = "packed"
        else:
            status = "placed"

        orders.append(
            DemoOrder(
                customer_key=rng.choice(CUSTOMERS).key,
                placed_on=today - timedelta(days=age),
                status=status,
                lines=tuple(lines),
            )
        )

    return orders

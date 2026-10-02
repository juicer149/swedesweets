# SwedeSweets

[![CI](https://github.com/juicer149/swedesweets/actions/workflows/ci.yml/badge.svg)](https://github.com/juicer149/swedesweets/actions/workflows/ci.yml)

Order, inventory and payment system for a small Swedish candy wholesaler
operating in the French Alps. Staff take and pack orders, shops order online,
and consumers buy merchandise with card payment.

Built with Django by one developer as a first client project. The operations
and B2B workflows run in production; the retail storefront is in development.

## What it does

Three kinds of users, each with its own interface:

| Interface | Who | What |
|---|---|---|
| **Ops portal** `/ops/` | staff | dashboard queues (placed, packed, expiring, low stock), orders for any customer, pick checklist while packing, inventory batches, products and pricing, accounts |
| **Business portal** `/my/` | shops (B2B) | catalogue with their available stock and special offers, cart, order history, repeat an earlier order |
| **Storefront** `/shop/` | consumers | catalogue, cart, checkout with delivery-area check, card payment via SumUp |

The site is in English and French.

## Design

The domain is split along a few deliberate lines. `ARCHITECTURE.md` has the
full rules; the main ones:

**Actor and sales channel are separate axes.** Who uses an interface (staff,
shop, consumer) is not the same as which commercial rules apply (BUSINESS or
RETAIL). Staff in the ops portal can place a business order; the portal does
not decide the rules, the channel does.

**Products are labels; offers decide where they are sold.** A product says
what something is. Stock says what is on the shelf. A commercial offer per
channel says whether, and at what price, it is sold there. A product can be
sold to shops, to consumers, to both at different prices, or to neither, and a
single batch can carry its own offer (short-dated stock at a lower price, say)
without the same units also being sold at the standard price.

**Each piece of state has one owner.** Inventory owns physical stock,
reservations own what is promised to orders, pricing owns offers, orders own
the order lifecycle. Layers depend inward only:

```text
portals             ops_portal, business_portal, storefront
   ↓
sales channels      business, retail
   ↓
shared capabilities accounts, customers, products, pricing, carts, orders,
                    inventory, reservations, payments, fulfillment
```

`config` wires the application together. These rules are enforced by a test
that parses every module's imports (`config/tests/test_architecture_imports.py`).

**Access is deny by default.** Every route declares the capability it needs;
roles (full staff, restricted staff, business customer) grant capabilities.

**Payments go through a provider interface.** SumUp is the real provider; a
fake provider stands in locally and in tests, including failure, cancellation
and webhook reconciliation.

## Try it locally

Requires Python 3.12.

```bash
git clone git@github.com:juicer149/swedesweets.git
cd swedesweets
make setup         # virtualenv, dependencies, migrations (SQLite)
make reset-demo    # synthetic demo data and logins
make run           # http://localhost:8000/
```

Log in with any of these (password = username):

| Username | Sees |
|---|---|
| `fullstaff` | ops portal, including account management |
| `restrictedstaff` | ops portal |
| `business` | business portal for a demo shop with order history |

The storefront needs no login. Payments use the fake provider locally.

All demo data is invented: six shops, stock with short-dated and low-stock
batches, four merch products with retail prices, and B2B orders in every
state. Only the product catalogue (publicly sold candy) is real. See
`config/management/commands/README.md`.

## Tests

```bash
make test     # about 1 000 tests, pytest
make check    # Django system checks
```

CI runs the checks, a missing-migrations check, `collectstatic` and the test
suite on every push.

## Stack

- Python 3.12, Django 6
- PostgreSQL in production, SQLite locally
- Server-rendered templates, vanilla JavaScript, hand-written CSS
- Railway for hosting; SumUp for card payments

## Project structure

```text
ops_portal/        staff UI
business_portal/   B2B customer UI
storefront/        public retail UI

business/          BUSINESS channel rules: catalogue, cart, ordering
retail/            RETAIL channel rules: catalogue, checkout, delivery areas

accounts/          identity, roles, capabilities
customers/         business customers
products/          product identity
pricing/           commercial offers and prices
carts/             generic carts
orders/            orders and their lifecycle
inventory/         physical stock (batches)
reservations/      stock promised to orders
payments/          payment attempts and providers
fulfillment/       packing and delivery

config/            settings, URL and policy composition, management commands
common/            shared UI and application primitives
```

## Configuration

Settings come from environment variables; see `.env.example` and
`config/settings.py`. The main ones:

```text
DJANGO_SECRET_KEY  DJANGO_DEBUG  DJANGO_ALLOWED_HOSTS  DJANGO_CSRF_TRUSTED_ORIGINS
PGHOST  PGDATABASE  PGUSER  PGPASSWORD  PGPORT
EMAIL_BACKEND  DEFAULT_FROM_EMAIL  SERVER_EMAIL
SUMUP_API_KEY  SUMUP_MERCHANT_CODE
```

Locally the console email backend and the fake payment provider need no
configuration.

## Deployment

Deployed on Railway (`railway.json`). On start it runs migrations, syncs the
retail delivery areas and ensures the admin user, then serves with gunicorn.
Production uses PostgreSQL, `DEBUG=False` and secrets from the environment.

## Status

Live: operations (orders, packing, delivery, inventory, pricing, accounts) and
B2B ordering.

Next: retail launch (the storefront and checkout are built; the SumUp
integration still has to be verified against the live API), transactional
email, and invoice generation for B2B orders.

## Documentation

- `ARCHITECTURE.md`: boundaries, ownership and dependency rules
- `accounts/README.md`: identity, roles and capabilities
- `config/management/commands/README.md`: management commands and demo data

## License

All rights reserved. The code is published for reference; it is not licensed for reuse.

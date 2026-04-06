# Catalog Design

## Purpose

The `catalog` app owns product truth.

It is responsible for:

- storing products
- storing categories and tags
- exposing product reads for browsing and ordering
- deciding which products are active/orderable

It is **not** responsible for order history or order persistence.
That belongs to `ordering`.

---

## Core mental model

`Category -> contains -> Products`

A `Product` is the source of truth for product metadata:
- code
- name
- description
- ingredients
- optional weight and box size
- category
- tags
- image
- active/inactive status

The catalog represents the current product truth.

---

## Boundary with ordering

`catalog` owns live product data.

`ordering` may read product data from `catalog` when a store places an order,
but once the order is created, ordering stores snapshots in `OrderItem`.

Rule of thumb:

- current product truth lives in `catalog`
- historical order truth lives in `ordering`

Examples:

- `list_orderable_products()` belongs to `catalog`
- `latest_order_for_store()` belongs to `ordering`

---

## Internal structure

### Top-level
- `models.py`: persistence schema for products, categories, and tags
- `views.py`: HTTP adapter only
- `urls.py`: route definitions
- `admin.py`: admin configuration
- `apps.py`: Django app config

### `read/`
Read queries for catalog data.

Examples:
- list active products grouped by category
- list orderable products
- get product detail

### `domain/`
Small catalog-specific rules.

Examples:
- whether a product is orderable
- future visibility rules for portal/catalog display

At the current stage, `catalog` is mostly a read-oriented app plus admin-managed writes,
so there is no separate `write/` layer yet.

---

## Current reads

Main queries in this app:

- `list_active_products_grouped_by_category()`
- `list_orderable_products()`
- `get_product_detail(product_id=...)`

These queries should live in `catalog/read/selectors.py`,
not inside views.

---

## Why there is no write/ yet

Catalog writes currently happen through Django admin.

That means:

- there is no public product creation workflow in the portal
- there is no bulk import/use case layer yet
- there is no need for `commands.py` or `actions.py` yet

If future workflows are added, such as CSV import, supplier sync, or backoffice tools,
a `write/` layer can be introduced.

---

## Design philosophy

This app prefers:

- product truth in one place
- read queries separated from views
- explicit boundaries toward ordering
- simple structure until real write workflows appear

The goal is to make it obvious that `catalog` answers:

- what products exist?
- which products are active?
- how should products be presented?

while `ordering` answers:

- what was ordered?
- by whom?
- when?
- in what status?

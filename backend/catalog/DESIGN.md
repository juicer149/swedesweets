# Catalog Design
## Purpose
The `catalog` app owns current product truth.

It is responsible for:

- storing products
- storing categories and tags
- exposing product reads for browsing and ordering
- deciding which products are visible in the catalog
- deciding which products are orderable right now

It is **not** responsible for order history or order persistence.
That belongs to `ordering`.

---

## Core mental model

`Category -> contains -> Products`

A `Product` is the source of truth for current product metadata:

- code
- name
- description
- ingredients
- optional weight metadata
- optional packaging metadata
- category
- tags
- image
- visibility
- orderability

The catalog represents the **current** truth about products.

---

## Visibility vs orderability

These are intentionally separate concerns.

### `is_visible`
Controls whether the product appears in the catalog UI.

Examples:
- a product can remain visible while temporarily out of stock
- a product can be hidden from presentation entirely

### `is_orderable`
Controls whether a store may order the product right now.

Examples:
- a product can be visible but not orderable if stock is unavailable
- a product can be disabled for ordering without disappearing from the catalog

This separation avoids overloading one boolean field with multiple meanings.

---

## Product metadata

Different product families need different metadata.

### `weight_grams`
Useful when weight matters, such as pick and mix candy.

In the current business, loose candy boxes may all have the same selling price
even if their weights differ. That means weight is currently descriptive metadata,
not necessarily pricing logic.

### `units_per_box`
Useful when packaging count matters, such as chips where one box contains
a number of sellable bags.

These fields are optional because they are not universally meaningful for all
products.

---

## Tags vs categories

### Category
Represents the primary product family or section.

Examples:
- Pick and mix candy
- Chips

Categories answer:
- what kind of product family is this?

### Tag
Represents cross-cutting descriptive traits used for filtering or richer UI.

Examples:
- Sour
- Sweet
- Chocolate
- Vegan
- New

Tags answer:
- what traits or properties does this product have?

Categories and tags solve different problems and should remain separate.

---

## Boundary with ordering

`catalog` owns live product data.

`ordering` may read product data from `catalog` when a store places an order,
but once the order is created, `ordering` stores snapshots in `OrderItem`.

Rule of thumb:

- current product truth lives in `catalog`
- historical order truth lives in `ordering`

Examples:

- `list_orderable_products()` belongs to `catalog`
- `latest_order_for_store()` belongs to `ordering`

This boundary is important because catalog data may change over time while
historical orders must remain stable.

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
- list visible products grouped by category
- list orderable products
- get product detail

### `domain/`
Small catalog-specific rules.

Examples:
- whether a product is visible
- whether a product is orderable

At the current stage, `catalog` is mostly a read-oriented app plus admin-managed writes,
so there is no separate `write/` layer yet.

---

## Current reads

Main queries in this app:

- `list_visible_products_grouped_by_category()`
- `list_orderable_products()`
- `get_product_detail(product_id=...)`

These queries should live in `catalog/read/selectors.py`,
not inside views.

### Read responsibilities

#### `list_visible_products_grouped_by_category()`
Used by the public catalog page.

This answers:
- which products should visitors currently see?
- how should they be grouped?

#### `list_orderable_products()`
Used by the ordering flow.

This answers:
- which products may stores currently order?

#### `get_product_detail(product_id=...)`
Used by the public product detail page.

This should return only visible products, because invisible products are not
part of the public catalog surface.

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

## Current business assumptions

The current business has a mixed catalog:

- pick and mix candy
- chips
- likely more packaged or grouped products later

Because of this, catalog metadata cannot assume one universal physical model.

Some products care more about:
- weight

Others care more about:
- units per box

The schema is therefore intentionally permissive and descriptive rather than overly strict.

---

## Design philosophy

This app prefers:

- product truth in one place
- read queries separated from views
- explicit boundaries toward ordering
- separate semantics for visibility and orderability
- simple structure until real write workflows appear

The goal is to make it obvious that `catalog` answers:

- what products exist right now?
- which products are visible?
- which products are orderable?
- how should products be presented?

while `ordering` answers:

- what was ordered?
- by whom?
- when?
- in what number of boxes?
- in what status?

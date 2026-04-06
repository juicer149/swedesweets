# Ordering Design
## Purpose

The `ordering` app owns the store ordering workflow.

It is responsible for:

- creating orders from store input
- storing immutable order snapshots
- exposing order history and latest-order reads
- enforcing ordering-specific business rules

It is **not** the source of truth for products. Product availability and product data come from `catalog`.

---

## Core mental model

`Store -> places -> Order -> contains -> OrderItems`

An `Order` is a persisted fact:
- it belongs to one store
- it has a creation time
- it has a current status
- it contains snapshot line items

An `OrderItem` is also a fact:
- product identity is copied into the item at order time
- later catalog changes must not rewrite history

---

## Architecture inside the app

The app is split into three internal areas:

### `write/`
Handles state changes.

Examples:
- parse submitted order quantities
- validate write input
- create `Order` + `OrderItem`
- run DB transaction

Typical flow:
`request.POST -> parsing -> command -> action -> ORM write`

### `read/`
Handles queries and view-oriented reads.

Examples:
- latest order for a store
- order history for a store

This side does not change state.

### `domain/`
Shared business meaning and invariants.

Examples:
- quantity must be > 0
- inactive store cannot place orders
- an order must contain at least one line
- the same product must not appear twice in one order

`domain/` is shared by the app, but is used mostly by `write/`.

---

## File responsibilities

### Top-level
- `models.py`: persistence schema for `Order` and `OrderItem`
- `views.py`: HTTP adapter only
- `urls.py`: route definitions
- `admin.py`: admin configuration
- `authz.py`: request/store access checks near the web layer

### `write/`
- `commands.py`: typed input/result objects for write flow
- `parsing.py`: raw form data -> internal write structures
- `actions.py`: write use cases such as `place_order`

### `read/`
- `selectors.py`: read queries such as order history and latest order

### `domain/`
- `errors.py`: domain-specific exceptions
- `policies.py`: business rules
- `value_objects.py`: small validated types such as `Quantity`

---

## Boundary with `catalog`

`ordering` does not own products.

`catalog` is responsible for:
- product source of truth
- which products exist
- whether a product is active/orderable
- product metadata such as code, name, category

`ordering` may read product data from `catalog` when building an order,
but once the order is created, it stores product snapshots locally in `OrderItem`.

Rule of thumb:
- product truth lives in `catalog`
- order truth lives in `ordering`

If a selector such as `list_orderable_products()` is only used to read active products, it conceptually belongs to `catalog`.
It may temporarily exist as a local wrapper in `ordering/read/selectors.py` for convenience, but the long-term home is `catalog`.

---

## Order lifecycle

Current MVP lifecycle:

- `pending`
- `packed`
- `delivered`

The status is modeled as one field with a linear progression.

Why not multiple booleans?
Because multiple booleans allow invalid combinations and do not express a single current state clearly.

Why not a bitmask?
Because the lifecycle is linear, not combinatorial.

---

## Invariants

Important invariants in ordering:

- a store user must have a store
- an inactive store cannot place orders
- an order must contain at least one line
- quantity must be a positive integer
- one product may appear only once per order
- orders are not edited after creation
- product code/name are copied into `OrderItem` at creation time

---

## Why snapshot order items exist

`OrderItem` stores:
- `product_code`
- `product_name`
- `quantity`

instead of relying on a live foreign key to `Product`.

This preserves historical accuracy:
- if a product is renamed later, old orders still show the old name
- if catalog metadata changes, past orders remain true to what was ordered

---

## Design philosophy

This app prefers:

- explicit flows over hidden framework magic
- small, named stages over large views
- immutable order facts over in-place editing
- simple status progression over premature complexity
- clarity over cleverness

The goal is that a developer should be able to point at the pipeline and say:

- this is request parsing
- this is business validation
- this is the write action
- this is the read query
- this is the persistence model

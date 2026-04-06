# ordering
`ordering` is responsible for order placement and order history for authenticated stores.

This is the most business-critical app in the system. The rules and history here must be stable, clear, and easy to follow.

## Purpose

The app replaces today’s manual SMS-based ordering with a simple partner flow where a store can:

- place a new order
- view its order history
- view details for a single order

## Core Idea

An order is **not** a reference to today’s catalog.  
An order is a **historical snapshot** of what the store actually ordered at a specific point in time.

This means old orders must not change just because the catalog changes later.

## Responsibilities

The app is responsible for:

- receiving order input from the partner portal
- validating order contents
- creating orders and order lines
- preserving a historical snapshot of product data
- exposing read selectors for order history and order details
- expressing ordering-related domain errors and invariants

## Non-responsibilities

The app is not responsible for:

- authenticating users (`accounts`)
- deciding which products are publicly available in the catalog (`catalog`)
- receiving public partner inquiries (`partner_request`)

## Domain Language

### Store
The store that places the order.

### Order
An aggregate that belongs to exactly one store.

### OrderItem
A historical snapshot line within an order.

### Boxes
The number of boxes ordered for a given product.

This matters:
`boxes` means **number of boxes**, not number of individual consumer units.

Examples:
- 3 boxes of pick-and-mix candy
- 2 boxes of chips, where each box contains multiple units

### Product code
The business-facing product identifier that stores recognize.

Even though internal write flows currently use `product_id` technically, the product code is the most important business identity in order history.

## Architecture

The app is split into clear layers.

### `views.py`
The HTTP layer.

Responsibilities:
- read the request
- fetch the current store
- call parsing/read/write functions
- render templates or redirect

Views should not carry business rules beyond what is necessary.

### `authz.py`
Access control close to the HTTP edge.

Responsibilities:
- ensure that the request user is linked to a store
- stop obviously invalid access early

### `read/selectors.py`
Read models and queries.

Responsibilities:
- fetch order history
- fetch the latest order
- fetch a single order for a store
- annotate read data such as `line_count` and `total_boxes`

### `write/parsing.py`
Input interpretation for the order form.

Responsibilities:
- parse the matrix-style form product by product
- validate user-facing input errors
- build an explicit, immutable form-state object

This is not the same thing as final domain validation.

### `write/commands.py`
Small explicit DTO-like objects for the write flow.

Responsibilities:
- carry the write intent in a clear format
- separate HTTP/form data from the write use case

### `write/actions.py`
The use-case layer.

Responsibilities:
- execute `place_order`
- load store and products
- protect invariants
- create the order and item snapshots atomically

### `domain/errors.py`
Domain-specific errors.

Examples:
- empty order
- invalid box quantity
- inactive store
- invalid product selection

### `domain/policies.py`
Small, pure business rules that do not need the ORM.

### `domain/value_objects.py`
Small types with their own invariants.

Example:
- `BoxQuantity`

## Important Invariants

### 1. An order must contain at least one line
It must not be possible to create empty orders.

### 2. An inactive store must not be allowed to place orders
This is protected both near the request edge and in the write layer.

### 3. Box quantity must be valid
The box quantity must be:
- an integer
- greater than zero
- not unreasonably large according to the current limit

### 4. The same product must not appear multiple times in the same order
This is protected both logically and in the database.

### 5. Order history must remain stable
Order lines snapshot the product data needed to understand what was ordered, even if the catalog changes later.

## Snapshot Principle

`OrderItem` stores not only a reference to a product, but also a snapshot of the product data relevant at the time of ordering, for example:

- product code
- product name
- category
- weight
- units per box
- number of boxes ordered

This makes the history deterministic and audit-friendly.

## Why not just use catalog objects directly?

Because the catalog is present-time data.

Ordering needs historical data.

If a product later:
- changes name
- changes category
- changes pack size
- is deactivated

old orders should still continue to describe what was actually ordered at that time.

## Why not just use Django Forms?

The order UI is a matrix with one field per product, not a natural `ModelForm` case.

That is why the app uses an explicit parsing layer and an immutable form-state object:

- `OrderFormRow`
- `ParsedOrderForm`

This makes the flow clearer than trying to force everything into standard Django form magic.

## Current Status Model

Order status is currently simple:

- `pending`
- `packed`
- `delivered`

This is enough for the MVP.

The next likely step is to make status transitions more explicit so that invalid jumps cannot happen by mistake.

## Future Development

Likely next steps:

- explicit transition logic for order status
- better admin/workflow support for packing and delivery
- possible export or admin order overview
- possibly faster ordering via product code as primary input
- possibly a more advanced max-box rule depending on product or category

## Design Principles

### Clear contracts before magic
The order flow should be easy to follow from request to persistence.

### Read and write are kept separate
Queries should not carry write logic, and write use cases should not be shaped by templates.

### History must remain stable
The present-day catalog and historical order data are different things and should be treated differently.

### Small rules at the right level
- user-friendly errors in parsing
- hard invariants in the domain/use case layer
- access rules close to the request edge

This makes the system robust without making it heavy.

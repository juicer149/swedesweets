# SwedeSweets — Design Notes (v0.1)

Date: 2026-03-24

This document captures the current design decisions for SwedeSweets v0.1.
The goal is to keep the system simple, professional, and mobile-friendly while
preserving a clean separation between **domain** (pure business rules) and
**Django** (web + persistence).

---

## Goals

### Product goals
- Replace an unstructured SMS ordering process with structured orders.
- Stores can log in quickly (mobile-first) and place restocking requests.
- Supplier can pack/confirm what was actually delivered.
- Keep v0.1 minimal but forward-compatible.

### Engineering goals
- Keep the **domain layer framework-independent** and fully testable.
- Make invalid states hard/impossible to represent.
- Keep Django as an adapter layer (DB + views/API), not the source of business rules.

---

## Domain Layer

Location: `src/swedesweets/domain/`

### Core workflow model

We model ordering as two immutable snapshots:

1. **RequestedOrder** (store intent)
   - created by the store
   - includes `created_at`
   - includes requested items (`product_id`, `quantity`)

2. **FulfilledOrder** (supplier fact)
   - created by the supplier when packing/accepting the order
   - includes `packed_at`
   - includes `delivered_at` (nullable)
   - includes `packing_notes` (free text for deviations / out-of-stock notes)
   - includes fulfilled items (`product_id`, `quantity`)

Delivery is modeled by creating a new fulfilled snapshot where `delivered_at` is set
(`mark_delivered()` returns a new instance).

### Why Requested vs Fulfilled?
- High traceability: “what was requested” vs “what was actually delivered”
- Enables robust handling of out-of-stock and mistakes without mutating history
- Makes supplier UX easy: start from requested quantities, then adjust

### Diff
We provide a domain diff between requested and fulfilled items.

- diff is computed per `product_id` with summed quantities
- we do **not** use `set()` diff due to quantities and duplicates

### Duplicates / Normalization
The domain is tolerant to duplicate lines (same product repeated), because data can
arrive from UI/API/integrations.

- domain normalizes items by summing quantities per product and sorting
- DB layer may enforce uniqueness per order+product for data integrity

### Value objects
We use value objects for domain correctness:
- `Quantity` must be `int` and `> 0`
- IDs: `StoreId`, `ProductId`, `OrderId` wrap UUID
- datetimes must be timezone-aware (UTC recommended)

### Ports & Use Cases
To keep the domain isolated from Django, we define ports:

- `RequestedOrderRepository`
- `FulfilledOrderRepository`
- `Clock`
- `UnitOfWork` (optional)

Use cases (orchestration, still framework-independent):
- `request_order`
- `pack_order`
- `deliver_order`
- `get_order_diff`

We also maintain small in-memory adapters for tests:
- `FixedClock`, `InMemoryRequestedOrders`, `InMemoryFulfilledOrders`, `NoopUnitOfWork`

### Testing strategy
Domain has:
- unit tests for invariants + diff
- workflow-like tests for full requested → fulfilled → delivered flows
- use-case tests using the in-memory adapters

---

## Django Layer (v0.1 plan)

Location: `backend/`

Django is the web + persistence adapter.
It should map DB data to/from domain concepts, and enforce authentication/permissions.

### Apps
We use separate apps to keep responsibilities clear:

- `accounts` — store accounts (B2B)
- `catalog` — products + category/tags/images
- `ordering` — requested orders + fulfilled orders

A future B2C merch flow (hoodies/t-shirts) should live in a separate app
(e.g. `merch` or `shop`) with different UX/payment and likely without store login.

---

## Authentication / Accounts (B2B)

### Decision: one login per store (v0.1)
Currently one person (store manager) sends SMS orders; therefore v0.1 uses **one account per store**.

Implementation:
- Use Django built-in `User` (sessions auth)
- Create a `Store` model as a profile linked via `OneToOneField(User)`
- Admin creates store accounts initially (no public signup)
- Store has metadata: `name`, `phone`, `address`, `is_active`

Supplier access:
- Supplier users are handled as Django users with `is_staff=True` (v0.1)

Rationale:
- fast and professional login UX
- controlled onboarding (B2B)
- minimal risk of random users placing orders

---

## Catalog / Products

### Categories + Tags
Products should be easily browsable on mobile.

We model:
- `ProductCategory` (single main category, sorted, for sectioning: candy/chips/drinks)
- `ProductTag` (ManyToMany) for attributes and filters:
  - sweet/sour/chocolate
  - gluten-free/lactose-free
  - etc.

Rationale:
- Category gives a stable primary grouping (best for mobile)
- Tags enable flexible filtering and future requirements

### Product image (avatar)
Products can optionally have a single image for faster selection.

Decision:
- `Product.image` is **optional**
- no snapshotting of image in orders (image is only for browsing at order time)
- single image is sufficient for v0.1
- merch might later require multiple images and belongs in a separate app

Implementation:
- `ImageField(upload_to="product-images/", null=True, blank=True)`
- use Pillow
- configure `MEDIA_URL` and `MEDIA_ROOT` for local dev

---

## Ordering / Persistence (Django models)

We store orders in Django in a way that is compatible with the domain workflow.

### Requested order
- `RequestedOrderModel`
  - UUID PK
  - FK to `Store`
  - `created_at`

- `RequestedOrderItemModel`
  - FK to requested order
  - FK to Product
  - `requested_qty`
  - snapshot fields: `product_code`, `product_name`
  - uniqueness constraint (requested_order, product)

### Fulfilled order
- `FulfilledOrderModel`
  - UUID PK
  - OneToOne to requested order
  - `packed_at`
  - `delivered_at` (nullable)
  - `packing_notes` (text)

- `FulfilledOrderItemModel`
  - FK to fulfilled order
  - FK to Product
  - `fulfilled_qty`
  - snapshot fields: `product_code`, `product_name`
  - uniqueness constraint (fulfilled_order, product)

Rationale for snapshot fields:
- product names/codes may change in the catalog, but order history remains readable

---

## UI (v0.1 intent)

### Store UI
- mobile-first page for placing a requested order
- uses Django session auth (login required)
- products displayed with category sections and optional images
- quantities default to 0, user sets desired qty
- submit creates a requested order + items (qty > 0)

### Supplier UI
- staff-only pages
- list requested orders that are not delivered
- pack view defaults packed qty = requested qty and allows adjustment
- optional `packing_notes` for deviations
- deliver action sets `delivered_at`

---

## Explicit Non-goals (v0.1)
- public signup / self-serve onboarding
- complex permissions model beyond store vs staff
- inventory/stock management
- pricing / invoicing
- notifications
- partial deliveries (1 requested order → multiple shipments)

---

## Future evolution ideas
- multiple users per store (if needed)
- richer fulfillment: per-item missing reasons, substitutions
- partial deliveries / shipment model
- merch/B2C app with separate checkout/payment

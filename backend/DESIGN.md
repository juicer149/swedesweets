# SwedeSweets Backend — System Design
## Purpose
This project is a Django-based MVP for a B2B web application used by a small company
that imports Swedish sweets to France and delivers to retail stores.

The system has two main public/business surfaces:

- a **public marketing/catalog surface**
- a **partner portal** for authenticated stores to place orders and view order history

There is also a small **public partner interest form** for stores that want to become resellers.

The project uses Django because it provides a fast and reliable MVP foundation:

- authentication
- admin
- ORM
- migrations
- templates
- routing

The goal is to keep Django’s strengths while still maintaining explicit boundaries,
clear contracts, and stable business history.

---

## Core design philosophy

This project prefers:

- clear app boundaries
- explicit read/write separation where it pays off
- minimal hidden behavior
- stable historical data
- admin-managed writes until a real workflow needs more structure
- simple code paths over framework magic

A practical summary:

> use Django for delivery speed, but keep business structure explicit

This means:

- views should stay thin
- queries should live in selectors when they are real reads
- write flows should become explicit actions/use cases when they matter
- domain rules should be expressed in small policies/value objects/errors where useful
- historical order data should be snapshotted, not lazily derived from current catalog state

---

## System overview

The project is split into a handful of focused apps:

- `pages`
- `partner_request`
- `accounts`
- `catalog`
- `ordering`

Each app owns a small, understandable part of the system.

### `pages`
Thin public content pages.

Examples:
- homepage
- about
- contact

No business logic, no models, no persistence.

### `partner_request`
Public inbound app for store interest requests.

Purpose:
- accept a simple partner request from a store
- store it safely
- let admin review and mark it handled

It is intentionally **not** an onboarding engine and does not create users or stores.

### `accounts`
Owns the internal `Store` entity and store-facing access.

Purpose:
- connect Django `User` to internal store identity
- provide store portal access
- provide public store locator data

The name `accounts` is historical; in practice the app also owns the `Store` concept.

### `catalog`
Owns current product truth.

Purpose:
- manage products, categories, and tags
- decide which products are visible
- decide which products are orderable
- expose read selectors for catalog browsing and ordering

`catalog` represents **current** truth.

### `ordering`
Owns order placement and order history.

Purpose:
- parse order submissions
- validate ordering rules
- create orders and order-item snapshots
- expose order history and detail reads

`ordering` represents **historical** truth.

---

## Key boundaries

### Public request vs internal store truth

A partner interest request is not the same thing as a store.

- `partner_request` stores public, external, potentially messy inbound data
- `accounts.Store` is internal, trusted system truth

These must remain separate.

### Current catalog truth vs historical order truth

The catalog may change over time:

- names can change
- visibility can change
- orderability can change
- categories or metadata can change

Orders must not change retroactively.

Therefore:

- `catalog` owns live product data
- `ordering` snapshots business-relevant product data into `OrderItem`

This is one of the most important design rules in the project.

### Authentication vs business identity

Django `User` is used for authentication.
`Store` is used for business identity inside the system.

For the current MVP, each store maps to exactly one user:

- one store
- one login
- one ordering identity

This is a deliberate simplification for the current business situation, not a universal domain truth.

---

## Current business assumptions

The current business is small and operationally simple:

- only a few partner stores
- one responsible manager per store
- store orders are currently replaced from SMS to web
- products include both loose candy and packaged products like chips

This has influenced several design decisions:

### One user per store
A one-to-one relation between `User` and `Store` is enough for now.

### Admin-managed store creation
Stores and users are created manually in admin.

### Public partner requests are passive
A partner request is just a lead/inbox entry, not a provisioning workflow.

### Product metadata is mixed and partially optional
Different product families need different metadata:

- loose candy: weight may matter more
- chips: units per box may matter more

The schema therefore stays permissive and descriptive.

---

## App interaction map

A simplified view of how the apps depend on each other:

- `pages`
  - links to `accounts`, `catalog`, `partner_request`

- `partner_request`
  - independent inbound boundary
  - no coupling to `Store` provisioning

- `accounts`
  - owns `Store`
  - partner portal entrypoint
  - public store locator

- `catalog`
  - owns current product truth
  - exposes selectors for visible/orderable products

- `ordering`
  - depends on `Store`
  - reads current products from `catalog`
  - creates stable historical snapshots

The important dependency direction is:

- `ordering` may read from `catalog`
- `catalog` must not know about orders

---

## Read/write structure

Not every app needs the same internal architecture.

This project uses deeper structure only where it pays off.

### Apps that stay simple
- `pages`
- `partner_request`

These apps are mostly straightforward HTTP + template or form handling.

### Apps with light read structure
- `accounts`
- `catalog`

These apps benefit from `read/selectors.py` because they expose meaningful query surfaces:
- public store locator
- catalog reads
- orderable product lists

### App with explicit read/write/domain structure
- `ordering`

This app is the most business-critical and therefore benefits from explicit layers:

- `read/selectors.py`
- `write/parsing.py`
- `write/commands.py`
- `write/actions.py`
- `domain/errors.py`
- `domain/policies.py`
- `domain/value_objects.py`

The point is not architectural ceremony.
The point is to make the order flow explicit and stable.

---

## Why not use Django models for all business logic?

Django models are useful persistence objects, but not every business workflow fits naturally
inside model methods.

This project prefers:

- model methods for small, local behavior
- selectors for reads
- explicit write functions for multi-step workflows
- value objects and policies for small invariants

This avoids turning models into “god objects” while still keeping the system lightweight.

---

## Routing philosophy

The root URL configuration is intentionally small and direct.

The site has a few clear route groups:

- public pages
- public catalog
- public partner request
- store portal
- order pages
- admin
- auth

The goal is that URL ownership remains obvious without introducing unnecessary indirection.

---

## Templates philosophy

Templates are server-rendered and intentionally simple.

They should:

- present data clearly
- avoid embedding business rules
- rely on selectors / views to provide already-shaped data
- remain understandable without tracing hidden context builders

The project prefers readability over clever templating.

---

## Admin philosophy

Django admin is used as the operational back office.

Current admin responsibilities include:

- product maintenance
- category/tag maintenance
- store maintenance
- partner request review
- order inspection / maintenance

The current principle is:

> use admin until a real dedicated workflow is justified

This keeps the MVP small and practical.

---

## Important invariants across the system

### Orders must remain historically stable
Order items snapshot product data.

### Inactive stores must not place orders
Protected both near the request boundary and inside the write path.

### Orders must contain at least one line
Empty orders are invalid.

### Box counts must be sensible
Ordering counts are expressed in boxes, not units, and are validated explicitly.

### Public inbound requests must not create internal entities automatically
`partner_request` is an inbox, not a provisioning engine.

### Current visibility and current orderability are different concerns
`catalog.Product` models them separately.

---

## Current simplifications (intentional MVP decisions)

These are not accidents; they are deliberate:

- one `User` per `Store`
- manual store/user creation in admin
- no custom user model
- no separate membership model yet
- no catalog write use-case layer yet
- no advanced order status workflow yet
- no dedicated geographic/location app yet
- no pricing model in catalog yet
- no asynchronous/background processing

These choices are acceptable because they match the actual current business complexity.

---

## Likely future evolutions

The design leaves room for these later changes:

### `accounts`
- multiple users per store via a membership model

### `catalog`
- richer visibility/orderability rules
- import/sync workflows
- richer filtering via tags

### `ordering`
- explicit status transitions
- admin fulfillment workflow
- exports / internal reporting
- ordering by product code as a faster input mode

### public store locator
- embedded map
- coordinates / pins
- public-listing-specific fields
- possibly a dedicated app later if that concern grows

### partner onboarding
- more structured contact/review workflow if volume increases

---

## Testing philosophy

Tests should focus first on business-critical seams, not just coverage for its own sake.

Highest-value tests:

- order placement action
- order form parsing
- catalog orderable/visible selectors
- partner request form normalization/validation
- access rules around store portal / order pages

The main goal is to protect invariants and boundaries.

---

## Summary

This project uses Django pragmatically:

- fast delivery through built-in framework features
- explicit structure where business logic becomes important
- stable boundaries between apps
- clear distinction between current truth and historical truth

In one sentence:

> SwedeSweets is a Django MVP with explicit domain boundaries, simple operational workflows, and stable order history.

# SwedeSweets Backend — System Design
## Purpose
This project is a Django-based MVP for a B2B web application used by a small company
that imports Swedish sweets to France and delivers to retail stores.

The system has three main surfaces:

- a **public marketing/catalog surface**
- a **store portal** for authenticated partner stores to place orders and view order history
- a **staff portal** for internal users to monitor operational work, manage accounts, and access deeper maintenance tools when needed

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
- simple code paths over framework magic
- lightweight operational workflows before building custom backoffice systems

A practical summary:

> use Django for delivery speed, but keep business structure explicit

This means:

- views should stay thin
- selectors should own meaningful reads
- multi-step workflows should become explicit actions/use cases
- domain rules should be expressed in small, named concepts where useful
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

Thin public content pages such as:

- homepage
- about
- contact

No business logic, no models, no persistence.

### `partner_request`

Public inbound app for store interest requests.

Purpose:

- accept a simple partner request from a store
- store it safely
- let internal users review and mark it handled

It is intentionally **not** an onboarding engine and does not create users or stores.

### `accounts`

Owns internal account identity and authenticated entry surfaces.

Purpose:

- connect Django `User` to business identity
- model partner stores through `Store`
- model internal staff through `StaffAccount`
- distinguish between store users, restricted staff, and full staff
- expose a smart authenticated portal entrypoint
- provide public store locator data
- provide internal account provisioning flows

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

## User types and work surfaces

The project uses Django’s default `User` model for authentication, but business role is interpreted through the `accounts` app.

### Store user

A store user is linked to exactly one `Store`.

This user uses the **store portal** to:

- place orders
- view order history
- view order details

### Restricted staff user

A restricted staff user is linked to a `StaffAccount` with restricted access.

This user uses the **restricted staff portal** to:

- monitor open orders
- monitor incoming partner requests
- perform lightweight internal operational work

Restricted staff should work through the portal, not through Django admin.

### Full staff user

A full staff user is linked to a `StaffAccount` with full access.

This user uses the **full staff portal** to:

- monitor open orders
- monitor incoming partner requests
- create store and staff accounts
- access Django admin for deeper maintenance

### Admin access

Django admin access is now treated as an infrastructure concern, not the primary role model.

In practice:

- store users do not access admin
- restricted staff do not access admin
- full staff may access admin

---

## Portal model

Authenticated users do not all share the same destination.

### `/portal/`

This is a smart authenticated entrypoint.

It dispatches based on business role:

- store user -> store portal
- restricted staff -> restricted staff portal
- full staff -> full staff portal
- other authenticated user -> fallback page

### Store portal

Partner-facing workspace for stores.

### Restricted staff portal

Internal operational surface for limited staff work.

### Full staff portal

Internal operational surface for broader staff work, including provisioning and admin access.

### `/admin/`

Django admin remains the full maintenance surface for deeper editing and inspection.

This separation is deliberate:

- `/portal/` is the main business-facing work surface
- `/admin/` is the deeper maintenance surface

---

## Key boundaries

### Public request vs internal store truth

A partner interest request is not the same thing as a store.

- `partner_request` stores public inbound data
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

### Authentication vs business identity

Django `User` is used for authentication.

Business identity is expressed through:

- `Store` for partner stores
- `StaffAccount` for internal staff

### Store users vs staff users

Store users and staff users do different jobs and should not be forced through the same workflow.

This is why portal dispatch exists.

### Provisioning flow vs deep maintenance

Creating accounts is now an explicit internal workflow.

- `accounts.write` owns account provisioning
- Django admin remains available for deeper maintenance and correction

---

## Current business assumptions

The current business is small and operationally simple:

- only a few partner stores
- one responsible manager per store
- store orders are currently replaced from SMS to web
- products include both loose candy and packaged products like chips
- internal users mainly need lightweight operational visibility, not a full custom backoffice yet

This has influenced several design decisions.

### One user per store

A one-to-one relation between `User` and `Store` is enough for now.

### Internal staff-managed provisioning

Users and stores are created by internal staff through explicit internal flows.

### Public partner requests are passive

A partner request is a lead/inbox entry, not a provisioning workflow.

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
  - no coupling to store provisioning

- `accounts`
  - owns `Store`
  - owns `StaffAccount`
  - owns portal dispatch
  - exposes public store locator reads
  - owns internal account provisioning

- `catalog`
  - owns current product truth
  - exposes selectors for visible/orderable products

- `ordering`
  - depends on `Store`
  - reads current products from `catalog`
  - creates stable historical snapshots

Important dependency direction:

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

### Apps with light structure

- `catalog`

`catalog` benefits from:

- `read/selectors.py`
- small domain rules for visibility and orderability

### Apps with richer workflow structure

- `accounts`
- `ordering`

`accounts` now owns:

- role resolution
- portal dispatch
- public store locator reads
- staff/store account provisioning

`ordering` owns the most business-critical workflow and therefore benefits from explicit:

- reads
- parsing
- commands
- actions
- domain rules

The point is not ceremony.
The point is to make important flows explicit and stable.

---

## Why not use Django models for all business logic?

Django models are useful persistence objects, but not every business workflow fits naturally inside model methods.

This project prefers:

- model methods for small, local behavior
- selectors for reads
- explicit write functions for multi-step workflows
- authz helpers for role-based routing and access control
- forms for HTTP-boundary validation
- typed commands for workflow intent

This avoids turning models into “god objects” while still keeping the system lightweight.

---

## Routing philosophy

The root URL configuration is intentionally small and direct.

The site has a few clear route groups:

- public pages
- public catalog
- public partner request
- public store locator
- smart authenticated portal entrypoint
- store order pages
- staff provisioning pages
- admin
- auth

The goal is that URL ownership remains obvious without unnecessary indirection.

### Namespaced route ownership

Apps that expose named routes should own them under namespaces.

Examples:

- `accounts:portal`
- `accounts:store_list`
- `accounts:create_store_account`
- `partner_request:apply`
- `catalog:product_list`
- `ordering:order_create`

This keeps URL contracts explicit as the project grows.

---

## Templates philosophy

Templates are server-rendered and intentionally simple.

They should:

- present data clearly
- avoid embedding business rules
- rely on selectors and views to provide already-shaped data
- remain understandable without hidden context builders

The project prefers readability over clever templating.

### Template responsibility split

Authenticated templates are intentionally separated by user type:

- store portal
- restricted staff portal
- full staff portal
- fallback/no-access page
- account provisioning pages

This is preferable to one shared portal template full of role branches.

---

## Admin philosophy

Django admin is used as the technical back office.

Current admin responsibilities include:

- product maintenance
- category/tag maintenance
- store maintenance
- partner request review
- order inspection and maintenance

The current principle is:

> use admin for deep maintenance, but not for every daily workflow

So the current operational split is:

- **staff portal** for daily operational work and provisioning
- **Django admin** for deeper maintenance and editing

---

## Important invariants across the system

### Orders must remain historically stable

Order items snapshot product data.

### Inactive stores must not place orders

Protected both near the request boundary and inside the write path.

### Orders must contain at least one line

Empty orders are invalid.

### Box counts must be sensible

Ordering counts are expressed in boxes, not units.

### Public inbound requests must not create internal entities automatically

`partner_request` is an inbox, not a provisioning engine.

### Current visibility and current orderability are different concerns

`catalog.Product` models them separately.

### Portal landing must match business role

- store users belong in the store portal
- restricted staff belong in the restricted staff portal
- full staff belong in the full staff portal

### Store account creation must create a real `Store`

A store login without a linked `Store` is invalid.

### Staff account creation must create a real `StaffAccount`

Internal staff identity should not live only in Django flags.

### Provisioning should be atomic

The system must not leave behind half-created account structures.

---

## Current simplifications (intentional MVP decisions)

These are deliberate:

- one `User` per `Store`
- one `StaffAccount` per internal staff user
- no custom user model
- no separate membership model yet
- no store-side role model beyond one store user
- no catalog write use-case layer yet
- no advanced order status workflow yet
- no dedicated location app yet
- no pricing model in catalog yet
- no asynchronous/background processing

These choices are acceptable because they match the current business complexity.

---

## Likely future evolutions

### `accounts`

- richer operational actions for restricted staff
- richer distinction between full staff and super-admin
- multiple users per store via a membership model
- store-side roles if one store later needs more than one user
- richer permission modelling if internal roles grow

### `catalog`

- richer visibility/orderability rules
- import/sync workflows
- richer filtering via tags

### `ordering`

- explicit status transitions
- internal fulfillment workflow beyond simple status edits
- exports and reporting
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
- access rules around portal and order pages
- portal dispatch by user type
- store/staff account provisioning flow

The main goal is to protect invariants and boundaries.

---

## Summary

This project uses Django pragmatically:

- fast delivery through built-in framework features
- explicit structure where business logic becomes important
- stable boundaries between apps
- clear distinction between current truth and historical truth
- distinct operational surfaces for stores and internal staff
- explicit internal provisioning for store and staff accounts

In one sentence:

> SwedeSweets is a Django MVP with explicit domain boundaries, stable order history, and distinct operational surfaces for stores and internal staff.

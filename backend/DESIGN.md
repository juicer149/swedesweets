# SwedeSweets Backend — System Design
## Purpose
This project is a Django-based MVP for a B2B web application used by a small company
that imports Swedish sweets to France and delivers to retail stores.

The system has three main surfaces:

- a **public marketing/catalog surface**
- a **store portal** for authenticated partner stores to place orders and view order history
- a **staff portal** for internal users to monitor operational work such as open orders, partner requests, and account provisioning

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
- admin-backed operations until a dedicated workflow clearly becomes worth it

A practical summary:

> use Django for delivery speed, but keep business structure explicit

This means:

- views should stay thin
- queries should live in selectors when they are real reads
- write flows should become explicit actions/use cases when they matter
- domain rules should be expressed in small policies, value objects, errors, and enums where useful
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
- let internal users review and mark it handled

It is intentionally **not** an onboarding engine and does not create users or stores.

### `accounts`

Owns the internal `Store` entity and authenticated account-facing entry surfaces.

Purpose:

- connect Django `User` to internal store identity
- distinguish between store users and internal staff users
- expose a smart authenticated portal entrypoint
- provide store portal access
- provide staff portal access
- provide public store locator data
- provide an explicit internal account provisioning flow for store and staff accounts

The name `accounts` is historical; in practice the app also owns the `Store` concept,
authenticated user routing, and account provisioning.

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

The project currently uses Django’s default `User` model, but users are interpreted in two primary ways:

### Store user

A store user is:

- a normal Django user
- linked to exactly one `Store`
- not an internal staff account

This user uses the **store portal** to:

- place orders
- view order history
- view order details

### Staff user

A staff user is:

- an internal Django user
- `is_staff=True`
- not required to be linked to a `Store`

This user uses the **staff portal** to:

- monitor open orders
- monitor unprocessed partner requests
- create store and staff accounts through the internal provisioning flow
- jump into Django admin for deeper maintenance

### Admin user

An admin user is a staff user with broader privileges, typically:

- `is_staff=True`
- `is_superuser=True`

Admins use Django admin for full system configuration and maintenance.

### Important distinction

These are different operational roles:

- store users perform external partner work
- staff users perform internal operational work
- admin users perform internal technical/system work

The current system does **not** yet model these as separate custom user classes.
Instead, it uses:

- `Store` linkage for store identity
- Django `is_staff` / `is_superuser` flags for internal access

---

## Portal model

Authenticated users do not all share the same destination anymore.

### `/portal/`

This is now a **smart authenticated entrypoint**.

It dispatches based on user type:

- store user -> store portal
- staff user -> staff portal
- other authenticated user -> fallback page

### Store portal

The store portal is the partner-facing workspace.

Responsibilities:

- show store-facing overview data
- link to order creation
- link to order history

### Staff portal

The staff portal is a lightweight internal operational surface.

Responsibilities:

- show recent open orders
- show recent unprocessed partner requests
- provide entrypoints into account provisioning
- act as a simpler operational landing page than full Django admin

### `/admin/`

Django admin remains the full system administration surface.

Responsibilities:

- product maintenance
- category/tag maintenance
- store maintenance
- partner request review
- order inspection / maintenance

This separation is deliberate:

- `/portal/` is a user-facing business entrypoint
- `/admin/` is a full system maintenance surface

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

### Store users vs staff users

Store users and staff users are not just permission variants of the same workflow.

They do different jobs and should have different surfaces:

- store users should not be forced through internal operational pages
- staff users should not land in store-only pages such as "No store connected"

This is why portal dispatch exists.

### Provisioning flow vs model maintenance

Creating accounts is now treated as an explicit internal workflow, not just a manual admin habit.

- `accounts.write` owns account provisioning use cases
- Django admin still owns deep maintenance and correction work

This keeps account creation explicit without forcing all operational work into admin.

---

## Current business assumptions

The current business is small and operationally simple:

- only a few partner stores
- one responsible manager per store
- store orders are currently replaced from SMS to web
- products include both loose candy and packaged products like chips
- internal users mainly need lightweight operational visibility, not a full custom backoffice yet

This has influenced several design decisions:

### One user per store

A one-to-one relation between `User` and `Store` is enough for now.

### Internal staff-managed provisioning

Users and stores are created by internal staff through explicit internal flows.

Django admin is still available for deeper maintenance and correction, but is no longer the only provisioning path.

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
  - owns portal dispatch
  - owns store portal and staff portal entry surfaces
  - exposes public store locator reads
  - owns explicit staff-driven account provisioning

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

### Apps with light structure

- `catalog`

#### `catalog`

- `read/selectors.py` for browsing and orderable product reads
- small domain rules for product visibility/orderability

### Apps with explicit read/authz/provisioning structure

- `accounts`

`accounts` now benefits from a slightly richer internal structure because it owns:

- user-type checks
- portal dispatch
- public store locator reads
- store portal reads
- staff portal reads
- internal account provisioning

Current internal structure includes:

- `authz.py` for account-type checks and access helpers
- `read/selectors.py` for public store locator and portal read models
- `forms.py` for account provisioning HTTP input
- `domain/` for account-type language and provisioning errors
- `write/` for explicit account creation commands, dispatch, and actions

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
- authz helpers for user-type routing and access control
- forms for HTTP input validation
- typed commands for explicit workflow intent

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

The goal is that URL ownership remains obvious without introducing unnecessary indirection.

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
- rely on selectors / views to provide already-shaped data
- remain understandable without tracing hidden context builders

The project prefers readability over clever templating.

### Template responsibility split

Authenticated templates are intentionally separated by user type and workflow:

- `accounts/store_portal.html`
- `accounts/staff_portal.html`
- `accounts/no_store_connected.html`
- `accounts/account_create_choice.html`
- `accounts/create_store_account.html`
- `accounts/create_staff_account.html`

This is preferable to one shared portal template full of role branches or one giant provisioning template full of account-type conditionals.

---

## Admin philosophy

Django admin is used as the operational and technical back office.

Current admin responsibilities include:

- product maintenance
- category/tag maintenance
- store maintenance
- partner request review
- order inspection / maintenance

The current principle is:

> use admin until a real dedicated workflow is justified

However, the project now also acknowledges that some internal daily work is better served by a lighter portal than by full Django admin. That is the reason the staff portal exists.

So the current operational split is:

- **staff portal** for lightweight operational overview and account provisioning
- **Django admin** for full maintenance and deep editing

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

### Store users and staff users should land in different work surfaces

Store users belong in the store portal.
Staff users belong in the staff portal.

### A store account should not be treated as an internal staff account

This is an important conceptual boundary even though the current implementation still uses Django’s default `User`.

### Store account creation must create a real `Store`

A store login without a linked `Store` is invalid for the current business model.

### Store account creation should be atomic

The system must not leave behind a half-created user/store pair.

### Staff account creation should be explicit about internal access level

Internal staff provisioning should use explicit role semantics rather than ad-hoc flags spread through views.

---

## Current simplifications (intentional MVP decisions)

These are not accidents; they are deliberate:

- one `User` per `Store`
- no custom user model
- no separate membership model yet
- no explicit internal role model beyond `is_staff` / `is_superuser`
- no store-side role model beyond one store user
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

- richer distinction between restricted staff and full staff/admin
- create store account and redirect into richer follow-up flows
- possibly multiple users per store via a membership model
- store-side roles if one store later needs more than one user
- richer permission modelling beyond Django’s current flags

### `catalog`

- richer visibility/orderability rules
- import/sync workflows
- richer filtering via tags

### `ordering`

- explicit status transitions
- internal fulfillment workflow beyond simple status edits
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
- access rules around store portal / staff portal / order pages
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
- separate work surfaces for store users and internal staff users
- explicit internal provisioning for store and staff accounts

In one sentence:

> SwedeSweets is a Django MVP with explicit domain boundaries, stable order history, and distinct operational surfaces for stores and internal staff.

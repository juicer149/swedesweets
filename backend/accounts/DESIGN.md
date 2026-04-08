# accounts
`accounts` owns the internal `Store` entity, the internal `StaffAccount` entity,
and the authenticated entry surfaces built around business role.

## Purpose

This app connects Django authentication to the business idea of:

- a store account
- an internal restricted staff account
- an internal full staff account

These actors do different work and should not be forced through the same portal UI.

---

## Current user model

The project uses Django’s default `User` model for authentication.

Business identity is then built on top of `User` through:

- `Store`
- `StaffAccount`

This is an important design distinction:

- Django `User` handles authentication
- `accounts` models the business meaning of that authenticated user

### Store user

A store user is:

- a normal Django user
- linked to exactly one `Store`
- not an internal staff account
- not allowed into Django admin

A store user uses the store portal to:

- place orders
- view order history
- view order details

### Restricted staff user

A restricted staff user is:

- an internal Django user
- linked to a `StaffAccount`
- `StaffAccount.access_level = restricted`
- not linked to a `Store`
- not allowed into Django admin

A restricted staff user uses the restricted staff portal to:

- monitor open orders
- monitor incoming partner requests
- perform lightweight internal operational work

Restricted staff should work through the portal, not through Django admin.

### Full staff user

A full staff user is:

- an internal Django user
- linked to a `StaffAccount`
- `StaffAccount.access_level = full`
- not linked to a `Store`
- allowed into Django admin

A full staff user uses the full staff portal to:

- monitor open orders
- monitor incoming partner requests
- create store accounts
- create staff accounts
- use operational shortcuts
- jump into Django admin for deeper maintenance

### Admin user

In the current system, a full staff user may also be an admin user through Django’s built-in flags:

- `is_staff=True`
- often `is_superuser=True`

That is an infrastructure concern, not the primary business model.

The important business distinction is:

- store
- restricted staff
- full staff

---

## Key design rule

Store accounts, restricted staff accounts, and full staff accounts are different actors.

They should have:

- different responsibilities
- different portal surfaces
- different operational flows
- different admin access rules

A store account should never be treated as an internal staff account.
A restricted staff account should never be treated as a full admin-capable staff account.

---

## Responsibilities

This app is responsible for:

- modelling `Store`
- modelling `StaffAccount`
- linking business identity to Django `User`
- exposing the public store locator
- dispatching authenticated users to the correct portal
- exposing read selectors for store and staff portal overviews
- provisioning new store and staff accounts through an explicit internal workflow
- expressing internal account-role semantics

---

## Non-responsibilities

This app is not responsible for:

- public partner request intake (`partner_request`)
- product truth (`catalog`)
- order write logic (`ordering`)
- full system administration (`/admin/`)
- fulfillment/domain rules for order transitions

---

## Portal model

### `/portal/`

Smart entrypoint after login.

It dispatches users based on business role:

- store user -> store portal
- restricted staff user -> restricted staff portal
- full staff user -> full staff portal
- unknown authenticated user -> fallback page

### Store portal

Dedicated surface for external partner stores.

### Restricted staff portal

Dedicated surface for internal operational work without admin access.

This portal should stay focused and limited.

### Full staff portal

Dedicated surface for internal operational work plus provisioning and deeper access.

This portal may link to `/admin/` and account-creation flows.

### `/admin/`

Remains the full system administration surface, separate from the business-facing portals.

In the current system:

- full staff may access admin
- restricted staff should not
- store users should not

---

## Public store locator

The app also exposes a public "Find sweets" page based on active stores with usable addresses.

This is a read concern and lives in `read/selectors.py`.

---

## Internal structure

### `models.py`

Owns:

- `Store`
- `StaffAccount`

`Store` expresses external partner identity.
`StaffAccount` expresses internal business role for staff users.

### `authz.py`

Helpers for:

- resolving business role from authenticated user
- protecting store-only pages
- protecting restricted/full staff pages
- keeping portal dispatch explicit

### `read/selectors.py`

Read selectors for:

- public store locator
- store portal snapshot
- staff portal overview

### `domain/`

Small domain language for role semantics and provisioning errors.

Current contents include:

- `roles.py`
- `errors.py`

This layer exists to make account-role language explicit.

Important concepts include:

- `StaffAccessLevel`
- `AccountRole`
- role specs / role dispatch data
- invalid account identity errors

### `write/`

Explicit account provisioning workflow.

Current contents include:

- `commands.py`
- `actions.py`
- `dispatch.py`

This layer exists because account creation is now a real multi-step use case.

### `forms.py`

HTTP-boundary validation for internal account creation.

Forms validate raw input and convert it into typed commands.

### `views.py`

HTTP adapters for:

- public store list
- smart portal dispatch
- store portal
- restricted staff portal
- full staff portal
- account creation flows

---

## Account creation pipeline

The internal provisioning flow follows a small explicit pipeline:

`account kind -> form -> command -> dispatch -> action`

This keeps concerns separated:

- forms validate HTTP input
- commands describe intent
- dispatch selects the right handler
- actions perform model creation

This avoids burying multi-step provisioning logic directly inside views or model methods.

---

## Role model and dispatch

The app now uses explicit business role semantics rather than relying only on Django flags.

### Why this exists

Django flags such as:

- `is_staff`
- `is_superuser`

are infrastructure-level flags.

They are useful for Django admin, but they are not expressive enough for the business distinction between:

- restricted staff
- full staff
- store users

### Business roles

The app therefore works with explicit business roles such as:

- `store`
- `restricted_staff`
- `full_staff`

These roles drive:

- portal routing
- template selection
- capabilities
- account provisioning behavior

### Central role specification

Role behavior is described centrally rather than being scattered across many if-statements.

This keeps role semantics easier to read and evolve.

The goal is not abstract cleverness.
The goal is to keep role behavior explicit, centralized, and stable.

---

## Why `StaffAccount` exists

Earlier versions of the app treated internal staff mostly through Django’s built-in flags.

That turned out to be insufficient because restricted staff and full staff are different actors:

- restricted staff should use the portal only
- full staff may also use Django admin

If role meaning lived only in `is_staff`, the system could not cleanly represent that distinction.

`StaffAccount` solves this by making internal staff identity a real business concept.

This lets the app express:

- who is internal staff
- what access level they have
- how portal dispatch should behave

without overloading Django’s admin flags.

---

## Why `domain/` and `write/` now exist

Earlier versions of the app could stay simpler because provisioning was fully manual.

Now there is a real internal workflow for creating:

- store accounts
- restricted staff accounts
- full staff accounts

That justifies:

- a small domain language
- explicit commands
- explicit actions
- explicit dispatch

The goal is not abstraction for its own sake.
The goal is to make account provisioning readable, stable, and easy to evolve.

---

## Current simplifications

The system intentionally keeps these assumptions for now:

- one store account per store
- one Django `User` model
- one `Store` per store user
- one `StaffAccount` per internal staff user
- full staff admin access still mapped partly through Django flags
- store/staff creation is still a small internal workflow
- no custom user model
- no separate membership model yet
- no store-side role model yet

These are acceptable for the current business size.

---

## Important invariants inside this app

### A store account must create both a `User` and a linked `Store`

A store login without a real `Store` identity is invalid for the current model.

### A staff account must create a `StaffAccount`

Internal staff identity should not exist only implicitly through Django flags.

### A user must not have two business identities

A Django `User` may represent exactly one business identity in this system:

- `Store`
- `StaffAccount`
- or no configured business identity yet

A user must never be linked to both `Store` and `StaffAccount`.

If that invalid state appears, role resolution should fail loudly rather than
silently choosing one identity.

### Restricted staff and full staff are different roles

They should not be treated as the same account type with slightly different templates.

### Portal dispatch must reflect business role

- store users belong in the store portal
- restricted staff belong in the restricted staff portal
- full staff belong in the full staff portal

### Restricted staff should not require Django admin access

Restricted staff should work through the portal.

### Store creation should be atomic

The system must not leave behind a half-created user/store pair.

### Staff creation should be atomic

The system must not leave behind a half-created user/staff-account pair.

---

## Likely next evolution

Possible future extensions:

- fuller operational actions for restricted staff
- richer distinction between full staff and super-admin
- multiple users per store via a membership model
- a dedicated store-role model if store-side permissions become richer
- redirects from account creation to created-object detail views
- tighter integration between staff portal and provisioning flows
- a richer capability model if internal roles become more complex

---

## Summary

`accounts` is the app that connects:

- authentication
- store identity
- staff identity
- portal routing
- public store discovery
- explicit account provisioning

In one sentence:

> `accounts` owns who the authenticated actor is, what business identity they represent, where they should land, and how new store and staff accounts are provisioned.

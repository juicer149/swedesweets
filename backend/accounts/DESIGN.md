# accounts
`accounts` owns the internal `Store` entity and the authenticated entry surfaces
built around user type.

## Purpose

This app connects Django authentication to the business idea of a store account
and an internal staff account.

In the current system there are two main authenticated user types:

- **store users**
- **staff users**

These users do different work and should not be forced through the same portal UI.

---

## Current user model

The project currently uses Django’s default `User` model.

### Store user

A store user is:

- a normal Django user
- linked to exactly one `Store`
- not a staff/admin account

A store user uses the store portal to:

- place orders
- view order history
- view order details

### Staff user

A staff user is:

- an internal Django user
- `is_staff=True`
- not required to be linked to a `Store`

A staff user uses the staff portal to:

- monitor open orders
- review incoming partner requests
- access operational shortcuts
- create store and staff accounts through the internal provisioning flow

### Admin user

An admin user is a staff user with broader privileges, often:

- `is_staff=True`
- `is_superuser=True`

Admins may use Django admin for full system management.

---

## Key design rule

Store accounts and staff accounts are different kinds of actors.

They should have:

- different responsibilities
- different portal surfaces
- different operational flows

A store account should never be treated as an internal admin/staff account.

---

## Responsibilities

This app is responsible for:

- modelling `Store`
- linking store identity to Django `User`
- exposing the public store locator
- dispatching authenticated users to the correct portal
- exposing minimal read selectors for store and staff portal overviews
- provisioning new store and staff accounts through an explicit internal workflow

---

## Non-responsibilities

This app is not responsible for:

- public partner request intake (`partner_request`)
- product truth (`catalog`)
- order write logic (`ordering`)
- full system administration (`/admin/`)

---

## Portal model

### `/portal/`

Smart entrypoint after login.

It dispatches users based on account type:

- store user -> store portal
- staff user -> staff portal

### Store portal

Dedicated surface for external partner stores.

### Staff portal

Dedicated surface for internal operational work.

### `/admin/`

Remains the system administration surface, separate from the business-facing portals.

---

## Public store locator

The app also exposes a public "Find sweets" page based on active stores with
usable addresses.

This is a read concern and lives in `read/selectors.py`.

---

## Internal structure

### `models.py`

Owns `Store`.

### `authz.py`

Helpers for identifying user type and protecting staff/store-only views.

### `read/selectors.py`

Read selectors for:

- public store locator
- store portal snapshot
- staff portal overview

### `domain/`

Small domain language for account provisioning and role semantics.

Current contents include:

- `roles.py`
- `errors.py`

This keeps account-type language explicit without overbuilding a full domain layer.

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
- staff portal
- account creation flows

---

## Account creation pipeline

The internal provisioning flow follows a small explicit pipeline:

`account type -> form -> command -> dispatch -> action`

This keeps concerns separated:

- forms validate HTTP input
- commands describe intent
- dispatch selects the right handler
- actions perform model creation

This avoids burying multi-step provisioning logic directly inside views or model methods.

---

## Why `domain/` and `write/` now exist

Earlier versions of the app could stay simpler because provisioning was fully manual.

Now there is a real internal workflow for creating:

- store accounts
- staff accounts

That justifies:

- a small domain language (`AccountType`, `StaffAccessLevel`)
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
- staff/admin distinction still handled through Django staff/superuser flags
- store/staff creation still relatively small and staff-operated
- no custom user model
- no separate membership model yet

These are acceptable for the current business size.

---

## Important invariants inside this app

### A store account must create both a `User` and a linked `Store`

A store login without a real `Store` identity is invalid for the current model.

### A store account must not be a staff account

Store users and staff users represent different actors.

### A staff account must be internal

Staff users are not required to have a `Store`.

### Portal dispatch must reflect account type

Store users belong in the store portal.
Staff users belong in the staff portal.

### Store creation should be atomic

The system must not leave behind a half-created user/store pair.

---

## Likely next evolution

Possible future extensions:

- richer distinction between staff/admin beyond current Django flags
- multiple users per store via a membership model
- a dedicated store-role model if store-side permissions become richer
- redirects from account creation to created-object detail views
- tighter integration between staff portal and provisioning flows

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

> `accounts` owns who the authenticated actor is, what business identity they represent, where they should land, and how new internal/store accounts are provisioned.

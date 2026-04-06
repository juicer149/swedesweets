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
- protecting store-only and staff-only views through small authz helpers

---

## Non-responsibilities

This app is not responsible for:

- public partner request intake (`partner_request`)
- product truth (`catalog`)
- order write logic (`ordering`)
- full system administration (`/admin/`)

`accounts` decides **who the authenticated actor is and where they should land**.
It does not own the deeper business workflows of catalog management or order writing.

---

## Portal model

### `/portal/`

Smart entrypoint after login.

It dispatches users based on account type:

- store user -> store portal
- staff user -> staff portal

If an authenticated user is neither a store user nor a staff user,
the app currently renders a fallback page.

### Store portal

Dedicated surface for external partner stores.

Responsibilities:

- show store-facing overview data
- link into ordering flows
- act as the normal authenticated home for store accounts

### Staff portal

Dedicated surface for internal operational work.

Responsibilities:

- show open orders
- show unprocessed partner requests
- provide a lighter operational surface than full Django admin

### `/admin/`

Remains the system administration surface, separate from the business-facing portals.

This split is intentional:

- `/portal/` is the authenticated business entrypoint
- `/admin/` is the technical / maintenance surface

---

## Public store locator

The app also exposes a public "Find sweets" page based on active stores with
usable addresses.

This is a read concern and lives in `read/selectors.py`.

The locator is currently simple:

- only active stores are shown
- a store must have a usable address
- the result is shaped for presentation

This is intentionally lightweight, but leaves room for future map/pin/location work.

---

## Internal structure

### `models.py`

Owns `Store`.

The `Store` model is internal, trusted system truth for a retail partner that is
allowed to act in the system.

### `authz.py`

Helpers for identifying user type and protecting staff/store-only views.

Examples:

- `is_store_user(user)`
- `is_staff_user(user)`
- `require_store_user(request)`
- `require_staff_user(request)`

These helpers keep access intent explicit and avoid scattering the same checks
through multiple views.

### `read/selectors.py`

Read selectors for:

- public store locator
- store portal snapshot
- staff portal overview

This keeps query logic out of views when the read has meaning of its own.

### `views.py`

HTTP adapters for:

- public store list
- smart portal dispatch
- store portal
- staff portal

Views in this app should stay thin and should not absorb deeper business rules
from other apps.

---

## Why there is no `write/` yet

Account creation and provisioning are still admin-managed.

A future `write/` package becomes justified when the project introduces an
explicit internal flow for creating:

- store accounts
- staff accounts

At that point it would make sense to model use cases such as:

- `create_store_account`
- `create_staff_account`

Right now that would be premature structure, because the workflow still lives in
manual admin operations.

---

## Relationship to Django admin

The current provisioning path is still:

1. create a Django `User`
2. if it is a store account, create a linked `Store`
3. if it is an internal account, mark it as staff as needed

This is workable for the current MVP, but is also one of the clearest current
friction points in the system.

That friction is a good signal for future improvement, not a reason to overbuild early.

---

## Current simplifications

The system intentionally keeps these assumptions for now:

- one store account per store
- one Django `User` model
- staff/admin distinction still handled through Django staff/superuser flags
- account provisioning still done manually
- no custom user model
- no explicit internal role model beyond store-vs-staff

These are acceptable for the current business size.

---

## Important invariants inside this app

### A store user must be linked to a `Store`

The store portal assumes a real business identity, not just an authenticated user.

### A staff user does not need a `Store`

Internal users are not partner stores and should not be forced through store-only flows.

### Store users and staff users should land in different work surfaces

This is now enforced by portal dispatch.

### Public store listing is a read concern, not a domain mutation concern

The locator should not contain hidden side effects or provisioning logic.

---

## Likely next evolution

The next likely step is a small internal account-creation flow where staff can
choose whether a new account is:

- a store account
- a staff account

and the system creates the correct linked objects and flags explicitly.

That would likely justify adding a `write/` package with explicit use cases.

Other plausible future changes:

- a clearer distinction between staff and admin
- richer store/account lifecycle handling
- more than one user per store via a membership model
- a dedicated location/store-locator concern if mapping becomes significant

---

## Summary

`accounts` is no longer just a place to hold `Store`.

It is the app that connects:

- authentication
- store identity
- staff identity
- portal routing
- public store discovery

In one sentence:

> `accounts` owns who the authenticated actor is, what business identity they represent, and which portal surface they should enter.

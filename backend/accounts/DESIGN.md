# accounts
`accounts` is responsible for the store as an internal trusted entity and for the access layer built around it.

## Purpose

The app connects Django’s user system to the business concept of a store.

In the current MVP, each store is represented by a single account. This reflects the actual business context: a small number of stores, where each store in practice has one responsible person placing orders.

The app also provides a public read-only page for "Find sweets", where visitors can discover stores that sell SwedeSweets products.

## Responsibilities

The app is responsible for:

- modeling `Store` as an internal, trusted business entity
- linking `Store` to `User`
- exposing the partner portal for authenticated users
- exposing a public store locator for visitors
- keeping read logic for store views in selectors

## Non-responsibilities

The app is not responsible for:

- receiving public partner inquiries (`partner_request`)
- handling write flows in the order domain (`ordering`)
- modeling the product catalog (`catalog`)

## Design Principles

### 1. `Store` is internal truth
`Store` is the system’s trusted representation of a retail partner.  
It should not be confused with public lead data from `partner_request`.

### 2. One account per store is a deliberate MVP simplification
The current business does not require multiple users per store.  
For that reason, a one-to-one relationship is used between `Store` and `User`.

If this need changes later, it can be replaced with a membership-based model.

### 3. The public locator is a read model
The "Find sweets" page is a public read surface.  
Its rules belong in selectors, not scattered directly across views or templates.

### 4. The portal is an access surface, not the order domain
`accounts` renders the portal and connects the authenticated user to the correct store.  
The actual ordering logic belongs in `ordering`.

## Current Structure

- `models.py`
  - `Store`

- `views.py`
  - `store_list()` for the public store locator
  - `portal()` for the authenticated partner portal

- `read/selectors.py`
  - read selectors for public store views

- `admin.py`
  - manual internal store management

## Future Direction

If the store locator grows to include things like:

- coordinates
- map pins
- embedded map
- special rules for public visibility

then the public locator portion could be split into its own app.

Until then, it is reasonable for it to live here, since it still revolves around the same central entity: `Store`.

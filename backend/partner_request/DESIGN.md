# Partner Request Module

## Purpose

The `partner_request` module handles inbound interest from potential retail partners.

It acts as the **entry point into the B2B system**, before accounts and ordering.

This module is intentionally simple:
- Accept data from external users (stores)
- Persist requests
- Allow internal review and approval

It does NOT:
- Authenticate users
- Create accounts automatically
- Handle ordering logic

---

## Conceptual Model

A `PartnerRequest` represents:

> "A store expressing interest in becoming a customer"

It is a **temporary, pre-account state**.

Lifecycle:

```

NEW → processed → (converted to Store)

```

---

## Design Principles

### 1. Separation of Concerns

- `partner_request` handles **inbound interest only**
- `accounts` handles **actual customers (Store)**
- `ordering` handles **business operations**

This avoids:
- premature coupling
- complex flows in a single module

---

### 2. Explicit State

We use:

```python
is_processed = BooleanField(default=False)
```

instead of deleting or mutating records.

Why:

* preserves history
* enables audit trail
* keeps logic simple

---

### 3. Write-Optimized Model

This model is:

* append-heavy (many inserts)
* rarely updated

Therefore:

* simple fields
* no foreign keys
* no heavy constraints

---

### 4. Human-in-the-loop

Approval is manual (via admin).

Why:

* early stage product
* avoids premature automation
* supports flexible business decisions

---

## Data Model

```python
PartnerRequest:
    name            # contact person
    store_name      # business identity
    email
    phone
    address
    message
    created_at
    is_processed
```

### Notes

* `address` is required → needed for logistics feasibility
* `phone` is optional → not always provided
* `message` is optional → marketing/context

---

## Request Flow

### 1. User submits form

```
POST /apply/
```

### 2. View layer

* extracts POST data
* creates `PartnerRequest`

### 3. Database

* row inserted via Django ORM

### 4. Redirect

```
→ /thanks/
```

---

## Admin Workflow

Admin reviews requests via Django admin:

* filter by `is_processed`
* inspect request
* contact store manually

Future step:

* create `Store` from request

---

## Future Extensions

### 1. Approval Action

Admin action:

```
Approve → create Store → mark processed
```

---

### 2. Email Integration

* confirmation email (user)
* notification email (internal)

---

### 3. Validation Layer

* basic form validation (Django Forms)
* email/phone normalization

---

### 4. Geo / Logistics

* distance filtering
* delivery feasibility

---

### 5. CRM-lite features

* tagging requests
* status beyond boolean (e.g. contacted, rejected)

---

## Why Separate App?

Even though it is small, `partner_request` is its own app because:

* distinct domain boundary
* different lifecycle than accounts
* easier to evolve independently

---

## Philosophy

This module follows:

> "Start simple, keep boundaries clear, evolve when needed."

It is intentionally minimal:

* no abstractions
* no premature patterns
* no hidden magic

---

## Summary

`partner_request` is:

* the first touchpoint for new customers
* a write-focused, simple system
* a bridge between marketing and operations

It will grow only when real needs appear.

# Partner Request Module

## Purpose

The `partner_request` module handles inbound interest from potential retail partners.

It acts as the **entry point into the B2B system**, before accounts and ordering.

This module is intentionally simple:

- Accept data from external users (stores)
- Persist requests
- Allow internal review and decision

It does NOT:

- Authenticate users
- Automatically create accounts
- Handle ordering logic

---

## Conceptual Model

A `PartnerRequest` represents:

> "A store expressing interest in becoming a customer"

It is a **temporary, pre-account state** at the boundary of the system.

External input is:

- incomplete
- untrusted
- inconsistent

This module captures that safely before entering the core system.

---

## Lifecycle

```

PENDING → APPROVED → (creates User + Store)
PENDING → REJECTED

```

Key idea:

- A request is never mutated into a Store
- It is **converted** into internal entities

---

## Design Principles

### 1. Separation of Concerns

- `partner_request` handles **external input**
- `accounts` handles **internal customers (Store/User)**
- `ordering` handles **business operations**

This keeps boundaries clean and avoids coupling.

---

### 2. Explicit State (State Machine)

We use an explicit status field:

```python
status = ("pending", "approved", "rejected")
```

Why:

* avoids ambiguous boolean flags
* models real business decisions
* makes transitions explicit
* easy to extend later

---

### 3. Boundary Normalization

All emails are normalized:

```text
lowercase + trimmed
```

Why:

* email acts as identity
* prevents duplicate users due to casing differences
* ensures consistent lookups

---

### 4. Human-in-the-loop

Approval is manual (via Django admin).

Why:

* early stage product
* avoids premature automation
* allows flexible business decisions

---

### 5. Minimal Relationships

* No foreign keys during input phase
* Only after approval:

```text
PartnerRequest → created_store
```

Why:

* keeps write-path simple
* avoids premature coupling
* preserves audit trail

---

## Data Model

```python
PartnerRequest:
    name
    store_name
    email
    phone
    address
    message
    created_at
    status
    created_store   # set only if approved
```

### Notes

* Only `email` is required at submission time
* Other fields can be completed by admin
* `address` is required before approval
* `message` is optional, capped in size

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

* inspect incoming request
* complete missing data
* approve → creates User + Store
* reject → marks as rejected

Approval is explicit and safe:

* prevents duplicate users
* requires minimum valid data
* runs inside a transaction

---

## Conversion (Core Operation)

Approval performs:

```text
PartnerRequest → User + Store
```

Rules:

* email is normalized and used as username
* user must not already exist
* store is created and linked
* request is marked as approved

This is the **only place where external data becomes internal truth**.

---

## Deletion Policy

* Pending / rejected requests can be deleted
* Approved requests cannot be deleted

Why:

* approved requests created real system entities
* they are part of system history
* deleting them breaks traceability

---

## Future Extensions

* Email notifications (confirmation / internal alerts)
* Password setup flow (instead of temporary passwords)
* Extended status (e.g. contacted, on_hold)
* CRM features (tagging, notes)
* Geo / logistics validation

---

## Philosophy

> "Start simple, keep boundaries clear, evolve when needed."

This module is intentionally minimal:

* no signals
* no hidden logic
* no premature abstractions

---

## Summary

`partner_request` is:

* the system boundary for new customers
* a controlled entry into the domain
* a bridge between marketing and operations

It ensures that **only validated, explicit decisions create real accounts**.

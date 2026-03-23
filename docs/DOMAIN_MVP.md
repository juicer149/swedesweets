# Domain Scope (MVP v0.1)

This document defines the scope and boundaries of the SwedeSweets domain for version 0.1.

The goal is to replace an **unstructured SMS-based ordering workflow**
with a simple, structured, and reliable ordering process.

---

## 1. Core Problem

Stores currently place orders via SMS.

This results in:

- unclear structure
- manual interpretation
- risk of mistakes
- no consistent order format

The system replaces this with a structured domain model.

---

## 2. Domain Model (Included)

The MVP models only what is required to support ordering.

### Store

A customer (retail store) that places orders.

Only minimal information is modeled:

- identity (UUID)
- name

---

### Product

A product that can be ordered.

Design decision:

- Each product has a **user-facing code** (e.g. "42")
- This reflects how orders are communicated today

---

### Value Objects

Primitive values are replaced with explicit domain types.

#### ProductCode

- user-facing identifier
- must be a positive integer

#### Quantity

- represents number of units
- must be a positive integer

Design principle:

> Invalid states should be impossible to represent.

---

### OrderDraft

Represents an order in progress before submission.

Key characteristics:

- editable over time (returns new instances)
- supports incremental updates
- subject to business rules (e.g. cutoff time)

Concept:

- Draft = intent (what the store plans to order)
- Order = fact (what was submitted)

---

### Order

Represents a finalized order.

An order:

- belongs to a store
- has a timestamp
- contains one or more items
- is immutable

Orders are created from `OrderDraft` and represent historical data.

---

### OrderItem

A single product within an order.

Contains:

- product reference (UUID)
- quantity (`Quantity`)

---

## 3. Key Design Decisions

### Minimal Domain

The domain models only what is needed **today**.

No attempt is made to anticipate future complexity.

---

### Value Objects over Primitives

Primitive types such as `int` are replaced with:

- `ProductCode`
- `Quantity`

This improves:

- correctness
- readability
- invariants

---

### Explicit Time Modeling

The domain models time explicitly:

- drafts can only be modified before a cutoff
- finalized orders are fixed in time

This ensures predictable behavior and avoids last-minute inconsistencies.

---

### No Assortment / Restrictions

All products are considered orderable.

There are currently no restrictions per store.

---

### No Workflow / Lifecycle

There is no concept of:

- order status
- delivery tracking
- partial fulfillment

Orders are treated as submitted data, not processes.

---

### Pure Domain Layer

The domain is:

- independent of Django
- independent of database concerns
- fully testable in isolation

---

## 4. Explicitly Out of Scope (v0.1)

The following features are intentionally excluded:

### Order Lifecycle

- status (pending, completed, etc.)
- delivery tracking
- partial deliveries

---

### Inventory Management

- stock levels
- availability constraints

---

### Pricing Logic

- pricing
- discounts
- customer-specific pricing

---

### Assortment / Personalization

- store-specific product lists
- ordering restrictions

---

### Authentication & Accounts

- login flows
- roles and permissions

---

### Notifications

- email
- SMS
- automated alerts

---

## 5. Philosophy

This version prioritizes:

- simplicity
- clarity
- fast iteration

The system is designed to solve the current problem well,
not to anticipate all future requirements.

---

## 6. Design Principle

> Make invalid states unrepresentable.

This is achieved through:

- value objects (`Quantity`, `ProductCode`)
- explicit validation
- minimal, focused entities

---

## 7. Future Evolution

The domain is intentionally designed to evolve.

Future additions may include:

- order lifecycle management
- delivery planning
- product categorization
- store-specific customization

These will be introduced only when required by real usage.

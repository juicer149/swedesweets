# Domain Model

This document explains the reasoning behind the domain layer of the
SwedeSweets replenishment platform.

The domain layer represents the **business logic of the company** and is
kept independent from any technical framework such as Django.

This separation allows the core business rules to remain stable even if
the infrastructure layer (database, web framework, etc.) changes.

---

# 1. Design Principles

The domain layer follows several architectural principles.

### Framework Independence

Business logic must not depend on Django, HTTP, or database models.

This ensures that the system’s behaviour can be tested, reasoned about,
and evolved independently of infrastructure decisions.

### Explicit Business Rules

All business behaviour is implemented through explicit domain rules
instead of implicit behaviour spread across views or database models.

### Data-Oriented Design

Domain logic is expressed in terms of **data transformations** rather
than procedural control flow whenever possible.

Example:
```

Order Items → Item Statuses → Derived Order Status

```

The system therefore derives behaviour from the current state of data.

### Deterministic Behaviour

The system avoids storing redundant state when that state can be derived
from other data.

For example:

```

OrderStatus = f(OrderItemStatuses)

```

This prevents inconsistencies between orders and their items.

---

# 2. Domain Entities

The system models several core concepts.

## Product

Represents a product in the SwedeSweets catalog.

Examples:

- Cola nappar
- Hallonbåtar
- Estrella dill chips

Products exist globally and can appear in multiple store assortments.

---

## Store

Represents a retail store supplied by SwedeSweets.

Each store:

- Has its own assortment
- Creates replenishment orders
- Receives deliveries

---

## StoreProduct

Represents the relationship between a store and a product.

This defines the **assortment of a store**.

Important design decision:

Assortment templates are **copied into store-specific records**
instead of referenced.

This ensures:

- historical stability
- independence between stores
- flexibility for store-specific adjustments

---

## ReplenishmentOrder

Represents a refill request created by a store.

An order contains multiple items.

Example:

```

Order: 42

Cola nappar:	5 kg
Hallonbåtar:	3 kg
Estrella chips:	2 boxes

```

---

## ReplenishmentOrderItem

Represents a single line in an order.

Each item tracks:

- requested quantity
- delivered quantity
- delivery status

---

# 3. Order Status Derivation

The overall order status is **derived from the statuses of its items**.

The system intentionally avoids storing order status as an independent
source of truth.

Instead:

```

OrderStatus = f(OrderItemStatuses)

```

This prevents situations where:

- an order says "COMPLETED"
- but some items are still pending

By deriving the status from item data we guarantee consistency.

---

# 4. Rule Table

The derivation of order status is implemented using a **rule table**.

Example rules:

| Item Status Set  | Result 	|
|------------------|------------|
| {PENDING} 	   | PENDING  	|
| {DELIVERED} 	   | COMPLETED 	|
| contains PENDING | IN_PROGRESS|
| otherwise 	   | PARTIAL 	|

This rule-based design was chosen instead of nested conditional logic.

Reasons:

1. Explicit rule ordering
2. Easy extension when new states appear
3. Clear mapping between business rules and code
4. Reduced branching complexity

---

# 5. Example

Order items:

```

Cola nappar       DELIVERED
Hallonbåtar       NOT_DELIVERED
Estrella chips    DELIVERED

```

Derived result:

```

OrderStatus.PARTIAL

```

---

# 6. Future Extensions

The rule-table design makes it easy to introduce additional states.

Possible future states include:

- BACKORDER
- RETURNED
- CANCELLED

New rules can be added without modifying the core algorithm.

---

# 7. Why Domain Logic Is Not Inside Django Models

A common pattern in Django projects is placing business logic inside
model classes or views.

Example:

```

models.py
def calculate_status()

```

This approach tightly couples the business logic to the ORM.

In this system the domain layer exists **independently of Django**.

Benefits:

- simpler testing
- clearer architecture
- reusable domain logic
- easier refactoring

---

# 8. Architecture Overview

The system follows a layered architecture.

```

Presentation Layer
Django Views / Templates

Application Layer
Services

Domain Layer
Entities
Rules
Enums

Infrastructure Layer
Django ORM
Database

```

The domain layer contains the **stable business logic**.

Infrastructure layers may evolve without affecting it.

---

# 9. Philosophy

The goal of this system is not to build a complex ERP platform.

Instead the goal is to replace an **SMS-based ordering workflow**
with a structured and reliable system while keeping the architecture
simple and maintainable.

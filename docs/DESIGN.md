# Design Overview

This document describes the core architectural decisions of the SwedeSweets system.

The goal is to keep the system **simple, testable, and maintainable** as it evolves.

---

## 1. Separation of Concerns

The system is split into two main parts:

```
Domain Layer        → Business logic (pure Python)
Infrastructure      → Django (web, database, UI)
```

### Domain

Located in:

```
src/swedesweets/domain/
```

The domain contains:

* core entities (Order, Product, Store, etc.)
* business rules
* validation logic
* use-case functions (services)

**Properties:**

* No external dependencies
* No Django imports
* Fully testable in isolation
* Deterministic behaviour

---

### Django (Backend)

Located in:

```
web/
```

Responsible for:

* HTTP handling (views)
* persistence (database models)
* authentication
* rendering UI

**Important:**

Django must not contain business logic.

---

## 2. Core Principle

> The domain is the source of truth.

Django is only a delivery mechanism.

---

## 3. Data Flow

The system follows this flow:

```
HTTP Request
    ↓
Django View
    ↓
Domain (business logic)
    ↓
Database (via Django models)
    ↓
HTTP Response
```

---

## 4. Rules

### Domain Rules

* All business rules live in the domain
* Domain objects validate their own state
* No framework-specific code in domain

---

### Django Rules

* Django models only represent stored data
* No business logic in models or views
* Views call domain functions

---

## 5. Why This Design

This separation provides:

### Testability

Domain logic can be tested without Django or a database.

### Flexibility

The web framework can be changed without rewriting business logic.

### Simplicity

Each layer has a single responsibility.

---

## 6. Non-Goals (for now)

The system intentionally avoids:

* complex workflow engines
* tightly coupled ORM logic
* premature abstractions

The design prioritizes solving the current problem well.

---

## 7. Philosophy

The system follows a simple principle:

> Keep the core small and stable. Build everything else around it.

The domain should change slowly.
The outer layers can evolve as needed.

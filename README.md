# SwedeSweets

SwedeSweets is a simple ordering platform for retail stores to request product restocking.

The system replaces an **unstructured SMS-based workflow** with a structured and reliable ordering process.

---

## Problem

Today, stores place orders via SMS.

This leads to:

- unclear messages
- manual interpretation
- risk of mistakes
- no consistent structure

---

## Solution

SwedeSweets provides:

- a simple interface for stores to place orders
- structured order data
- reduced communication overhead
- a more professional workflow

---

## Core Idea

Instead of:

```

"Need 3 cola, 2 sour..."

```

Stores submit structured orders:

```

Product 42 → Quantity 3
Product 17 → Quantity 2

```

---

## Architecture

The system is built with a clear separation of concerns:

```

src/
└── swedesweets/
└── domain/      # Pure business logic (no Django)

```
```

backend/             # Django (web layer, DB, API)

````

---

### Domain Layer

The domain is:

- framework-independent
- fully testable
- based on explicit business rules

Key concepts:

- `Store`
- `Product`
- `Order`
- `OrderItem`

---

### Value Objects

Primitive types are replaced with domain-specific types:

- `ProductCode`
- `Quantity`

This ensures:

- valid data
- clearer intent
- fewer bugs

---

## Features (v0.1)

- create orders
- structured order items (product + quantity)
- simple store model
- product catalog support (via code + name)

---

## Out of Scope (for now)

- order status / lifecycle
- inventory management
- pricing logic
- authentication & permissions
- notifications

---

## Testing

The domain is fully tested using `pytest`.

Run tests:

```bash
pytest
````

With coverage:

```bash
pytest --cov=swedesweets
```

---

## Setup

Create virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -e .
pip install pytest pytest-cov
```

---

## Development Philosophy

This project follows a few core principles:

* **Keep it simple**
* **Model only what is needed now**
* **Make invalid states unrepresentable**
* **Separate domain from framework**

---

## Roadmap

Future versions may include:

* order history
* delivery planning
* product categorization (tags)
* store-specific personalization
* admin interface

---

## Context

This project is built to support a real business:

A small distributor of Swedish candy supplying retail stores in France.

The goal is not to build a complex system, but to:

> replace SMS with something simple, reliable, and scalable

---

## Status

MVP (v0.1) — in active development

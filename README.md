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

- `src/swedesweets/domain/` — **pure business logic** (no Django)
- `backend/` — Django (web/API layer + database)

### Domain Layer

The domain is:

- framework-independent
- fully testable
- focused on explicit business rules

The core workflow is modeled as two immutable snapshots:

- `RequestedOrder` — store intent (what the store asked for)
- `FulfilledOrder` — supplier fact (what was actually packed/accepted)

A fulfilled order can later be marked delivered by setting `delivered_at`.

Key concepts:

- `RequestedOrder`, `RequestedItem`
- `FulfilledOrder`, `FulfilledItem`
- value objects: `Quantity`, `OrderId`, `StoreId`, `ProductId`

Notes:

- Orders are **ASAP** (no delivery date in v0.1).
- Supplier can record `packing_notes` on the fulfilled order.
- Differences between requested vs fulfilled can be computed via a domain diff.

### Ports & Use Cases

The domain exposes small interfaces (“ports”) for persistence/time, and pure use-cases:

- `RequestedOrderRepository`, `FulfilledOrderRepository`
- `Clock`, `UnitOfWork` (optional)
- use cases: `request_order`, `pack_order`, `deliver_order`

---

## Features (v0.1)

- store can create **requested orders**
- supplier can pack/accept a requested order into a **fulfilled order**
- supplier can mark fulfilled orders as delivered (`delivered_at`)
- diff between requested vs fulfilled (useful for rare out-of-stock cases)
- product catalog managed via Django admin (Django layer)

---

## Out of Scope (for now)

- authentication & permissions (store_id is provided by client for MVP)
- inventory management / stock levels
- pricing logic
- customer-facing B2C merch flow (hoodies, t-shirts)
- notifications
- partial deliveries (1 request → multiple shipments)

---

## API (high-level)

The Django API is responsible for:

- product catalog endpoints
- creating requested orders
- supplier packing + delivery actions

(Exact endpoints may change while the v0.1 web layer is implemented.)

---

## Testing

Run all tests:

```bash
pytest
```

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

### Run Django locally

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Admin:

- `http://127.0.0.1:8000/admin/`

---

## Development Philosophy

- **Keep it simple**
- **Model only what is needed now**
- **Make invalid states unrepresentable**
- **Separate domain from framework**

---

## Roadmap

Future versions may include:

- authentication (derive store_id from logged-in user)
- order history per store
- richer supplier fulfillment (per-item missing reasons / substitutions)
- partial deliveries (shipments)
- B2C merch ordering flow (hoodies/t-shirts)
- improved UI

---

## Context

This project is built to support a real business:

A small distributor of Swedish candy supplying retail stores in France.

The goal is not to build a complex system, but to:

> replace SMS with something simple, reliable, and scalable

---

## Status

MVP (v0.1) — in active development

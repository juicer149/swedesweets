# Domain Scope (MVP v0.1)

This document defines the scope and boundaries of the SwedeSweets domain for version 0.1.

The goal of this version is to replace an **unstructured SMS-based ordering workflow** with a simple and reliable digital process.

---

## 1. Core Problem

Stores currently place orders via SMS.

This results in:

* unclear order structure
* manual interpretation
* risk of mistakes
* poor overview of orders

The system replaces this with a structured order flow.

---

## 2. Domain Model (Included)

The MVP domain models only what is required to support this flow.

### Store

A customer (retail store) that places orders.

### Product

A product that can be ordered.

### StoreAssortment

Defines which products a store is allowed to order.

Each store has its own assortment.

### Order

A submitted order from a store.

### OrderItem

A single product and quantity within an order.

---

## 3. Key Design Decisions

### Minimal Domain

The domain only models what is needed **today**.

No attempt is made to model future requirements prematurely.

---

### No Derived or Redundant State

The system avoids storing additional state that is not required.

Orders are simple requests, not lifecycle-managed entities.

---

### No Workflow Complexity

There is no concept of:

* order status
* delivery tracking
* partial fulfillment

Orders are treated as submitted data.

---

### Store-Specific Assortments

Stores can only order from their own assortment.

This prevents invalid or unexpected orders.

---

## 4. Explicitly Out of Scope (Future Versions)

The following features are intentionally excluded from v0.1:

### Order Lifecycle

* delivery tracking
* order status (pending, completed, etc.)
* partial deliveries

### Inventory Management

* stock levels
* availability constraints

### Pricing Logic

* customer-specific pricing
* discounts
* pricing rules

### Account Management Flows

* self-service registration
* approval workflows

### Notifications

* email
* SMS
* automated alerts

---

## 5. Philosophy

This version prioritizes:

* simplicity
* clarity
* speed of delivery

The system is designed to solve the current problem well, rather than anticipate future complexity.

Future versions can extend the domain incrementally as new requirements become concrete.

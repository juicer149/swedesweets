# Domain (v0.1)

The domain is intentionally small and framework-independent.

## Domain concepts

- `Order` (append-only event / immutable)
- `OrderItem`
- `DeliveryDate`
- `Quantity`

The domain does **not** model:
- `Store` as an entity (only `store_id` is used)
- `Product` as an entity (orders reference product_id; API uses product_code which is mapped in Django)

## Key design decision: append-only orders

- Orders are facts: once created they are not edited.
- Supplier views aggregated totals via packing list queries.
- Any future changes/cancellations would be represented as new events (v0.2+), not by mutating past orders.

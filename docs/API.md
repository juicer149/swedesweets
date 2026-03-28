# SwedeSweets API (v0.1)

SwedeSweets uses **append-only orders**. There is no draft/edit workflow in v0.1.

## Products

### GET /api/products/?q=...

Returns product catalog for UI.

Response 200:
```json
[
  {"code": 42, "name": "Cola Nappar"},
  {"code": 17, "name": "Hallonbåtar"}
]
```

## Orders

### POST /api/orders/

Creates an order (immutable fact).

Body:
```json
{
  "store_id": "uuid (MVP; later derived from auth)",
  "delivery_date": "YYYY-MM-DD",
  "items": [
    {"product_code": 42, "qty": 3},
    {"product_code": 17, "qty": 2}
  ]
}
```

Response 201:
```json
{"order_id": "uuid"}
```

Notes:
- `product_code` is mapped to a `ProductModel` in the Django layer.
- The database stores product snapshots (code + name) on each order item.

## Supplier

### GET /api/supplier/packing_list/?delivery_date=YYYY-MM-DD

Aggregates all order items for the delivery date.

Response 200:
```json
[
  {"product_code": 42, "product_name": "Cola Nappar", "total_quantity": 12}
]
```

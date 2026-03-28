# Flows (v0.1)

## Store flow
1. Load products: `GET /api/products/`
2. Create an order: `POST /api/orders/`

## Supplier flow
1. Choose a delivery date
2. Get aggregated packing list: `GET /api/supplier/packing_list/?delivery_date=...`

## Authentication note
In v0.1 the API accepts `store_id` from the client.
In a later version, `store_id` should be derived from the logged-in user/session.

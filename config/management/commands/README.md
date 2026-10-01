# Management commands

| Command | Purpose |
|---|---|
| `ensure_admin_user` | Create or update the superuser from environment variables (runs on deploy) |
| `reconcile_payments` | Reconcile retail payments with the payment provider |
| `export_order_history` | Export order history as JSON, outside the repository |
| `seed_demo_data` | Synthetic demo data, local development only |

## Demo data

```bash
make reset-demo   # seed_demo_data --reset --with-orders --with-demo-user
```

Everything except the product catalogue is invented (`_demo_data.py`):

- six business customers in Haute-Savoie with `@example.com` addresses and
  phone numbers from the range reserved for fiction (+33 1 99 00 xx xx)
- one long-dated batch per active product, plus short-dated batches for the
  expiry queue and a few small ones for the low-stock queue
- four retail merch products with EUR prices
- 28 B2B orders over the last eight weeks: 4 placed, 4 packed, 20 delivered

Dates are relative to the day it runs, so the queues always look current.
The command refuses to run unless `DEBUG=True`. Real orders and customer
data never belong in the repository; use `export_order_history` for those.

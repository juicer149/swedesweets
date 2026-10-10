# Product variants

Status: agreed; steps 1–2 done, step 3 (pricing) in progress.

A product can come in variants: a hoodie in XS–XL, a chocolate bar in 60, 100
and 120 g. Variants are modelled the way Shopify does it: **every product has
at least one variant, and the variant is what is stocked, priced, sold and
packed.** A product with one variant (every product today) shows no choice;
the rest of the system handles both alike.

## Model

```text
Product                        what a customer sees as one thing
  name, brand, manufacturer
  internal_number              "#1": the informal number used with customers
  stock_unit                   box, piece, bag, case (same for all variants)
  active, vegan, profile       picture, description, category (ProductProfile)
  translations

ProductVariant                 what is stocked, priced, sold and packed
  product                      FK, PROTECT
  label                        "M", "60 g"; "" for a product's only variant
  position                     order shown everywhere (1, 2, 3 …)
  sku                          unique; generated, stable
  weight_per_unit              grams for one stock unit (shown on labels,
                               parcels); immutable once used
  active                       False: paused (see Rules)
```

The three relations that point at `Product` today move to the variant:

| Model | Today | After |
| --- | --- | --- |
| `inventory.InventoryBatch` | `product` | `variant` (required), `product` kept |
| `pricing.CommercialPrice` | `product` (+ optional `batch`) | `variant` (+ optional `batch`), `product` kept |
| `orders.OrderLine` | `product` | `variant` (required), `product` kept |

Everything else follows from those:

- **Carts** point at a `CommercialPrice`, so a cart line knows its variant
  without a new field.
- **Reservations** (`Allocation`) point at a batch and an order line, both
  of which know their variant.
- `OrderLine.product` stays as a plain historical fact (reports, "Order
  again"), always equal to `variant.product`. `InventoryBatch.product` stays
  too, for the same reason and so stock queries by product keep working;
  the batch keeps the two in step (it fills in the product of a given
  variant, and the only variant of a given product).

## Rules

1. Every product has at least one variant.
2. A variant with an empty label is its product's **only** variant. Adding a
   second variant gives the first one a label.
3. Labels are unique within a product, compared case-insensitively.
4. `sku` is unique across all variants. A product's only variant keeps the
   product's existing SKU; a labelled variant gets the product's SKU plus the
   label (e.g. `SWS-HOODIE-M`).
5. `weight_per_unit` cannot change once the variant has a batch or an order
   line (as on `Product` today).
6. A variant that has ever had a batch, a price, a cart line or an order line
   cannot be deleted, only **paused** (`active=False`). A paused variant is
   left out of catalogs, new batches and new orders; its history stays.
7. The last active variant of an active product cannot be paused (pause the
   product instead).
8. Consistency, enforced in the services and tested:
   - a batch offer's `variant` is its batch's variant;
   - an order line's `variant` is its offer's variant;
   - an allocation only takes stock from batches of the order line's
     variant.

The services in `products` own rules 1–7; `inventory`, `pricing`, `orders`
and `reservations` own rule 8.

## What shows where

- **Name:** `"Hoodie — M"` wherever one variant is meant (cart lines, order
  lines, packing lists, mails, exports, ops search); `"Hoodie"` where the
  product is (catalog card, product page). One helper builds it.
- **Choice:** only when a product has more than one active variant.
- **Catalog and product page:** one card per product. "+" (or "Add to
  cart") opens the variants as round radio chips, sold-out ones muted and not
  selectable, then the tick and the cross, then the quantity.
- **Stock:** counted per variant ("Only 3 left" means of that size). A
  product's card is sold out when every variant is.
- **Price:** set per variant. Ops sets one price for all variants at once and
  can change one variant's price on its own.

## Ops

- **Product page** gets a **Variants** tab: the variants in order with the
  stock of each.
- **Edit** gets a **Variants** tab:
  - reorder by dragging (and up/down buttons for phones);
  - behind a lock: add, rename, set a weight, pause, delete (only without
    history, rule 6);
  - saved with the form's Save, like the other tabs.
  Suggested labels (XS, S, M, L, XL, XXL, One size) come as a datalist; any
  text is allowed.
- **Add batch:** after the product, its variant (skipped for a product with
  one variant). The product search lists each variant as its own row.
- **Order form:** each variant its own row in the search; Previous orders
  per variant.

## Migration

Data migrations written to run on production data, one per step:

1. For every product, create one variant: label `""`, position 1, the
   product's `sku` and `weight_per_unit`, active (`products/0008`, step 1).
   Active even for an inactive product: the product's own switch decides
   whether it is sold, and a paused only variant would leave nothing to
   sell when the product is switched back on.
2. Point every batch, commercial price and order line at its product's
   variant (steps 2–4, each in its own app).
3. Make the new `variant` fields required.

It is tried on a copy of the production database before it runs on Railway.
`Product.sku` and `Product.weight_per_unit` stay until the last step (below)
so that nothing reads a missing field halfway.

## Steps

Steps 1–4 change no behaviour: every product has exactly one variant, so the
site works as today and the existing tests stay green. Steps 5–7 bring the
variants into view.

1. **Model** — `ProductVariant`, the migration, factories that make a
   product's variant automatically, the name helper.
2. **Inventory** — every batch is of one variant (`inventory/0003–0004`);
   a product with one variant fills it in on its own. Stock and low stock
   per variant come with the pages that show them (steps 5–6): with one
   variant per product they equal the product's.
3. **Pricing** — every offer is for one variant (`pricing/0003–0004`): a
   batch offer's is its batch's, a product with one variant fills it in.
   One standard offer per variant and channel; the old one-per-product
   rule stays until the code that looks offers up by product reads them by
   variant. Catalog offers per variant and ops pricing for all variants at
   once come with steps 5–6.
4. **Orders** — order lines by variant; allocation by variant; packing list,
   mails, exports, "Order again".
5. **Ops products** — the Variants tabs, the lock, create a product with
   variants.
6. **Catalogs and carts** — retail and business: chips, sold-out sizes,
   the "+" flow, names in carts and the navbar cart.
7. **Ops orders** — the order form and Previous orders by variant.
8. **Clean-up** — drop `Product.sku` and `Product.weight_per_unit` (read
   from the variant); demo data: hoodie and T-shirt in XS–XL.

Each step is its own branch, merged with the full test suite green.

## Tests that matter most

- The migration: every row gets its variant; counts before and after match.
- Allocation never takes stock from another variant of the same product.
- Stock per variant in the catalog, "Only N left" and the dashboard.
- Rules 1–7 in the product services.
- A product with one variant looks and behaves exactly as today.

## Open questions

- Should a variant be able to have its own picture (a colour, say)? Not
  needed for sizes; the model leaves room for it.
- Business customers: merch stays retail-only for now; the model does not
  depend on the channel.

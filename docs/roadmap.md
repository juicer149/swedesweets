# Roadmap

What is planned next, in order, with what has been decided. Items move to
"Done" as they reach `main`; when everything here is done the file goes.
Product variants have their own spec: [product-variants.md](product-variants.md).

## Decided

- **Variants have a label only** ("S", "60 g"); no longer full name. The
  shop sells in one region of France, where a label reads the same in every
  language.
- **The model stays `ProductVariant`** (table `products_productvariant`),
  like `ProductProfile` and `ProductTranslation`.
- **Retail checkout is one page**: the cart lines and the contact details
  together, all editable; "Continue to payment" validates everything on the
  server, creates the order and goes to SumUp. No separate review page.
  B2B keeps its review before placing an order.
- **Mobile cart**: the cart icon goes to the cart page, drawn as a sheet
  that grows out of the icon (cross-document View Transitions), closed by
  the cross or the icon, back to the page before. Plain navigation where
  the browser has no View Transitions. The cart is already on the server;
  half-filled contact details are kept in the session.
- **Prices per variant**: one price typed for all variants is saved as each
  variant's own price; one variant's price can be changed on its own.
- **Swedish as a site language**: later, not now.

## Open questions

- Is **brand + name** unique (two brands may each have a "Sour Mix"), or the
  name alone? Product + variant label then identifies one thing to sell.
- **Order lines keep a copy** (name, label, SKU, weight, unit, price,
  thumbnail path) so old orders read the same whatever happens to the
  product. Should products then be deletable (the order line's link
  emptied), or only archived?

## Next, in order

1. **Ops product pages** — see below.
2. **Order lines keep a copy** of what was bought, and brand + name unique
   (after the open questions).
3. **Variants, step 6**: catalogs and carts (retail and business) with the
   size chips, sold-out sizes, the variant in cart lines and the navbar
   cart; merch shows its size, not a candy weight. Prices per variant in
   ops. The one-standard-offer-per-product rule goes.
4. **Variants, steps 7–8**: the ops order form by variant; clean-up
   (`Product.sku` and `Product.weight_per_unit` read from the variant).
5. **Shared expandable row** (button with `aria-expanded`, the FAQ and
   dashboard animation), then the ops lists that use it:
   - Products: picture and name first, brand, manufacturer and weight as
     quiet text under the name, vegan as an icon, active as a small dot,
     available stock coloured by level. Expanded: in stock, reserved,
     available and active batches, per variant when there are several
     (variants of one product share its stock unit, so the row may sum
     them), and "View details". Inventory's "Product stock" view goes.
   - Customers: contact details and active orders, "View details".
   - Accounts: last login, role, the three latest activities, "View
     details"; from the existing activity history, no new log.
6. **Retail flow**, after a look at what exists (payment states, webhooks,
   reconciliation and their tests are already there):
   1. Mini-cart on desktop: picture, name, variant, unit price, stepper
      (the minus becomes the trash at 1 in retail; B2B keeps a separate
      trash and a muted minus at 1); scrolling lines with subtotal and
      "Go to cart" always visible; closes on Escape and outside clicks.
   2. The mobile cart sheet.
   3. Cart and contact details on one page.
   4. Confirmation page and mail; SumUp keys set in Railway.
7. **Order messages**, in three parts:
   1. A thread per order ("Have a question about this order?"), status,
      ops replies from the order, mail to info@ and to the customer (the
      app is the record; mail only notifies, with retry and no doubles),
      a sixth dashboard queue.
   2. Quick replies for ops, a thumbs up for customers.
   3. Questions that need the customer's decision (approve or decline),
      each acted on by a separate, checked order action.
   The model lives in `orders` to begin with.
8. **Catalog cards**: weight or size under the name, the price on its own
   small tilted label, attribute icons; colours per category, sketched in
   Figma first, together with the size chips from step 6.

Small things to fit in anywhere: on `/ops/orders/<id>/deliver/` the contact
details follow the page's left edge instead of sitting centred (check
mobile).

## Ops product pages

**Detail page**, three tabs:

- **Product**: everything about the product under headings: details
  (catalog ID, brand, name, status, attributes, the variants' labels on one
  line), **Variants** (each with its weight, price and stock), **Pricing**.
- **Catalog**: the product as customers see it (the catalog card and its
  page), so the catalog data is checked by looking at it.
- **Inventory**: stock and batches, as today.

**Edit page**, one page without tabs, everything about the product in
sections, actions at the bottom:

1. Product: catalog ID (was "internal number"; typed, no spinner arrows),
   manufacturer, brand, name, status as one switch (green on, muted off)
   instead of two radio buttons, vegan.
2. Catalog: picture, category, French name, description, ingredients.
3. Pricing: one price for all variants (per variant in the next section).
4. Variants: the current Variants editor, lock and all, last before the
   actions.

## Done

- Ordering by weight removed (order lines count stock units).
- Product variants, steps 1–5: the model, batches, prices and order lines
  by variant, the ops Variants tab, the variant when adding a batch.

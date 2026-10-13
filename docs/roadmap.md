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
- **Prices per variant**: each variant has its own prices (per channel
  and currency), as they are stored; no product price over them. "Use
  for all variants" copies one variant's prices to the others. Each
  variant has its own sales channels (retail, business); in neither, it
  is paused.
- **Price changes ask for the password**: saving a change to a price
  already set (raised, lowered, removed) lists the changes and asks for
  the password again; a first price never asks. `PRICE_CHANGE_CHECK`
  (environment, on by default) switches it off while prices are typed in.
  Done on the product edit page; batch offers to follow. The password
  once more is its own piece (`accounts/password_again.py`, its dialog
  `includes/ui/password_again_dialog.html`) for other places to use: five
  wrong ones lock it for 15 minutes. Login has no such limit yet: worth
  the same.
- **Edit pages**: sections open one under the other (no folding, no
  locks: having opened the edit page is the intent; what needs a second
  look asks for it, like price changes); saving comes back to the same
  page.
- **Product page and edit page alike**: the product page shows the same
  cards as the edit page, to read: tabs Product (the product's card with a
  pencil in its corner, then Variants and offers, each variant's channels
  with their prices at its right), Catalog, and Inventory (each variant's
  batches at its right). Stock lives only on Inventory.
  Edit stays a page of its own for now (one page for both, later
  perhaps).
- **Tabs in a form show their changes**: a tab whose panel has a changed
  field gets a dot (`dirty_form.js`), first on the catalog page's
  languages.
- **Pages with tabs**: Back at the tabs' left (to the page one came
  from, else the page's list; the arrow alone on phones), the open tab's
  action at their right (page_tabs.html: `tabs_back_url`,
  `tab_actions`); no Back under the page. Every detail page has the Back;
  actions are added page by page, first on the product page.
- **Help on a page**: a round "?" beside a title opens a dialog with what
  everything there means (`includes/ui/help.html`, its text a template of
  its own; a form section takes it as `help`). First on Variants and
  offers; add it where other pages need explaining.
- **Swedish as a site language**: later, not now.
- **Catalog text per language**: each language (`settings.LANGUAGES`, French
  first) has its own name, description and ingredients. The texts written
  so far are French. Where a language has none of its own, the shop shows
  the product's own (Swedish) name, and the French description and
  ingredients. Variant labels per language may come later.

## Open questions

- Is **brand + name** unique (two brands may each have a "Sour Mix"), or the
  name alone? Product + variant label then identifies one thing to sell.
- **Order lines keep a copy** (name, label, SKU, weight, unit, price,
  thumbnail path) so old orders read the same whatever happens to the
  product. Should products then be deletable (the order line's link
  emptied), or only archived?

## Next, in order

0. **Edit pages in one design**, before the steps below. The product and
   catalog pages set it: "Edit" over the name in the heading; open
   sections, locks where data matters; statuses as one switch, first in
   their part; EUR / SEK as filter chips; saving stays on the page. Then
   the other edit pages, one by one: batches (its pricing too), customers,
   orders, accounts.
1. **Order lines keep a copy** of what was bought, and brand + name unique
   (after the open questions).
2. **Variants, step 6, the rest**: the "+" on a card opens the sizes as
   round chips (sold-out ones muted) instead of leading to the product
   page; the variant's name on packing lists, mails and exports; merch
   shows its size, not a candy weight. Sketched in Figma with the catalog
   cards.
3. **Variants, steps 7–8**: the ops order form by variant; clean-up
   (`Product.sku` and `Product.weight_per_unit` read from the variant).
4. **Shared expandable row** (button with `aria-expanded`, the FAQ and
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
5. **Retail flow**, after a look at what exists (payment states, webhooks,
   reconciliation and their tests are already there):
   1. Mini-cart on desktop: picture, name, variant, unit price, stepper
      (the minus becomes the trash at 1 in retail; B2B keeps a separate
      trash and a muted minus at 1); scrolling lines with subtotal and
      "Go to cart" always visible; closes on Escape and outside clicks.
   2. The mobile cart sheet.
   3. Cart and contact details on one page.
   4. Confirmation page and mail; SumUp keys set in Railway.
6. **Order messages**, in three parts:
   1. A thread per order ("Have a question about this order?"), status,
      ops replies from the order, mail to info@ and to the customer (the
      app is the record; mail only notifies, with retry and no doubles),
      a sixth dashboard queue.
   2. Quick replies for ops, a thumbs up for customers.
   3. Questions that need the customer's decision (approve or decline),
      each acted on by a separate, checked order action.
   The model lives in `orders` to begin with.
7. **Catalog cards**: weight or size under the name, the price on its own
   small tilted label, attribute icons; colours per category, sketched in
   Figma first, together with the size chips (step 2).

Later, not planned yet: **prices in SEK from EUR** at the day's rate (an
exchange-rate API), EUR staying the price that is set; the SEK fields would
then show the converted price instead of being typed.

Small things to fit in anywhere: on `/ops/orders/<id>/deliver/` the contact
details follow the page's left edge instead of sitting centred (check
mobile).

## Ops product pages

**Detail page** (no hero; a hidden page title), three tabs; at their left
Back, at their right the open tab's action: "Edit" (pencil) to the
product's form on Product, the catalog's on Catalog, "Add batch" on
Inventory (`TabAction`, page_tabs.html):

- **Product**: the product's card (picture, brand over name, status,
  catalog ID, SKU, manufacturer, attributes; a pencil in its top right
  corner, no stock), then **Variants and offers**: a card per variant
  (label, weight; at its right its channels as chips, Business over
  Retail, each with its price beside it when sold in it).
- **Catalog**: the language tabs alone, a label over the shop's page
  ("In shop", or what keeps it out), the shop's product page a little
  smaller; category and picture.
- **Inventory**: a card per variant (label, weight), at its right its
  batches on the shelf stacked, the soonest best-before at the top: each
  batch's ID and how many, to its page; none with less than one unit;
  past its best-before and not closed in red, within `EXPIRY_SOON_DAYS`
  (inventory/expiry.py) in orange.

**Catalog page** (no hero; a hidden page title): the category, the
picture small at its right, then name, description and ingredients under
one tab per language; a language with a change gets a dot.

**Edit page**: Product as a card (its picture, catalog ID and status at
its top, brand and name large), then **Variants and offers**: EUR / SEK
tabs, then a card per variant: arrows (up at the top, down at the
bottom), label, weight, its sales channels one over the other (Business,
Retail), each with its price at its right (read-only and greyed while
the channel is off), "Use for all variants" under them; "+ Add variant"
as a faint last row. Price changes ask for the password.

## Done

- Ordering by weight removed (order lines count stock units).
- Product variants, steps 1–5: the model, batches, prices and order lines
  by variant, the ops Variants tab, the variant when adding a batch.
- Catalog text per language, the catalog page and its preview; the edit
  pages' heading.
- Prices per variant (step 6): a standard offer per variant, set from the
  edit page; catalogs and carts by variant (a card with several sizes
  leads to its page), names with the size in carts and orders.

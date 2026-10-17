# Design

How SwedeSweets looks and why. The decisions here were made page by page
while the site moved to the *calm design*; this file collects them so a new
page can follow them without reading the history. `ARCHITECTURE.md` covers
the code; this covers what people see.

The CSS files carry the details (each one starts with a comment saying what
it owns). This file is the map, the rules and the reasons.


## The calm design in one paragraph

No boxes. Content sits on the page itself, in one centred column, with a
soft glow behind it that holds it together. Rows are divided by hairlines,
not cards. Each page has **one primary action** (yellow in light; navy with blue text/edge
and gold hover light in dark); secondary actions are quiet
text links, coloured by the theme. Colour is spent only where it means something (a status, a pin,
the action). Mobile first: on a phone the actions sit at the bottom, within
reach of the thumb. Words are short, and the page does not repeat what the
navigation already says.


## Principles

1. **No boxes.** No white cards, no yellow-topped panels, no borders around
   groups. Group with space, hairlines and the glow (`.page::before`).
   One exception, on ops work pages: **the thing being worked on is a
   card** (a product, each of its variants), the same card on its page
   and on its edit page, so the edit page reads as the page made
   editable. See "Ops work pages" below.
2. **One primary action per page.** The main button is "the thing to
   do here"; its palette follows the theme. Cancel, back, decline, remove: quiet links. If a page seems to
   need two primary buttons, one of them is a link or belongs on another page.
3. **Colour means something.** Yellow = the brand, selection and action
   emphasis. Blue = available links, actions and navigation. Brick red = a place on a map. Green, amber, red,
   grey = status. Decoration that is not one of these is neutral or
   brand yellow, softened.
4. **The navigation already says where you are.** List pages and create
   forms have no visible title; they keep an `h1` for screen readers
   (`includes/ui/list_page_head.html`, `class="visually-hidden"`).
5. **Fit the screen.** A page that can fit one screen does not scroll. Size
   with `clamp()` and `dvh` before adding a breakpoint.
6. **Reuse before inventing.** A new page is built from the parts below. A
   new part is added to `includes/ui/` with a header comment, and only when
   two pages need it.


## Light and dark themes

Light is the default: a cream page and brand-blue menu. The customer dark
palette uses deep blue surfaces, neutral reading text and light blue available
interactions. Ops remains light until its work pages have been reviewed.
Theme selection and implementation details are in [CSS themes](docs/css-themes.md).

Gold marks the brand, hovered/focused main actions and selected states. The active sort heading uses a slightly deeper gold (accent-700); section tabs
share navigation gold (accent-600). Available
choices use interactive blue. Hover/focus on an order row marks its edge blue,
while its background retains its status hue: placed gold, packed blue,
delivered green, cancelled red. Dark table rows share a tint intensity,
which increases on hover without changing the status hue. Orange warning prose remains distinct from gold selection surfaces.

Dark public section tabs, Find Sweets shop names and FAQ question rows share the
navbar's diffuse hover/focus light and illuminated lettering. Selected tabs use
light instead of an underline; open FAQ questions keep only the light behind
their title and chevron, without a tinted rectangle. FAQ and Find Sweets lights
follow the question/name and icon separately, rather than lighting the empty
middle of the row. Addresses
and answers stay neutral. The landing menu and its account/cart/language controls
use the same backlight, as does the navbar Login action. The chosen landing
item owns its light even when pointer input follows keyboard focus. Login/password
page home logos share the navbar logo's gold hover/focus treatment. Ready catalog cart buttons
are interactive blue, becoming gold with the navbar cart's backlight on hover or
keyboard focus; success feedback remains green. Catalog card hover and focused
quantity/size fields also use the warm gold light; available controls remain blue.
Dropdown options pair foreground
and background colours so selected countries and variants remain readable.
Variable mappings live in [docs/css-themes.md](docs/css-themes.md).

Catalog labels have a palette per theme: light paper in light, blue surfaces
with a gold name band in dark. Quantity and variant fields are blue when
available and gold while focused/open. Fixed weight is neutral; price tags
keep their own gold ink. About's polaroid remains light with dark lettering,
and product photos retain their original colours.

Layout and behaviour are shared by both themes. The catalog wraps at a readable
minimum card width, with at most four columns. The detail title scales from
the source card's text area to retain its proportions. Navigation reserves
space for its crown and customer pages keep a stable scrollbar gutter.

Review both themes with focus, hover, disabled, open, loading, success and error
states. Theme files own colour choices; component files own layout and states.
Shared roles describe meaning, not merely matching colours: ordinary text,
interaction, action, selection and status remain independently adjustable.
Use component mappings for deliberate exceptions. Do not invert primitive
colour scales to switch the theme.

## CSS ownership

| Location | Owns |
|---|---|
| `static/css/tokens.css` | Primitive colour scales, typography, sizes, spacing and motion timings |
| `static/css/themes/` | The semantic colour choices for light and dark |
| `static/css/common/` | Shared components: icons, buttons, forms, navigation, rows and dialogs |
| `static/css/public/` | Customer-page styles, including both retail and B2B |
| `static/css/ops/` | Staff work-page styles |
| `static/css/main.css` | The imports shared by both surfaces |
| `static/css/public.css`, `ops.css` | The shared foundation plus each surface's own styles |

Component files own selectors, layout, typography, responsive behaviour and
interaction rules. Theme files supply the colours those rules consume.
For example, `public/catalog.css` places and animates the label;
`themes/light.css` and `themes/dark.css` choose `--label-bg`.
A component used by both ops and customer pages belongs in common, even
when it first appeared on one page (FAQ and previous orders share the
accordion). A folder name describes ownership, not the logged-in role.

Theme preview URLs, import details and the workflow for changing a page
are documented in [docs/css-themes.md](docs/css-themes.md).


## Colour

Primitive colour scales are in `static/css/tokens.css`. Semantic colour choices
live in `static/css/themes/light.css` and `themes/dark.css`. Component CSS
uses those roles; see [docs/css-themes.md](docs/css-themes.md).

| Use | Token | Notes |
|---|---|---|
| Page background | `--page-bg` | warm cream in light, deep blue in dark |
| Body text | `--text-main` | |
| Titles | `--color-text-heading`, `--page-title-color` | theme-dependent |
| Quiet text and notes | `--text-muted` | |
| Hairlines | `--line-soft`, `--line-strong` | theme-dependent |
| The action | `--color-action-place-solid` | softened yellow in light, solid yellow in dark |
| Links | `--color-link` | dark blue in light, light blue in dark |
| A place (pins, addresses) | `--contact-place` | brick red in light, lighter red in dark; distinct from danger |
| Brand (logo, crown) | `--color-brand-yellow`, `--color-brand-blue` | sampled from the logo |
| Status | `--color-status-{success,warning,info,danger,muted}-text` | |

Status colours mean the same everywhere:

- **Orders:** placed = amber, packed = blue, delivered = green,
  cancelled = red.
- **Stock** (`quantity-text--*`): plenty = green, running low = amber,
  low or empty = red.
- **Yes/no** (`includes/table/bool_icon.html`): green tick, grey cross.
- **A fact's state** (`.facts__status` with `status-text--*`): Active =
  green, Inactive = red, Listed = green, Not listed = grey.
- **Contact rows:** mail, phone and place icons each have their own tone
  (`.icon-rows__icon--mail|phone|place`).
- **A sales channel** (`.variant-view__chip`): sold in it = green with a
  tick, not = grey with a cross.
- **Best-before** (`inventory/expiry.py`): past it = red, within
  `EXPIRY_SOON_DAYS` = amber (`--color-expiry-soon-text`), else dark blue
  (primary-900) or plain text.
- **Something to act on** (`.inventory-notes`): a red note with the
  warning icon at the top of its tab (out of stock, batches past their
  best-before).

Decoration (the binoculars) uses brand yellow softened with
`color-mix(… transparent)` so it never reads as a button.


## Type

- **Body:** Nunito (`--font-body`). **Headings:** Fredoka
  (`--font-heading`, weight `--font-weight-heading`, 600): round like the
  logo, so the glad voice sits in headings and everything read or filled
  in stays calm.
- Both are our own files (`static/fonts/`, `css/common/fonts.css`), never Google's
  servers. Nunito's figures are equal width, so prices and quantities line
  up without `tabular-nums`.
- Sizes from the scale `--font-size-12 … -64`. Page titles are small and
  calm (`.page__lead`, `--font-size-20`), not hero-sized.
- Headings have no full stop. Sentences in notes do.
- A closing line or a quote may use the heading font (`.about__signoff`).


## Space and sizes

- Spacing tokens `--space-1 … -16`. Gaps that should shrink on small
  screens use `clamp(var(--space-x), Ndvh, var(--space-y))`.
- Breakpoints (the only widths a media query may use): `1023px`, `767px`
  (phone: bottom navigation, actions at the bottom), `639px`, `479px`
  (and their `min-width` complements, `768px` and so on).
- Icons: `--size-icon-sm` (1rem) in text and rows, `-md` for pins.
- The column: `.page` is 380px; `--wide` 640px; FAQ 600px; About 560px.


## Page shells

Every page starts from one of these (`static/css/common/page.css`).

| Shell | Use |
|---|---|
| `.screen` (`--in-site` with the navbar) | One-screen pages: login, password, errors, payment result. Actions at the bottom on phones. |
| `.page-section` | Pages that scroll: lists, detail pages, cart, FAQ, Find Sweets, About. `--top` puts work pages close to the navbar. |
| `.page`, `--centered`, `--wide` | The column inside either shell. Carries the glow. |
| `.page--auth` | Login and the password reset pages: title, fields and button kept together as one group a little above the middle, on every screen. |
| `layouts/detail.html` | A detail page or an edit form: heading (status heading, or a hidden title on ops work pages), tabs (`page_tabs`) and at their foot Back at the left, the open tab's actions at the right. |
| `layouts/error.html` | 400/403/404/500 and similar: small grey code, title, one line, one yellow way back. |

Parts of the column: `.page__heading`, `.page__lead` (the title),
`.page__note` (small grey line), `.page__text`, `.page__message`,
`.page-part` with `.page-part__title` (a named part further down),
`.page__actions`.


## Building blocks

**Rows: `.lines`** (`static/css/common/lines.css`). The list in the calm design.
Rows divided by hairlines, nothing around them.

- `includes/ui/line.html`: a read-only line (product and an amount).
- `includes/ui/line_link.html`: the whole row is a link, with an icon in a
  tinted circle (`tone`: warning, info, success, danger, `pin`), name, meta
  and an aside. Dashboard queues, customer lists, Find Sweets.
- `line_product.html`, `line_image.html`, `line_remove.html`: cart and
  order lines.
- `.lines-total` under the lines.

**Facts: `.facts`.** Label left, value right, for dates, counts and
states. `--small` for a footnote list; `--footer` sets it off under a
hairline at the end of a page (customer detail, My account).
On customer My account, contact text and fact labels share one left edge;
icons hang in a reserved gutter inside the page. The customer name has extra
space below it. These local rules live in `public/account.css`.

**Contact: `.icon-rows`.** Email, phone and address as rows with coloured
icons; `--links` when each is one tap away. Use
`includes/ui/contact_rows.html` for someone's details and
`includes/site_contact_rows.html` for SwedeSweets' own (the one place they
are written).

**Status heading:** `includes/ui/status_heading.html`. A title with one
quiet line under it: the status in its colour, the date, who, what. Ops
work pages that open on a card (the product's) have a hidden title
instead; the card says what it is.

**Tabs with a foot:** `includes/ui/page_tabs.html` with `tabs_back_url`
(and `tabs_back_label`) and `tab_actions` (`common.page_tabs.TabAction`):
under the open tab, Back at the left and that tab's actions at the right
(the yellow one, and beside it an outline one if a tab needs two).
`layouts/detail.html` passes the page's `back_url`, so every detail page
has the Back. Back leads to the page one came from when it is this
site's and not the page itself or one under it (`back_link.js`), else to
`back_url`. The section nav stays tabs alone.

**Help:** `includes/ui/help.html`, a round "?" beside a section's title
that opens a dialog (`help_dialog.js`) with what everything there means;
its text is a template of its own. A form section takes it as `help`.

**Password once more:** `includes/ui/password_again_dialog.html` with
`accounts/password_again.py` (five wrong ones lock it for 15 minutes) for
a change that deserves a second look: changing a price already set lists
the changes and asks for the password before saving.

**List pages:** hidden title (`list_page_head.html`), then either tabs or
`includes/table/list_toolbar.html` (quick search on the left, the add
action on the right). The add action is `includes/ui/list_action.html`, the
small yellow-edged outline button with a plus.

**Catalog:** `includes/catalog/` holds the shop's and the business
portal's catalog: `grid.html` (category tabs, search, tiles), `tile.html`
(a product on the page, no card: the price on a tag on the picture's
corner, "from" the cheapest when sizes differ, and a small copy of the cart
button with how many in the other corner when the cart holds some; under the
name one row,
never more, in two halves: the size as a small dropdown ("Choose size",
then the size; sold-out sizes muted in it) or the package, then how many,
typed, no box; the themed round cart button on the label's foot,
44px. Its cart icon spins while adding, then the whole button disappears
as a green cart with a halo appears inside the label. Failure keeps the
cross and reason; the label surface stays in its theme. The row returns
after feedback, and the navbar cart catches the success after 450ms) and `no_photo.html` (in place of a missing picture: the logo's crown,
muted, and "No photo for this product") and `product.html` (a product's page in the card's
design: the picture with the price tag and in-cart badge and a round ×
above it, beside it the card's label scaled up (the name breaks as on the
card): the name on the yellow band, the category, size | how many, the
chosen size's special offer to tick, the stock, the round cart button on
its foot; Description and Ingredients under the label, as wide as it). On
the catalog a card opens its page over the wall, with its own address
(catalog.js): on a computer the label folds to its band, the picture,
tag, badge and band float to their places (a view transition) and the
label unfolds; closing is the same backwards, the wall where it was; on a phone too,
to the label over the picture's foot. Reduced motion or no view
transitions: the page just shows. The ×
above the picture goes back; there is no Back link at the foot. Over the
wall the page is moved under the body (out of the catalog's stacking
context), so it covers the footer, and ends with room under it. The wall
shows 24 cards at a time and the next 24 as one nears its foot (dots, then
the crown); all cards are in the page, so search and the categories reach
them. The channel's pages only say where the form posts and what its
button says. CSS in `static/css/public/catalog.css`.

**Status burst:** `includes/ui/status_burst.html`, rendered once in
`base.html` as a `<template>`, with `status_burst.js` (also loaded there).
While something is saved something waits in place of the controls; then a
mark says how it went, or a cross when it did not.
How it looks is two tokens in `tokens.css`: `--feedback-burst-style`
(`ring`, `dots`, or `wave`, where the logo's crown waits and its dots
move) and
`--feedback-burst-mark` (after `ring` or `dots`: `crown`, `cart` or
`check`). The dots go round at one steady speed (`--feedback-burst-cycle`)
until the answer is in, but at least `--feedback-min-loading`; then they
settle a moment (`--feedback-burst-rest`) and the mark grows, or the crown
glows, with a
soft halo of the place's colour behind it (`--status-burst-halo`). A place
gets its own look by setting the tokens on its element, at the end of
`common/status-burst.css`: the crown's wave is the default and belongs to orders; the
catalog's Add is dots then the cart; login is dots then a tick. The request
and a minimum time run side by side, so it never slows anything down. The
times (`--feedback-min-loading`, `--feedback-mark-grow`,
`--feedback-mark-hold`) are tokens too, read by the script. Used by the
catalog's green tick (the navbar cart then gives a little jump) and login.

**Submit burst:** a form that leads to the next step (Review order, Place
order, Continue to review, Pay, Order again) has `data-submit-burst`
(`submit_burst.js`, loaded on every page). When it is sent its yellow
button gives way to the same burst, in its place: the crown's wave for
`--feedback-min-loading`, then the crown settles and glows a moment, then
the form goes (the times on `.page__submit` at the end of `tokens.css`); a
second press does nothing. The next page is the real answer.

**Crown hero:** `includes/ui/crown_hero.html`, the crown large, growing in
above the title of the page that says it went through: the shop's "Thank
you for your order" and a business order just placed (the review page's
Place order lands on it with `?placed=1`).

**Tables** remain only where ops compare many columns (orders, batches,
stock). On phones they become rows (`.mobile-lines`).

**Ops work pages** (the product's page and its edit, shop text and
inventory: `products.css`, `variants.css`; the pattern for the other ops
pages to follow):

- The thing worked on is a card, edged in the accent (`.product-card`,
  `.variant-view__card`, `.variant-row__card`), its status in its top
  right corner, its picture in a circle.
- When cards have columns, heads over the first card name them (the
  card's own grid, past its edge), so the cards carry no repeated labels
  and numbers no units.
- Rows under a card's own columns that must line up across cards share
  one column width (the Inventory tab's batches: ID, best-before, in
  stock, reserved).
- What needs acting on comes first, as a red note.
- A thing's parts get their own tab when they would crowd it (Product,
  Shop text, Inventory), not when they fit.
- On a phone, columns that do not fit move to a row of their own; the
  page never scrolls sideways.

**Accordions:** `<details data-smooth data-smooth-group="…">` with
`smooth-details.js`; one open at a time per group (FAQ, dashboard queues).

**Illustrations:** line drawings inline as SVG in `includes/ui/`, drawn in
`currentColor`, `stroke-linecap/linejoin="round"`, stroke about 1.8 on a
120-wide viewBox, `aria-hidden="true"`. Placed with `.page__illustration`;
`.page__heading--illustrated` lets the content below slide over the
drawing's faded foot (Find Sweets).


## Actions

- **The action:** `button button--md button--solid button--tone-place
  page__submit`. One per page or per tab; on a page with tabs, at the
  tabs' foot with its icon (`TabAction`).
- **Secondary:** `.quiet-link`, grey, underlined on hover, with a small
  icon (`arrow-return` for Cancel/Back). Works on `<button>` too.
  `.quiet-link--danger` turns red on hover for things that cannot be undone.
- **Where:** `.page__actions.page-actions`: the yellow button, then
  `.page-actions__links` with the quiet links under it, centred. On a page
  with tabs: Back at the left of the foot, the actions at its right.
- **Back or Cancel** (`includes/ui/back_or_cancel.html`): an edit form's
  way out says Back while nothing is changed and Cancel once something
  is; both leave without asking.
- **Confirming:** destructive actions ask first with the site's own dialog
  (`data-confirm`, `data-confirm-title`; `confirm_dialog.js`,
  `confirm_action.js`), never the browser's `confirm()`.
- **Other tones** belong to ops work: pack = blue, deliver = green,
  danger = red. Outline buttons (`button--outline`) only for list "add"
  actions.
- Forms that matter warn before leaving with unsaved changes
  (`data-dirty-form`, `dirty_form.js`); one-shot posts use
  `data-submit-once`.


## Forms

- Fields through `includes/ui/form_field.html` in a `.form-grid`. Widths are
  set in the form, not the template: `set_form_field_layout(full=…,
  half=…, third=…)` (`common/form_layout.py`).
- **Yes/no choices are chips, not checkboxes:** a `ChoiceField` (or
  `TypedChoiceField`) with `RadioSelect(attrs={"class":
  "radio-chip-group"})`, e.g. Active/Inactive, Listed/Not listed. On an
  ops card a yes/no is one switch instead (`.product-tag-toggle`: green
  on, grey off): Active, Vegan, a variant's sales channels.
- **Numbers are typed, never stepped:** a text field with
  `inputmode="numeric"` (and `pattern="[0-9]*"`), no spinner arrows
  (catalog ID, quantities, weights).
- **Something switched off keeps its value:** greyed like its switch and
  read-only, still sent (a variant's price while its channel is off), so
  switching back loses nothing.
- **Edit pages:** open sections, no locks (having opened the page is the
  intent; what needs a second look asks for it); saving comes back to
  the same page. A changed field gets a dot before its label, and a tab
  holding one a dot too (`dirty_form.js`).
- A named group inside a form: a section with `.pricing-channel` and
  `.pricing-channel__title` (pricing, Find Sweets).
- Help text under the field; errors replace it, in red.
- Create forms have no visible title (the button that led there and the
  submit label say enough). Edit forms use the status heading, or on ops
  work pages a hidden title and the thing's card.
- Selects with many options use Tom Select (`data-enhanced-select`).


## Navigation and chrome

The menu's colours (navbar, phone bar, start page, login) live in the theme
palettes (`--menu-bg`, `--menu-cart-*`, `--menu-language-*`, …). Light uses
the brand blue, dark uses deep blue. Component CSS reads the same roles in both.

- **The navbar is the start page's menu in a bar:** the menu's blue with the
  cream logo, cream links, the page you are on yellow (brand-yellow) with
  the crown, which has a dark blue shadow under it as on the start page;
  a yellow line (accent-600) between it and the page; the chosen language
  filled yellow, Login outlined cream; the cart blue with a light yellow ring
  and a yellow cart, filled yellow when pointed at or open; its count
  yellow (accent-600, primary-950 text), hidden while the cart is open
  and when it is empty. The chosen language a yellow ring and yellow
  letters, the other muted (on the start page too). On a phone the
  account is its icon and a short word ("Me"). On a phone the bottom
  bar has a thin yellow edge. The cart's popover stays cream.
- **Desktop:** links in the top bar, with icons; the page you are on gets
  the crown tilted on its last letter (as on the logo and the start page),
  with no hover underline in either palette. In dark, hover and keyboard
  focus add a diffuse yellow backlight (`--menu-link-glow`), with the
  letters and icons uniformly gold. Layered text shadows let each letter emit
  light, with a wider soft spill at both ends; the active crown glows too. Active links keep the light;
  crowns retain solid ink; light keeps its text-colour feedback. The header's line (`--menu-edge`)
  is independent of the chosen link colour. On a phone the crown sits
  on the icon, the labels being too small for it.
- **Phone:** the same links as a fixed bottom bar, the same blue
  (`--site-nav-count` columns); pages leave room for it.
- **Customer pages** (shop and business portal): Catalog/Shop, Find
  Sweets, FAQ, About us. **Ops** has its own links and no footer.
- **Navbar cart** (`includes/navbar_cart.html`): a look, not a place to
  edit. Its lines are the read-only line (picture, name, grey lines, `× 2`
  on the right) with only the bin; the quantity is changed on the cart's
  page, reached by the yellow button. Something added: it jumps and
  flashes green; something taken out (a bin, in it or on the cart's
  page): the same in red.
- **Footer** (customer pages only): the name with the crown, and under
  it phone, mail, Instagram and TikTok as icons, centred. About us and
  FAQ are in the navbar, not repeated here. Quiet and small, every size
  clamped; it sits at the foot of the screen on a short page.
- **Start page** (`storefront/landing.html`, `landing.css`): the one loud
  page. Cream on the menu's blue, the logo and "Sweden’s sweetest tradition"
  alone for a moment, then a menu of the navbar's own links rises under
  them, like a game's: the crown is the cursor, tilted on the chosen
  word's last letter as on the logo; pointer, Tab or ↑↓ move it and it
  stays where it was last put (`landing.js`). Cart at the top once it holds something, login or the
  account at the bottom; no navbar, no footer, one screen, no scroll. The
  splash plays once per visit.
- **On blue** (`<body class="on-blue">`, `on-blue.css`): the ways in, the
  start page, login and the password reset, are the blue of their posts
  with cream letters, the cream logo in the middle at the top; blue is the
  door, cream is the shop. Red cannot be read on it, so problems are cream
  words with a yellow mark (accent-600). Changing the password from My
  account stays cream, inside the site.
- **Logging in** (`login.js`): the form fades, the yellow dots stand in
  its place while it is sent in the background, then the crown and the
  next page; a wrong password gives a cream cross and the form back with
  the problem above the fields.
- **Head:** favicon (the crown), Open Graph image (logo on cream). Blocks
  `meta_description`, `og_title`, `og_description`, `og_image` in
  `base.html` for pages that want their own.


## Words

- English in the templates, French in `locale/fr` (`make i18n`). Every
  user-facing string goes through `{% trans %}` or `gettext_lazy`.
  Ops pages are mostly plain English; customer pages are always translated.
- Short. A label is one or two words; a note is one sentence.
- Personal over corporate: "Come and make your own bag", not "embark on a
  flavour adventure".
- FAQ questions live in `storefront/faq.py`. An item without an answer is
  kept as a reminder and not shown. An item can add the contact rows
  (`contact=True`) or a link (`link`, `link_label`) under its answer.


## Template conventions

- Every include starts with a `{% comment %}` saying what it is and what
  context it takes. `{# #}` is single-line only (a multi-line one is printed
  on the page).
- Include with `only` and pass exactly what the part needs.
- Views hand templates frozen dataclass viewmodels, not querysets to
  format in the template.
- New CSS goes in the file that owns that part, with a comment above the
  rule saying what it is for. No inline styles except a custom property
  (`style="--site-nav-count: 4"`).


## Checklist for a new page

1. Which shell: `.screen` (fits one screen) or `.page-section` (scrolls)?
2. Does it need a visible title, or does the navigation say it?
3. What is the one yellow action? What are the quiet links? On an ops work
   page: what is the card, and what are its tabs and their actions?
4. Can the content be `.lines`, `.facts` or `.icon-rows` instead of
   something new?
5. Does every colour on it mean something from the colour table?
6. Phone: actions at the bottom, nothing wider than the screen, the
   bottom bar not covering the last row.
7. Strings translated; French added (`make i18n`).


## Not calm yet

- **About and FAQ:** structure done, personality (pictures, the founders'
  own words, their latest posts) to come.
- **The logo** uses the authentic traced SVG in `includes/ui/logo.html`.

The customer footer uses the authentic vector wordmark on one line, with the
crown above the final s in Sweets. Its wordmark, crown and links have independent
`--footer-*` theme colours. Missing product photos use a themeable SVG crown
and translated message, with independent `--catalog-placeholder-*` colours.
FAQ question colours remain independent of strong body text; hover/focus uses
solid gold question/chevron ink and the shared interaction light.

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
not cards. Each page has **one primary action** (yellow in light; navy with gold text/edge
and gold hover light in dark); secondary actions are quiet
text links, coloured by the theme. Colour is spent only where it means something (a status, a pin,
the action). Mobile first: on a phone the actions sit at the bottom, within
reach of the thumb. Words are short, and the page does not repeat what the
navigation already says.


## Principles

1. **Ordinary content stays on the page.** Group with space, hairlines and
   the glow (`.page::before`), rather than enclosing every group in a card.
   Dropdowns and dialogs are bounded surfaces; catalog labels are paper objects.
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
interactions. A shared cool near-white `--moonlight` lifts the logo above the
menu and is used for cart product names/controls, FAQ questions and shop names.
Cart quantities and primary actions use gold; removal actions use red.
The footer wordmark uses light blue (primary-200) in both themes.
Ops remains light until its work pages have been reviewed.
Theme selection and implementation details are in [CSS themes](docs/css-themes.md).

The public/B2B dark theme was approved and merged on 2026-10-18. Its palette
and interaction rules are the baseline for future pages. The full light-theme
review and dark ops rollout remain separate work; neither is implied by this
completion. Light is still the default.

The Menu (three lines; Escape opens it) holds the settings on navbar, landing
and entrance/error pages.
Language is selected through text buttons naming each language in itself
(English, Français). JavaScript fetches the server
translations and updates text in place, retaining the open Menu and
form values; the native language POST remains the fallback. The chosen language uses navy ink in light and gold
ink with a soft gold light in dark. The theme is two choices, a sun and a
moon, the chosen one filled and gold. Selection lasts for the current tab.
Staff switch sites with a house and a wrench on the Menu's first level.

Gold marks the brand, hovered/focused main actions and selected states. In the navigation (common/states.css) three
states are set per theme: by night "here" (the page you are on, what is in
use, the logo on the start page and login) is gold with its light and the
crown, the pointer (hover, focus, the choice in the Menu) is moonlight, and
the rest light blue; the navbar's logo rests light blue without its crown,
which moves to the page's link. By day both are gold, as before. The active sort heading uses a slightly deeper gold (accent-700); section tabs
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
and answers stay neutral. In the navigation (navbar, Menu, cart button and
the start page's menu) three states are set per theme in common/states.css:
by night "here" is gold with its light and the crown, the pointer moonlight,
the rest light blue (see Navigation and chrome). The chosen landing item owns
its light even when pointer input follows keyboard focus. Ready catalog cart buttons
use blue ink/edges, becoming moonlight with a cool light on hover or keyboard
focus by night. Day success feedback is green; night uses moonlight. Catalog
card hover and focused quantity/size fields share the night moonlight pointer
palette; gold marks the opened product title/frame instead.
Dropdown options pair foreground
and background colours so selected countries and variants remain readable.
Variable mappings live in [docs/css-themes.md](docs/css-themes.md).

Catalog labels use a gold title band by day and light-blue title text on a
blue surface by night. Card navigation turns the title/frame blue by day and
lights its lettering moonlight by night. The opened night product instead uses a gold title,
frame and glow. Fields keep their ordinary surface until
they receive focus. Price tags and in-cart counts use white/navy/gold by day
and blue/gold by night; badges have no hover treatment. About's polaroid
remains light with dark lettering, and photos retain their original colours.

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
| Primary action | `--action-primary-bg`, `--action-primary-text`, `--action-primary-border` | yellow in light; navy/blue in dark, gold on hover/focus |
| Links | `--color-link` | dark blue in light, light blue in dark |
| A place (pins, addresses) | `--contact-place` | brick red in light, lighter red in dark; distinct from danger |
| Brand (logo, crown) | `--color-brand-yellow`, `--color-brand-blue` | sampled from the logo |
| Status | `--color-status-{success,warning,info,danger,muted}-text` | |

Status colours mean the same everywhere:

- **Orders:** placed = amber, packed = blue, delivered = green,
  cancelled = red.
- **Stock** (`quantity-text--*`): plenty = green, running low = amber,
  low or empty = red. Catalog product detail hides healthy stock; low/empty
  stock follows its existing threshold of 10 units.
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
  (and their `min-width` complements, `768px` and so on). The customer header
  additionally widens at 1200px; catalog content keeps its own width.
- Icons: `--size-icon-sm` (1rem) in text and rows, `-md` for pins.
- The column: `.page` is 380px; `--wide` 640px; FAQ 600px; About 560px.


## Page shells

Every page starts from one of these (`static/css/common/page.css`).

| Shell | Use |
|---|---|
| `.screen` (`--in-site` with the navbar) | One-screen pages: login, password and errors. Actions at the bottom on phones. |
| `.page-section` | Pages that scroll: lists, detail pages, cart, FAQ, Find Sweets, About. `--top` puts work pages close to the navbar. |
| `.page`, `--centered`, `--wide` | The column inside either shell. Carries the glow. |
| `.page--auth` | Login and the password reset pages: title, fields and button kept together as one group a little above the middle, on every screen. |
| `layouts/detail.html` | A detail page or an edit form: heading (status heading, or a hidden title on ops work pages), tabs (`page_tabs`) and at their foot Back at the left, the open tab's actions at the right. |
| `layouts/error.html` | 400/403/404/500 and similar: small grey code, title, one line, one themed way back. |

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
(the primary action, plus an outline action if the tab needs two).
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
typed, with a quiet outlined field; the themed round cart button on the label's foot,
44px. Its cart icon spins while adding, then the whole button disappears
as a green cart with a halo appears inside the label. Failure keeps the
cross and reason; the label surface stays in its theme. The row returns
after feedback, and the navbar cart catches the success after 450ms) and `no_photo.html` (in place of a missing picture: the logo's crown,
muted, and "No photo for this product") and `product.html` (a product's page in the card's
design: the picture with the price tag and in-cart badge and a round ×
above it, beside it the card's label scaled up (the name breaks as on the
card): the name on the yellow band, the category, size | how many, the
chosen size's special offer to tick, low-stock information when needed, the round cart button on
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
(`ring`, `dots`, `wave` or `button`) and
`--feedback-burst-mark` (after `ring` or `dots`: `crown`, `cart` or
`check`). The dots go round at one steady speed (`--feedback-burst-cycle`)
until the answer is in, but at least `--feedback-min-loading`; then they
settle a moment (`--feedback-burst-rest`) and the mark grows, or the crown
glows, with a
soft halo of the place's colour behind it (`--status-burst-halo`). A place
gets its own look by setting the tokens on its element, at the end of
`common/status-burst.css` and the owning component: the crown's wave is the
default for orders; catalog Add spins the button's cart and then shows its green
cart mark; login is dots then a tick. Recent orders uses confirmed row flashes.
Unused animation ideas are preserved in `design/animations_ideas/`. The request
and a minimum time run side by side, so it never slows anything down. The
times (`--feedback-min-loading`, `--feedback-mark-grow`,
`--feedback-mark-hold`) are tokens too, read by the script. Used by catalog cart feedback (the navbar cart then gives a little jump) and login.

**Submit burst:** a form that leads to the next step (Review order, Place
order, Continue to review, Pay, Order again) has `data-submit-burst`
(`submit_burst.js`, loaded on every page). When it is sent its primary
button gives way to the same burst, in its place: the crown's wave for
`--feedback-min-loading`, then the crown settles and glows a moment, then
the form goes (timing defaults in `tokens.css`, with component overrides in `common/status-burst.css`); a
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
- **Secondary:** `.quiet-link`, theme-coloured (interactive blue in dark),
  underlined on hover unless the owning component uses shared light instead,
  with a small icon (`arrow-return` for Cancel/Back). Works on `<button>` too.
  `.quiet-link--danger` turns red on hover for things that cannot be undone.
- **Where:** `.page__actions.page-actions`: the primary button, then
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

Theme files own navigation paint (`--menu-*`, `--menu-dropdown-*`,
`--preferences-*`, `--account-menu-*`, and the `--state-*` roles with each
part's own variables). Shared component CSS owns geometry and interaction.
Detailed mappings are in [CSS themes](docs/css-themes.md).

- **Here, pointer and rest:** where you are ("here": the page's link, the
  Menu or cart on its own page, what is in use in Settings, the view you are
  in, the logo on the start page and login) is gold with its light and the
  crown; what you point at or reach with the keys is moonlight, by night
  without a crown; everything else rests light blue. The navbar's logo rests
  light blue without its crown, which moves to the page's link. An open Menu
  or cart lights its button gold without a crown (the cart keeps its count).
  By day both "here" and the pointer are gold and the rest white, with the
  same rules (the logo white without its crown in the navbar, gold with it
  on the start page and login); three lines in
  light.css (`--state-rest-ink`, `--state-here-ink`, `--state-pointer-ink`)
  change the whole navigation at once.
- **The page's parts by night** follow the same three: tabs, questions, Find
  Sweets, the catalog's cards and cart buttons, and the quantity steppers
  rest light blue, are gold where chosen, open or in use, and moonlit where
  pointed at (a stepper blinks moonlight when pressed). Primary buttons are
  gold ink and edge on the night sky; pointed at, their ink, edge and light
  turn moonlight. The FAQ's answers read in moonlight.

- **Desktop:** logo/home at the left, page navigation centred, and the cart
  and the Menu at the right in that order. The customer header can be wider
  than catalog content on large screens. Normal navigation has no hover
  underline; by night "here" is gold with glyph/icon emission and the diffuse
  halo, the pointer moonlight; only "here" gets a crown.
- **Phone:** page links live in a fixed bottom bar; dropdown icons stay at
  the top. Catalog/Shop, Find Sweets, FAQ and About are customer destinations.
  Ops has its own page links. Pages leave room under their last content for
  the bottom bar. The header edge is independent of selection (`--menu-edge`).
  The Menu and the cart open as full-height sheets below the top bar, hiding
  the covered page/footer and keeping the page's scroll position. Their
  V-shaped lower edge meets a 44px close circle. Mobile sheets use the visible
  viewport down to a small safe-area-aware bottom margin; they do not reserve
  space for the hidden bottom navbar. Long content scrolls inside that frame. On desktop they are centred
  rounded boxes over the dimmed, softly blurred page. Mobile sheets hide the
  page links; the logo and header buttons stay available, the open one lit
  gold. The close/back circle returns to the page.

- **Menu:** three lines (and "Menu" from 768px up) open a pause-menu panel
  with a fixed title. The Menu level: Profile, Order history for business
  customers, Settings ›, Log out (CSRF-protected POST) or Login, and a
  quieter Return on desktop (mobile uses the close circle); staff switch views in the top left corner ("View" over
  the house and the wrench, the current one filled). In Settings the choice
  in use is gold ("here"); the one pointed at is moonlight by night (gold with the crown by day).
  The page behind is dimmed and softly blurred. The Settings level: English/Français and the sun/moon theme (the
  chosen icon filled); ops has no theme choice. The button keeps selected
  ink, light and crown on profile/history/order-detail pages even when
  closed. Escape opens the Menu when nothing else is open, goes back from
  Settings and closes it, returning focus to the button. The arrow keys move the
  pointer as on the start page (by day the crown follows it); no focus box.
  Switching views keeps it open. Phone: the pennant
  sheet with its close circle at the tip; desktop: a centred rectangle with
  a small × in the corner. The FAQ tells customers how to find it.
- **Navbar cart:** an icon-only disclosure with editable product rows and a
  quantity stepper. The minus stops at one; a separate quiet trash removes
  the entire product row at any quantity. Desktop
  uses a compact preview with Go to cart in a centred box like the Menu's; the full cart, review and placed
  share unframed pages. Mobile hosts the full flow in the same sliding V-shaped sheet as
  the Menu, with its own scrolling content. Retail details follow
  products in the editor. B2B includes Previous orders and product search. The icon is 22px with a
  stronger stroke than the original artwork. Cart/checkout pages retain its
  selected light and count; the cart never carries a crown. AJAX refresh
  preserves selection, scroll and in-progress contact fields. Added items produce green feedback; removals use red.
  In dark this is the bouncing icon and a diffuse coloured light, without a
  circular fill.
  Light retains the filled flash. An empty cart has no count; an open one
  keeps it, including on the cart page.
- **Customer footer:** the vector wordmark and crown, phone/mail/social icons,
  with Login for guests. Signed-in identity/logout are omitted;
  My account offers a quiet Log out below Change password as well as the menu.
  The footer stays small and centred on short pages. Ops uses its own quiet footer
  with identity, personal profile and logout.
- **Landing:** the logo and tagline appear, then the menu rises beneath them.
  The chosen item follows pointer, Tab or arrow-key selection and stays at the
  last one: by night it is moonlight and the crown is on the gold logo (you
  are home); by day the crown marks the chosen item. The Menu button (and on
  wider screens a non-empty cart) sit above; Login or a protected POST Log out
  sits below.
  One screen, no navbar/footer or page scroll; the splash runs once per visit.
- **Entrances:** login/reset share the menu background and centred logo (by
  night gold with its crown: you are home), with the Menu on the right. Their field, text and error colours have independent
  entrance roles. Dark errors use orange prose and a red failure cross. Login
  feedback is dots then a tick on success; it returns the form on failure.
- **Head:** crown favicon and Open Graph logo on cream. Pages can override
  `meta_description`, `og_title`, `og_description` and `og_image` in `base.html`.


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
3. What is the one primary action? What are the quiet links? On an ops work
   page: what is the card, and what are its tabs and their actions?
4. Can the content be `.lines`, `.facts` or `.icon-rows` instead of
   something new?
5. Does every colour on it mean something from the colour table?
6. Phone: actions at the bottom, nothing wider than the screen, the
   bottom bar not covering the last row.
7. Strings translated; French added (`make i18n`).


## Cart and checkout

Retail cart and mobile sheet share `includes/cart/checkout_details.html`.
Cart panels use wider desktop product rows, with quantity controls alongside
the product. B2B
search/add options keep their compact product presentation.
Names and delivery address come first, then email, confirmation and
phone in a bounded form column. On desktop postal code takes a quarter and town three quarters.
The country stays France, matching the delivery policy. A focused input uses
`--field-focus-color` / `--field-focus-shadow`; entrance pages use their own
`--entrance-field-focus-shadow`. These shared roles apply to ordinary forms,
password fields, enhanced selects and autofill without changing their surface.

The Continue button is muted until required fields are valid and emails match;
the confirmation field accepts typing, not paste/drop. Browser feedback is
progressive enhancement: Django validates confirmation, delivery area, cart
ownership, stock and payment locks. Invalid submissions return the editable
cart with submitted values. The checkout endpoint and review/payment flow stay
in place. With JavaScript disabled the form still submits for server validation.

All three navbar disclosures shade the page beneath with `--menu-backdrop-bg`.
The page remains visible and preserves its scroll position. Mobile locks and
inerts covered content while a sheet slides down over it; changing disclosures
retracts the old sheet first. The cart scrolls inside its frame, keeping the
close button and navigation accessible.

Desktop separates its compact navbar preview from the full cart page. The
preview contains editable rows and Go to cart. Cart, review and placed sit
directly on the page with the same width and top spacing. The timeline replaces visible page
headings. Landing hides cart access on mobile; its desktop icon links to the
cart page without opening a panel.
Mobile hosts cart, review and placed in one sheet. `responsive-cart.js` moves
the same live DOM between sheet and page on viewport changes, preserving
fields and controls. The server pages/forms remain the no-JavaScript fallback.

Mobile sheets preserve their V-shaped bottom with softer joins; outlines
share the navbar's `--menu-edge`. On desktop the Menu and the cart are
rounded centred boxes with a quiet cross in the corner; on phones sliding
sheets with a close circle at the tip (the start page's Menu a centred
pennant). Outside click and Escape dismiss every panel. Desktop panels grow
naturally with their contents and use clamped spacing.
They scroll within the frame only after reaching available screen height,
with one position marker and the close control outside the scroll area.
Covered content is inert behind centred cards and mobile sheets.

In dark mode panel backgrounds match navbar/landing. Sliding sheets have a soft
light fading down from the gold top edge; centred cards omit that edge emission.
The cumulative timeline owns the flow heading.
FAQ, Previous orders and its nested order headings share
`--dropdown-title-*` roles; component aliases remain available in the themes.
Empty retail carts centre the message and keep Browse shop near the bottom,
falling back to internal scrolling when the screen is short.

Panel light follows motion: the edge and mobile timeline illuminate after the
sheet arrives, then extinguish before closing. Settings and My account omit
extra headings. Catalog images and labels keep a quiet external rim in dark.

Order progress is cumulative: Cart → Review order → Order placed. While a
forward request runs, content disappears and the existing status burst appears
centrally below the persistent timeline. The server response triggers the next
connector from left to right, a brief dot flash and a top-to-bottom content
reveal. Validation errors do not advance. Network errors offer reload without
repeating POSTs. Reduced motion skips the decorative sequence.

Completed checkout timelines retain success green. The final connector and point
arrive in gold, followed by one green confirmation pulse across the full timeline.
Only verified placed-order responses receive this state; failed/uncertain payment
returns keep their earlier stage. Reduced motion displays the final state directly.

Retail payment still redirects normally to its hosted provider; only confirmed
payment lights the final stage on return. Failed/uncertain results stay at
review. B2B reaches placed only after successful server placement. Historical
orders keep their normal detail view. The mobile review close control becomes
Back, returning to Close after placement. The navbar cart stays locked on later
pages, while an existing mobile flow stays mounted and open.

See [CSS themes](docs/css-themes.md) for roles, timings and controller ownership.

The desktop cart icon alone marks every checkout stage, including payment return
and just-placed B2B order detail. Its count remains visible; the active light stays without a crown.
The quick preview is disabled on cart as well as later stages. Mobile mounts the
existing flow in that slot, without creating another editable cart. The start
page's Menu shows its button's light but no top-edge panel emission.

`order-flow.js` and `responsive-cart.js` keep the journey section, surface and
timeline mounted across transitions. Only the editor/content below is replaced;
editor listeners initialize on that new content. Back waits for its response,
then extinguishes the connector from right to left before revealing the prior
step. All stages share the timeline's geometry; mobile placed spacing belongs
to the content below it rather than shifting the timeline.

Previous orders uses immediate row flashes and the navbar cart's green feedback
for confirmed additions. The add/repeat buttons remain visible but disabled
while awaiting a response; there is no scoop/bag burst or artificial pause.
The artwork remains in `design/animations_ideas/` for future experiments.
Clear cart asks for confirmation before its POST, then returns to the retail or
B2B catalog and shows a compact, three-second
confirmation near the cart icon. Other success/error messages retain their
normal behavior. Theme roles are documented in [CSS themes](docs/css-themes.md).

On the start page the Menu opens centred on desktop and mobile (a pennant on
phones). The Menu and the cart use centred boxes on every desktop page;
normal mobile pages keep their sliding sheets. Outside click and Escape
dismiss them. The centred panels fade/scale instead of sliding from the
navbar. An open panel lights its header button gold.

B2B quick add resolves its live form on each change/submit, so review/back and
replaced enhanced selects retain AJAX addition and reset after success.
Normal additions have no success banner. Native fallback confirmation is short
and anchored below the timeline; all flow messages render after the timeline
so they cannot move it. Previous orders, search and product rows have larger
gaps, using `--space-10`.

Checkout uses a shared 36rem column for timeline, product rows and details. Email
and confirmation share a 26rem maximum; phone uses 18rem. Names retain their
paired layout. The shared timeline leaves 40px before normal content and
placed content adds another 32px before its crown. Section gaps increase around
Your details and before actions, while field-to-field spacing stays unchanged.
Checkout primary actions fit their label with a 16rem minimum, capped by the
available width, instead of stretching across desktop rows.

Confirmed retail returns show a receipt to the owning checkout session: saved
product/variant names, quantities, price snapshots, total, delivery address and
contact details, matching the buyer mail. Other sessions still see only outcome
and order reference. Failure/uncertain outcomes never expose the receipt.
B2B placement no longer queues a redundant success banner on its placed page.

The desktop cart quick view opens as a centred box like the Menu's, titled
"Cart", with a quiet cross in the corner; a long cart scrolls inside it with
the panels' own scroll marker. It stays between 26rem and 44rem high, with a
summary row held at its bottom: the subtotal (retail) or how many products
(business) beside a smaller Go to cart; by night a fade marks the edge when
more lies below, by day a line and a soft shadow. The phone's sheet holds
the same row for the order flow's cart step. An empty cart shows the crown
in placeholder colours, "Cart is empty", and the way on. Unfinished retail
details keep their button pressable: a press dots what is missing (yellow)
or wrong (red), like ops's changed fields, and goes to the first.

## Remaining design work

Customer day section navigation uses quiet neutral lettering at rest and the
navbar's brand blue for hover, keyboard focus and the active section. There is
no blue cloud behind these tabs. Their labels gently enlarge and thicken like
the navbar's hover lettering, keeping adjacent tabs in place; the active label
keeps this emphasis. Day filter chips use muted neutral pill surfaces and the
primary action's blue/white palette when selected. Cart and Menu have more space
between them on desktop and mobile. These changes apply only to customer day
pages; the night theme and ops retain their existing appearance.

- Review the full light customer theme using the finished public structure.
- Review ops work pages before enabling their dark palette; ops remains light.
- Keep future content and photography changes separate from palette tuning.

The public/B2B dark theme, authentic vector logo, wide footer wordmark and
missing-photo treatment are complete. Their colour choices remain in the
respective theme roles. See [CSS themes](docs/css-themes.md) for implementation.

Light-theme text on yellow buttons and catalog name bands uses dark navy.
The accent scale's orange end is decorative/selection colour, not dark text
ink. FAQ and footer hover text uses dark navy on pale surfaces; the Menu is
white and gold on the navbar's blue.
Order-progress text is navy in light while its connectors/dots retain gold;
completed progress remains green in both themes.

## Customer navbar transitions

Each day navigation link owns its cloud artwork even while inactive; page
transitions only animate its visibility and size, without copying another
painted background. On phones an open cart/Menu moves its real trigger into
the header centre while the current destination fades away; closing restores
the destination and trigger. Counts, focus and live cart updates stay on the
same controls. Reduced motion shows the final positions directly.

Over the mobile catalog, a product's close link replaces the bottom navigation
at the foot of the screen. The Catalog/Shop cloud stays in the header and also
closes the product through its existing history entry, preserving filters and
scroll. Day product return controls consume the shared secondary-action roles:
pale blue fill, brand-blue ink and border, and a lighter fill on hover/focus.

The current mobile destination has larger lettering and a wider day cloud;
night uses the same larger lettering with a wider/taller gold light. The logo
keeps its own geometry. Closed day FAQ questions use the existing deep-blue
reading role (primary-950) on hover/focus so text remains legible beyond the
small blue cloud; open questions retain white. Entrance-page Menus share
landing's centred mobile pennant and scale/fade motion instead of sliding
down from the header.

Available links inside the day Menu, including its unselected language/theme
choices, share landing's pale-blue rest and white, gently enlarged pointer or
keyboard choice. Current destinations/settings keep their existing cloud
selection. The white mobile bar's engraving is generated by draw_clouds.py
with the clouds' own broken curved hatching; it has no diffuse outer shadow.

The day mobile bottom bar is white inside its clean rounded rectangle, with a
thin brand-blue outline and blue links. Fine engraved strokes shade its lower
corners and foot, leaving the reading area clear. The active destination stays
on its cloud with its crown in the header. Day product and mobile cart/Menu
close controls use quiet circles instead of clouds: muted blue with a white
cross on paper, near-white with a blue cross on the blue Menu, gold at
hover/focus. Their target is 44px. Night and ops keep their existing appearance.

By day the navbar wordmark has no cloud or crown: it rests in the same pale
blue as the links and turns white with their gentle enlargement and optical
thickening on hover/focus. Landing keeps its existing logo cloud and crown.
The gold crown marks the current navbar destination, including its centred
label on phones. Menu and cart share the links' pale rest and white pointer
colours on both landing and normal pages; their current-page clouds keep blue
ink for contrast. Repeated activation of the current navbar link releases the
same bounded candy shower and cloud hop as the landing logo, without reloading.
Normal navigation, modifier clicks and night retain their existing behaviour.

In the light customer navbar, available links rest in pale primary-50. Hover
or keyboard focus turns them white and gently thickens/enlarges the lettering
without moving adjacent links. The selected engraved cloud stays as designed.
When changing between Catalog, Find Sweets, FAQ and About, the old cloud fades
out over 160ms as the destination cloud grows over 200ms, without overshoot.
Desktop starts both on activation, before the network response; mobile keeps
the destination in its normal header position when the page arrives. Navigation
has no extra animation wait. The navbar remains in place; fresh page
content appears below it. Mobile places the active link at the header centre, on its day cloud
(or the existing night light); the other links share the bottom bar. Reduced motion shows the final state directly.
Ops keeps its work-oriented navigation. Checkout and product-detail transitions
remain their own flows; implementation and timing controls are in
[CSS themes](docs/css-themes.md#persistent-customer-navbar-and-cloud-navigation).


The day landing cloud gently sways and grows/shrinks behind the fixed logo;
shape morphing and stronger wind effects are deferred. Landing links share
the navbar's primary-50 rest, white hover and slight text growth.
Clicking the logo releases a bounded shower of engraved sweets and gives
the day cloud a small hop; keyboard and touch work too. The wordmark stays
fixed. Reduced motion uses a brief stationary fade.

Mobile panel interactions: the brand follows its link directly, without first
closing the sheet or stepping back through panel history. While typing, the
keyboard covers the lower part of the sheet rather than lifting its close
circle; tapping outside the editor dismisses its keyboard while preserving
normal control actions and Tom Select option selection. Cart Previous orders
uses a 160ms height-only disclosure, including its nested orders; FAQ and ops
retain their usual disclosure timing.


### Returning home and focused checkout navigation

The browser starts its normal destination request immediately on activation.
`home-departure.js` moves the existing brand, links, cart and Menu while that response is
pending; no second HTML request or form interception is involved. A recorded
landing layout (or an inert measurement) supplies target geometry. The next
document captures the current source rectangles and only completes remaining
travel time, sampled from the same animation clock as the captured geometry.
On departure, slogan/login and unused mobile links fade in the first 90–100ms
before the travel begins. Desktop reserves the same scrollbar gutter on landing
and entrances as on content pages, including during inert measurements. Cart and
Menu travel as whole triggers in both directions; their own panel transitions
do not compete with the journey. When the response outlasts the journey, the existing crown burst
waits on the landing surface. Reduced motion remains ordinary navigation.

On mobile only the chosen link travels to the header centre. Other links stay
out of the flight; after the top header settles, its rule draws and the bottom
navigation slides up, then the page is revealed. The real current anchor lives
inside the sticky header while mobile, using `current-nav.js`, and returns to
its original nav slot on desktop or when inactive. It does not depend on a
fixed child inside the bottom bar, so toolbar/viewport resizing cannot detach
it from the header. Normal public navigation keeps the header mounted.

A logo click fades the page onto landing while the request is already running,
then returns wordmark, selected link and cart. Crowns and clouds cannot flash
before landing is ready. Returning wordmarks use white/moonlight until arrival,
then day lettering reforms into its cloud or night lettering flickers into gold.
Night first visits share the lamp effect. Login carries its whole existing brand.
Landing shows its cart whenever it holds products, on mobile and desktop.

Cart, review and result keep their current page/sheet design. Their navbar
hides the ordinary page links, retaining the logo, Menu and the real cart
trigger centred across the viewport. Opening a mobile quick cart over a
reading page keeps that page's navigation state; the focused checkout chrome
begins when the URL actually belongs to the order flow. Continue shopping,
Back, the logo and Menu retain their existing routes. A separate checkout
page design is deferred.

The server remains authoritative for checkout validity. Expired/replaced
unpaid checkouts return to details; valid details are remembered even if the
cart is rejected, so the first step can be corrected and resubmitted without
retyping them. Validation failures do not automatically empty purchase intent.
Existing pending-payment reconciliation, cart locking and stock checks remain
in place; a payment with an unknown result must be reconciled before a fresh
attempt is allowed.


### Landing exit, catalog batches and cart rows

A landing click removes hover and commits the chosen link's active state
before departure: day blue on its cloud, night gold with its crown. The whole
link (icon, text and selection) then travels intact; other links keep navbar
rest ink. Only the wordmark changes during departure: day white, night light
blue without its crown. Once the links settle, the navbar rule draws, followed
by the page surface and a reveal from top to bottom.

The landing cart link shares that journey: wordmark to the corner, cart trigger
to the header centre, then rule and page. Returning through the current cart
trigger or the logo reverses the brand/cart flight after fading the page.
Login first folds the menu and ancillary controls towards the brand, then
carries the complete logo/cloud to its centred header. The form fades in last.
Login's cloud keeps the landing proportions at a smaller responsive size;
returning from login carries that complete brand back without reforming it. Normal navbar changes remove the crown before
the old cloud and add the new crown after its cloud. `effects.js` keeps motion
separate from palette; night celebration remains disabled and day candy rain
is unchanged. Reduced motion keeps its static alternatives.

The catalog renders twelve cards initially. Its complete text-only index
supports search/category filtering; additional card HTML and images load in
small batches as needed. Tom Select keeps its separate complete option set.
Previous/Next links provide the no-JavaScript path. Each label's lower half
is a full-area variant or quantity field; the expanded variant list keeps
the shared dropdown styling. Product-only transitions leave the navbar still.

Cart rows use portrait rectangular crops to the left of wrapped product text.
The shared catalog price tag overlays the image without an "each" suffix.
Mobile tags are centred at the image's top. Desktop page/review tags overhang
the image's right edge; navbar preview tags hang left, with about one fifth
remaining over the image and a subtle day shadow/night glow. Scroll clipping
keeps these tags from leaking below the preview's fixed summary.

On mobile a larger quantity stepper and its row amount form a centred stack
beside the product, slightly inset from the upper-right trash button. Desktop
keeps quantity, row amount and removal inline. Only current product rows grow
to the wider desktop clamp; search, Previous orders and contact fields retain
the standard content width. Review/just-placed confirmation reuse the same
product visual; historical orders retain their own layout.

Cart additions use secondary actions: pale blue with blue ink/edge by day,
stepper-blue with pale ink by night, with gold hover emphasis. The day
in-cart badge uses its separate gold information palette.
The cart close is also secondary; continuing the order remains primary.
Opening mobile cart/Menu gives the centred trigger its active cloud/halo.
The current cart icon returns to the browsing URL/scroll recorded before
entry; the lower Continue shopping action always opens Shop/Catalog. A quick
preview closes onto its underlying page. No return arrow duplicates this.

Cart row text uses the portrait height: manufacturer at the top, product name
in the middle, variant and offer information at the bottom.

All successful additions, removals and quantity changes share server-confirmed
price feedback: row amounts and subtotal make one larger hop and hold green/red before
fading to their normal ink over 850ms; refreshed fragments resume the same
timeline instead of hopping again; only the subtotal
shows a short signed change. Mobile displays the subtotal solely in its fixed
summary. Decimal arithmetic owns amounts. B2B shows a subtotal only when every
EUR price is known; otherwise it shows the product count. Failed mutations
never paint optimistic prices. Navbar cart feedback shakes and lights its
icon (day gold/night moonlight), leaving its active cloud intact.

Customer edit/onboarding and retail checkout share `.customer-form` spacing.
The native listed switch retains strict true/false validation. Edit store
marks Menu current; on mobile Save changes replaces the bottom reading links
and hides behind the software keyboard instead of lifting. Onboarding retains
the blue entrance frame; entrance primary actions share a white border.
Completed timeline steps use bright theme greens and a soft glow. Find Sweets
names/pins share hover and keyboard emphasis while addresses remain still.

### Catalog label and notification palettes

Day cards have an accent-600 name band with primary-950 text. Pointer and
keyboard navigation retain that band, changing only the title and frame to
brand blue, without an image glow or sheen. The opened day detail keeps the
same blue title and frame. Night cards use light-blue title text and a
light-blue frame around a dark-blue band; navigation changes their title
and frame to moonlight with cool light. Secondary night cart actions
share the moonlight hover/focus/pressed palette wherever they are used.

The opened night product instead has a gold title, frame and diffuse light:
this is the selected product page, rather than a hovered destination. Its
`--product-title-text`, `--product-label-border`, outline and glow roles stay
independent from the catalog's pointer palette. Form feedback keeps priority.
On opening, the clicked label retains its navigation colours through folding
and travel, then takes the detail palette on landing. Closing resets the
detail to the resting card palette before it folds and returns.

Day variant/quantity fields retain their white surface and blue values. Night
fields share the dark title surface, with blue interactive values and a
quiet divider; fixed weight and empty choices use muted neutral ink. Fields repaint only on their own
focus/open state, including product detail. Night focus uses moonlight on a
blue surface. Detail fields share one full-width layout in both themes,
including the rounded lower corners and foot around the cart button. Their
values are vertically centred, and focus paints the entire half rather than
an inset rectangle. Secondary cart buttons retain their pale-blue day surface.

Detail images stay anchored when Description/Ingredients changes height.
Vegan sits on the image in an opaque, theme-specific green badge. Categories
remain catalog filters rather than detail headings. Low stock uses the price
tag shape at the quantity side's lower edge, clear of the cart button; its
warm palette has its own roles. It straddles the quantity edge, vertically
centred on the count, with reserved room on narrow screens. These notices
do not create extra field rows.
The day detail close control rests on the page colour. Enhanced selects retain
their native option elements so variant price, stock and offer metadata
survives selection.

Price tags and in-cart badges share an information palette: white/primary-950
with a gold border by day; dark blue with lighter gold ink/edge by night. The
badge has no hover rule in either theme. Confirmed additions retain their
separate success feedback; a transient green badge is not a hover state.

`--label-band/text/border` own the card title/frame; `--catalog-fields-bg/divider`
own its fields. `--catalog-title-pointer-bg/text/border/shadow` own navigation
feedback. Price/badge roles own information independently from action buttons.
`--catalog-success-*` and the burst tokens own day confirmation feedback. Ops
is excluded. Day rendered colours are unchanged by the night refinement.

### Product image delivery

Media stays private and signed. Product URLs are reused for five minutes per
worker, well inside their one-hour signature lifetime; new/rebuilt objects
receive private five-minute browser cache headers. Existing bucket objects
retain their previous headers until rebuilt. Cart images load eagerly and
Tom Select warms only its visible options. Product transitions briefly wait
for the display image to decode. On an image error the browser fetches fresh
HTML from the existing authorised product/current page and retries once with
its current media URL. Failed retries report a path-only console diagnostic,
never a signed query. Products without an image retain their normal placeholder.
These measures cover delayed/expired media requests; production failures still
need a Network status to distinguish delivery errors from other causes.


### Compact cart metadata and night main actions

`products.presentation` shares customer variant metadata between retail and
business carts: a sole internal variant name is suppressed, food retains its
weight, and merchandise shows the chosen size without shipping weight. Variant
choices and translations are prefetched with cart rows. Retail names use the
current catalog translation too. Historical order snapshots are not rewritten.
On mobile the name moves above the controls, the stepper's top meets the name's
bottom, the row amount stays below the stepper and trash remains at the top.
The mobile cart's grid can shrink within its padded scrollport.

Night primary actions use page/entrance background with blue text/edge on a
fine-pointer desktop, moonlight at hover and gold text/edge/glow on press.
Touch uses moonlight text/edge at rest and no sticky hover enlargement/glow.
These are shared primary roles, including login, reset and business edit actions;
the entrance reads its own background but shares border and pressed roles.


### Quiet labels and uninterrupted travel

The cart trigger never carries a crown, including checkout and open previews;
its nonzero count remains visible. Crown loading and order confirmation remain
separate status components. A sole fixed weight uses neutral muted ink, while
quantity and selectable variants use blue. Night labels share one dark surface;
the catalog/detail add button supplies the filled pale-blue action and moonlight
hover. Open product titles/frames still use gold.

Returning Menu/cart triggers finish their actual translate before the old page
label fades back in. No independent timer guesses the return duration. Incoming
navigation resumes the captured remainder of the original easing curve rather
than starting a new acceleration. Page reveal is a short opacity/6px movement,
without a height-dependent clipping mask or a separate long surface pause.

Unused checkout order-list styles, the obsolete auth action selectors and the
unused cart text-inset variable are removed. Delivery heading styles remain:
checkout review and confirmation still use them.

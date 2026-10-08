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
not cards. Each page has **one yellow action**; everything else is a quiet
grey link. Colour is spent only where it means something (a status, a pin,
the action). Mobile first: on a phone the actions sit at the bottom, within
reach of the thumb. Words are short, and the page does not repeat what the
navigation already says.


## Principles

1. **No boxes.** No white cards, no yellow-topped panels, no borders around
   groups. Group with space, hairlines and the glow (`.page::before`).
2. **One yellow action per page.** The filled yellow button is "the thing to
   do here". Cancel, back, decline, remove: quiet links. If a page seems to
   need two yellow buttons, one of them is a link or belongs on another page.
3. **Colour means something.** Yellow = the action and the brand. Blue =
   links and navigation. Brick red = a place on a map. Green, amber, red,
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


## Colour

All colours are tokens in `static/css/tokens.css`. Templates and page CSS
use the semantic tokens, not hex values.

| Use | Token | Notes |
|---|---|---|
| Page background | `--color-neutral-50` (#fffaf0) | warm cream |
| Body text | `--color-neutral-900` | |
| Titles | `--color-neutral-800`, `--page-title-color` | warm near-black, not navy |
| Quiet text, notes, links | `--color-neutral-600` | |
| Hairlines | `--color-neutral-200` / `-300` | |
| The action | `--color-action-place-solid` | accent yellow at 85% |
| Links, navigation | `--color-link` (primary-700) | |
| A place (pins, addresses) | `--color-place` (#a3392c) | brick red; deliberately not the danger red |
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

Decoration (the binoculars) uses brand yellow softened with
`color-mix(… transparent)` so it never reads as a button.


## Type

- **Body:** Nunito (`--font-body`). **Headings:** Fredoka
  (`--font-heading`, weight `--font-weight-heading`, 600): round like the
  logo, so the glad voice sits in headings and everything read or filled
  in stays calm.
- Both are our own files (`static/fonts/`, `css/fonts.css`), never Google's
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
  (phone: bottom navigation, actions at the bottom), `639px`, `479px`.
- Icons: `--size-icon-sm` (1rem) in text and rows, `-md` for pins.
- The column: `.page` is 380px; `--wide` 640px; FAQ 600px; About 560px.


## Page shells

Every page starts from one of these (`static/css/page.css`).

| Shell | Use |
|---|---|
| `.screen` (`--in-site` with the navbar) | One-screen pages: login, password, errors, payment result. Actions at the bottom on phones. |
| `.page-section` | Pages that scroll: lists, detail pages, cart, FAQ, Find Sweets, About. `--top` puts work pages close to the navbar. |
| `.page`, `--centered`, `--wide` | The column inside either shell. Carries the glow. |
| `.page--auth` | Login and the password reset pages: title, fields and button kept together as one group a little above the middle, on every screen. |
| `layouts/detail.html` | A detail page or an edit form: status heading, tabs (`page_tabs`), back link. Each tab carries its own actions at its foot. |
| `layouts/error.html` | 400/403/404/500 and similar: small grey code, title, one line, one yellow way back. |

Parts of the column: `.page__heading`, `.page__lead` (the title),
`.page__note` (small grey line), `.page__text`, `.page__message`,
`.page-part` with `.page-part__title` (a named part further down),
`.page__actions`.


## Building blocks

**Rows: `.lines`** (`static/css/lines.css`). The list in the calm design.
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

**Contact: `.icon-rows`.** Email, phone and address as rows with coloured
icons; `--links` when each is one tap away. Use
`includes/ui/contact_rows.html` for someone's details and
`includes/site_contact_rows.html` for SwedeSweets' own (the one place they
are written).

**Status heading:** `includes/ui/status_heading.html`. A title with one
quiet line under it: the status in its colour, the date, who, what.

**List pages:** hidden title (`list_page_head.html`), then either tabs or
`includes/table/list_toolbar.html` (quick search on the left, the add
action on the right). The add action is `includes/ui/list_action.html`, the
small yellow-edged outline button with a plus.

**Catalog:** `includes/catalog/` holds the shop's and the business
portal's catalog: `grid.html` (category tabs, search, tiles), `tile.html`
(a product on the page, no card; the round yellow-edged "+" asks for a
quantity before it adds) and `product.html` (a product's page: picture
beside what to buy, offers as chips, Description and Ingredients as
tabs). The channel's pages only say where the form posts and what its
button says. CSS in `static/css/catalog.css`.

**Status burst:** `includes/ui/status_burst.html`, rendered once in
`base.html` as a `<template>`, with `status_burst.js` (also loaded there).
While something is saved something waits in place of the controls; then a
mark says how it went: the crown when it worked, a cross when it did not.
How the waiting looks is one token, `--feedback-burst-style` in
`tokens.css` (being tried out):
`ring` (eight dots, then the crown grows in), `wave` (the logo's crown, its
three dots growing in turn), `is_writing` (the dots hop), `color_wave` (a
colour runs through the dots), `candy` (three sweet colours). With the
crown styles, the wait ends on a whole round of the dots
(`--feedback-burst-cycle`), the dots stop and the crown stands still a
moment (`--feedback-burst-rest`), then grows a little with a glow. A
place gets its own look by setting the token on its element, at the end of
`tokens.css` (login: `ring`). The request
and a minimum time run side by side, so it never slows anything down. The
times (`--feedback-min-loading`, `--feedback-mark-grow`,
`--feedback-mark-hold`) are tokens too, read by the script. Used by the
catalog's green tick (the navbar cart then gives a little jump) and login.

**Submit burst:** a form that leads to the next step (Review order, Place
order, Continue to review, Pay, Order again) has `data-submit-burst`
(`submit_burst.js`, loaded on every page). When it is sent its yellow
button gives way to the same burst, in its place; they show at least
`--feedback-min-loading` before the form goes, and stay until the next
page arrives; a second press does nothing. No crown here: the next page is the
answer.

**Crown hero:** `includes/ui/crown_hero.html`, the crown large, growing in
above the title of the page that says it went through: the shop's "Thank
you for your order" and a business order just placed (the review page's
Place order lands on it with `?placed=1`).

**Tables** remain only where ops compare many columns (orders, batches,
stock). On phones they become rows (`.mobile-lines`).

**Accordions:** `<details data-smooth data-smooth-group="…">` with
`smooth-details.js`; one open at a time per group (FAQ, dashboard queues).

**Illustrations:** line drawings inline as SVG in `includes/ui/`, drawn in
`currentColor`, `stroke-linecap/linejoin="round"`, stroke about 1.8 on a
120-wide viewBox, `aria-hidden="true"`. Placed with `.page__illustration`;
`.page__heading--illustrated` lets the content below slide over the
drawing's faded foot (Find Sweets).


## Actions

- **The action:** `button button--md button--solid button--tone-place
  page__submit`. One per page or per tab.
- **Secondary:** `.quiet-link`, grey, underlined on hover, with a small
  icon (`arrow-return` for Cancel/Back). Works on `<button>` too.
  `.quiet-link--danger` turns red on hover for things that cannot be undone.
- **Where:** `.page__actions.page-actions`: the yellow button, then
  `.page-actions__links` with the quiet links under it, centred.
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
  "radio-chip-group"})`, e.g. Active/Inactive, Listed/Not listed.
- A named group inside a form: a section with `.pricing-channel` and
  `.pricing-channel__title` (pricing, Find Sweets).
- Help text under the field; errors replace it, in red.
- Create forms have no visible title (the button that led there and the
  submit label say enough). Edit forms use the status heading.
- Selects with many options use Tom Select (`data-enhanced-select`).


## Navigation and chrome

- **Desktop:** links in the top bar, with icons; the page you are on gets
  the crown tilted on its last letter (as on the logo and the start page),
  and the yellow underline only answers the pointer. On a phone the crown
  sits on the icon, the labels being too small for it.
- **Phone:** the same links as a fixed bottom bar
  (`--site-nav-count` columns); pages leave room for it.
- **Customer pages** (shop and business portal): Catalog/Shop, Find
  Sweets, FAQ, About us. **Ops** has its own links and no footer.
- **Footer** (customer pages only): the name with the crown, About us,
  phone, mail. Quiet.
- **Start page** (`storefront/landing.html`, `landing.css`): the one loud
  page. Cream on primary-600, the logo and "Sweden’s sweetest tradition"
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
3. What is the one yellow action? What are the quiet links?
4. Can the content be `.lines`, `.facts` or `.icon-rows` instead of
   something new?
5. Does every colour on it mean something from the colour table?
6. Phone: actions at the bottom, nothing wider than the screen, the
   bottom bar not covering the last row.
7. Strings translated; French added (`make i18n`).


## Not calm yet

- **About and FAQ:** structure done, personality (pictures, the founders'
  own words, their latest posts) to come.
- **The logo** on the start page is the PNG recoloured; a cream SVG from
  them should replace it.

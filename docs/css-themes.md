# CSS structure and themes

The visual principles and ownership overview are in [DESIGN.md](../DESIGN.md).
This file describes loading, previews and the workflow for implementation.

Status (2026-10-18): the public/B2B dark theme is approved and merged into
main. FAQ, About, Find Sweets, accounts, carts/checkout and catalog share its
finished semantic palette and interaction rules. Labels have a separate palette
per theme; photos and About's polaroid retain their own light surfaces.
Light remains the default. A full light-theme review and the dark ops rollout
are still separate work; ops is explicitly held in light mode.

## Theme controls

Each theme file opens with a short block of the choices everything else
follows; change these first, and tune a single part further down only when
it must differ:

| Control | What it sets | Day (light.css) | Night (dark.css) |
|---|---|---|---|
| `--theme-chrome-bg` | the navbar's surface, and the Menu's, start page's and login pages' around it | primary-350 | primary-950 |
| `--state-rest-ink` | everything clickable on it, at rest: text, edge and light | white | light blue (`--interactive-text`) |
| `--state-here-ink` | where you are (with the crown) | gold | gold |
| `--state-pointer-ink` | what you point at or reach with the keys | primary-950 | moonlight |
| `--theme-page-bg` | the page | cream (neutral-50) | primary-900 |
| `--state-page-rest/here/pointer-ink` | the same three on the page (tabs, questions, Find Sweets, chips) | primary-700 / 900 / 600 | as the three above |
| `--theme-sky-*` | tabs and filter chips: the word at rest, a cloud behind it and its ink pointed at and chosen, the cloud's softness (`-blur`), how far it reaches beside the word (`-reach`; the tab row keeps that much room at its ends, so the light is not cut), its size while closed (`-closed`), how far it opens when pointed at (`-peek`: a smaller look at the chosen one's sky) and how long it takes (`--sky-open-time`) | primary-950; the navbar's blue + white pointed at, + gold chosen; 6.5px; 16px; scale(.35, .6); scale(.72, .82); 280ms | (not used: the night keeps its halo, with 1.25rem of room at the row's ends) |
| `--interaction-glow-strength` | how strongly the lights shine | 1 | 0.85 |
| `--theme-action-bg`, `-edge`, `-ink`, `-pointer-ink`, `-pressed-ink` | the primary buttons' fill and edge, and the ink of their text and light | the navbar's blue, edge the same (unseen); white; gold with a gold light; gold | the night sky; gold; moonlight; gold |
| `--theme-entrance-action-bg` | the button on the blue login pages | primary-450 | (the night sky) |

The inks colour text, edges and the lights alike (a pointer's glow is made
from `--state-pointer-ink`). The crown keeps its gold (`--menu-crown`:
`--brand-crown`) whatever colour "here" takes. Ops shares light.css but not
these choices: a block at the end of light.css keeps its navbar and yellow
buttons as they were. The catalog's green add-to-cart button, the red
removal and the quantity steppers keep their own colours.

## Files

- `static/css/tokens.css`: primitive colour scales, sizes, type and timings.
- `static/css/themes/light.css`: default semantic colours and the day menu.
- `static/css/themes/dark.css`: dark palette overrides.
- `static/css/main.css`: the shared CSS imports.
- `static/css/public.css`: common plus customer pages (retail and B2B).
- `static/css/ops.css`: common plus staff work pages.
- `common/`, `public/`, `ops/`: component and page rules, grouped by owner.

`config.context_processors.static_assets` chooses the entrypoint by URL surface,
independently of the user's role. Shared account and error pages use public CSS.
FAQ and previous orders use `common/accordion.css`; neither portal depends on
FAQ's page layout. Relative font/image URLs follow their new CSS location.

`static/js/theme.js` runs before CSS and sets `data-theme` on the HTML element.
Both palettes are loaded. Preview `?theme=dark`, `?theme=light` or `?theme=auto`;
the choice lasts for this browser tab. Auto uses Paris time: light 06–22,
dark 22–06. An unknown choice falls back to light. Ops remains light until its
work pages have been checked for the dark palette.

## Here, pointer and rest (common/states.css)

The navigation has three states, set once per theme and read by every part:

- **Here**: where you are. The navbar's link for the page, the Menu or
  cart button on its own page, the Menu's link for the page, the language
  and theme in use, the view you are in, and the logo on the brand's own
  pages (the start page, login and the other entrance pages).
- **Pointer**: what you point at, or reach with the keys.
- **Rest**: everything else.

| Role | By day (light.css) | By night (dark.css) |
|---|---|---|
| `--state-rest-ink` | white | `--interactive-text` (light blue) |
| `--state-here-ink`, `-glow`, `-glow-filter`, `-text-shadow`, `-icon-filter` | gold (as before) | gold with its light |
| `--state-pointer-ink`, `-glow`, `-glow-filter`, `-text-shadow`, `-icon-filter` | gold (as before) | moonlight with a moonlit glow |
| `--state-pointer-crown-opacity` | 0: the crown marks only "here" | 0: the crown marks only "here" |

Each part has its own variables pointing at these, so one part can be tuned
without touching the rest: `--nav-link-*` (the navbar's links),
`--nav-trigger-*` (the Menu and cart buttons; `--nav-trigger-open-*` while
their panel is open: by night gold with its light but no crown, the cart's
count still beside it; on their own page they are "here" with the crown,
the cart's count stepping aside), `--nav-cart-rest-ink` (the cart button at
rest), `--logo-*` (the logo: rest,
pointer, here; `--logo-rest-crown-opacity` hides its crown in the navbar by
night, where the crown is on the page's link instead), `--menu-link-*` (the
Menu's links), `--menu-choice-*` (Settings: `-active-*` for the one in use,
`-pointer-*` for the one pointed at), `--site-switch-*` (the view switch),
`--landing-*` (the start page's menu, its Login / Log out and the logo's
halo).

By day the three inks are the source: `--state-rest-ink` (white),
`--state-here-ink` and `--state-pointer-ink` (both gold) are set at the top of
light.css's "Here, pointer and rest" block, and `--menu-ink`, `--menu-chosen`,
the cart's and Settings' hover colours and the gold glows are made from them.
Change those three lines and the whole navigation follows: navbar, Menu,
Settings, the Menu and cart buttons, the view switch, the start page's menu,
and the light behind the filter chips. The logo follows the same rules by
day as by night: resting without its crown in the navbar, the pointer's
colour when pointed at, "here" with its crown on the start page and login.
The page's own parts sit on the cream,
where those colours would not read, so their words have their own three:
`--state-page-rest-ink`, `--state-page-here-ink`, `--state-page-pointer-ink`. `common/states.css` is loaded last (public.css,
ops.css) and maps the parts onto their variables.

The page's own parts follow the same three states by night: the tabs (the
catalog's categories, /my/: `--section-nav-*`, `--section-nav-pointer-*`),
the questions (FAQ, Previous orders: rest light blue, open gold, pointed at
moonlight, `--dropdown-title-pointer-*`; the FAQ's answers moonlight without
light, `--faq-answer-text`), Find Sweets (`--find-sweets-pointer-*`), the
catalog's cards (a moonlit sheen and edge, `--catalog-card-hover-*` from
`--state-pointer-sheen` and `--state-pointer-box-glow`) and their cart
buttons (light blue, moonlight pointed at). The primary buttons are gold ink
and edge on the night sky (`--action-primary-bg`: primary-1000), and
pointed at take moonlight ink, edge and light (`--action-primary-hover-*`,
`--action-primary-shadow`). The quantity steppers have a light blue edge and
signs, moonlit signs when pointed at, a moonlit blink when pressed, and a
gold edge while in use (`--stepper-active-line`, `--stepper-pointer-ink`,
`--stepper-press-*`; the cart's own: `--cart-control-*`). By day all of
these point at what the parts had before. The order timeline keeps its own
states.

## The Menu: account, settings and the staff site switch

One button, three lines (with the word "Menu" from 768px up), opens the Menu
in the customer navbar, the start page, entrance/error pages and ops. It
replaced the gear and the person icon; the cart stays its own icon. Like a
game's pause menu, Escape opens it from anywhere nothing else is open (no
sheet, dialog, product opened over the catalog, dropdown, and not typing in
a field), and Escape closes it again.

The panel has a fixed title at the top ("MENU", or "SETTINGS") and two
levels below it, which take turns:

- **Menu:** Profile and, for business customers, Order history (with the
  crown on the one you are on); Settings ›; then a divider, Log out (a
  CSRF-protected POST) or Login for guests; and Return, quieter, at the
  bottom. Staff have their view switch in the top left corner, opposite the
  cross: "View" over a small pill with the house (public view) and the
  wrench (operations), the one they are in filled and lit; the other's name
  shows beside it on hover or focus.
- **Settings:** the language (English/Français, each in its own language;
  the existing Django POST)
  and the theme, a sun (light) and a moon (dark) as `aria-pressed` buttons,
  the chosen one filled and in the selected colour with its light. Ops has
  no theme choice and stays light. Return goes back to the Menu level.

Escape on Settings goes back to the Menu level; on the Menu level it closes
and gives focus back to the button.

Played like the start page's menu: the chosen choice has the gold and the
crown (on a language, theme or site the crown sits on its top right corner),
with no focus box around it. Pointing at a choice or focusing it makes it the
chosen one, and it stays. ↓/↑ go from row to row, ←/→ between the choices of
a row (Language, Theme), Home/End to the ends; Enter takes it. Opening
the Menu chooses its first row; back from Settings, Settings. Only the keys
put the gold on the focus: with the mouse the pointer chooses, and a
language or theme it leaves lets go. In Settings the language and theme in
use shine in moonlight by night and gold by day (`--menu-choice-active-ink`,
`--menu-choice-active-glow`), the others rest dimmed
(`--menu-choice-idle-opacity`), so the gold and the crown mean only "chosen".
Behind an open Menu or cart the page is dimmed and softly blurred
(`--menu-backdrop-bg`, `--menu-backdrop-filter`). A staff member
switching views keeps the Menu in front: the new site opens with it already
there, without its motion. Return, the cross and Back close it; closing it
on a cart page leaves the order flow as it was (its history step keeps the
address, so order-flow.js does not reload the step).
On a phone the panel is the pennant sheet under the header, its close circle
at the tip of the V; from 768px up it is a centred rectangle with a small
quiet × in its corner. Without JavaScript the panel opens as a plain
disclosure showing both levels at once; the language still posts.

By day the panel takes the menu's sky (`--account-menu-bg`, from
`--preferences-bg`), its ink white and the chosen gold, as in the navbar; by
night the dark panel roles. The cart keeps the shop's paper
(`--cart-sheet-bg`, `--cart-sheet-close-ink`).

The choice uses the existing sessionStorage preview key, survives navigation
and reload in the current tab, and overrides auto mode until explicitly
requesting `?theme=auto` again. An existing `theme` query is updated on change;
other query parameters, hashes and catalog history state are preserved.

`theme.js` owns `window.siteTheme.set(light|dark)`; `theme-switch.js` handles
the switch and synchronization with auto changes. Language retains a native form fallback; `language-switch.js` enhances it with fetch.
`includes/site_menu.html` owns the Menu, including
`includes/theme_switch.html` for customer theme choices. `common/site-menu.css`
owns the button, title, levels and links; `common/mobile-menu.css` the
sheet and the desktop rectangle (`public/landing.css` the start page's
pennant); `theme-switch.css` the theme icons. `site-menu.js` switches the
levels, the title and handles Escape; `mobile-menu.js` opens, closes and
animates; `details-popover.js` closes it on an outside click.
`--preferences-*` and `--account-menu-*` in the theme files own the colours
and shadows.

At viewport widths of 1200px and above, customer header content can grow to
1200px. Page/catalog content retains `--width-page` (1040px), its four-column
maximum and existing card widths. Ops header sizing is unchanged.

The navbar's right-hand buttons are the cart and the Menu (three lines, the
word "Menu" from 768px up), in that order: icons with transparent hit areas,
no painted circular border or background. Keyboard focus keeps a visible
outline. The cart's navbar artwork is 1.375rem with a 12-unit stroke in its
201-unit viewBox; this local override does not change cart icons elsewhere.
Both follow here, pointer and rest (above): at rest like the rest of the
navbar, the pointer's colour when pointed at, lit like "here" without a
crown while their panel is open (the cart keeps its count beside it), and
"here" with the crown on their own pages: the cart on the cart and checkout
pages (its count then steps aside), the Menu on My account, the order
history and an order's page. `config.context_processors.navigation` selects
account/profile/history versus cart/checkout destinations; catalog pages
select neither. `navbar-cart.js` keeps the current-page marker when it
replaces the cart's HTML. The customer footer omits signed-in identity and
Log out; My account has Log out below Change password; ops keeps its own
footer.


## Checks

Validation: `make lint check collectstatic`,
`DJANGO_DEBUG=True .venv/bin/python -m pytest config/tests/test_static_assets.py`,
and `node --test tools/tests/theme.test.cjs`.

## Editing a page

Keep layout, selectors, responsive rules and interaction states with the owning
component. Add a semantic colour role only when it has a distinct purpose;
reuse `--text-main`, `--text-muted`, `--page-bg`, `--surface-bg` and border roles
for ordinary content. Add its default to light.css and only its differences to
dark.css. Do not redefine the primitive colour scales to invert the page.

Paper objects are independent surfaces: `--label-*` controls the catalog's
labels, price tags and dropdowns; `--paper-*` controls the About polaroid.
Polaroid text stays dark. Dark labels use light ink on their blue surface;
light labels keep darker ink on paper. Each has its own status text roles.

The page glow, display lettering's SVG shadows, contact icons, focus states,
quantity controls and disabled controls also have theme roles. Review the
page in both themes, with open/focused/error states, on a phone and desktop.

## Verification and review scope

The completed public dark theme was reviewed in Chrome and Firefox on mobile
and desktop, including navigation, open/focused controls, catalog feedback,
account/history and cart/checkout states. Light shares layout and behaviour,
but its full palette review is still pending. Ops dark is not enabled.

The cleanup is intended to preserve rendering: compare component paint,
geometry and screenshots before/after in both palettes. The initial CSS move
was also checked against main before the later design changes. Neither check
is a claim of a loading-speed gain. Use the commands above for current test
results rather than treating an old test count as a permanent guarantee.

## Shared roles in the dark theme

`themes/dark.css` defines shared roles first, followed by component mappings.
Primitive colour scales stay in `tokens.css`. Component CSS continues to use
its existing variables; the dark theme maps those variables to shared roles.
Shared mappings make coordinated changes explicit. Light supplies the defaults;
ops currently uses those light definitions.

| Shared role | Component mappings / purpose |
| --- | --- |
| `--text-primary` | Ordinary main text and headings |
| `--text-secondary` | Body/field ink and login/reset information |
| `--text-reading` | `--prose-text`: About paragraphs and FAQ answers |
| `--text-muted` | Muted metadata and entrance help |
| `--interactive-text` | Quiet links, linked names, entrance links, closed FAQ questions and ready/pressed catalog cart ink |
| `--interactive-text-hover` | Hover/focus for quiet links, linked names and entrance links |
| `--interactive-text-subtle` | Navbar and footer links |
| `--interactive-text-strong` | General links, control accents and contact email |
| `--interactive-border` | Search focus border and catalog cart focus outline |
| `--surface-bg`, `--surface-muted` | Standard and quiet panels, including label and missing-photo backgrounds |
| `--surface-hover`, `--surface-active` | Shared field and stepper interaction backgrounds |
| `--action-primary-bg`, `--action-primary-text` | Normal filled primary button background and text |
| `--selected-accent` | Selected navigation item |
| `--color-status-success-text`, `--color-status-warning-text` | Shared green success and orange warning text |
| `--danger-text` | Strong red failure/removal feedback; general status prose retains its softer `--color-status-danger-text` |

Text roles describe importance and purpose, not font size. Gold action,
selection and decorative roles remain independent even when their primitive
colour matches. Search ink, label ink, artwork and other deliberate exceptions
keep their component-specific primitive references.

To change related interactions together, edit `--interactive-text` near the
top. To change only entrance links, edit `--entrance-link-text` in the entrance
section instead. The same pattern applies to surfaces and text. Component
variables remain available for exceptions; shared roles are not a requirement
to make every similar-looking colour identical.

Legacy names such as `--text-blue-strong` remain compatible mappings (this one
uses neutral `--text-secondary` in dark). Layout, selectors, sizes and animation
rules remain in their component files. The new shared names are defined and
consumed within the dark theme, so light does not need matching declarations.

## Editing reading text, search and FAQ colours

These roles are grouped and commented in `static/css/themes/dark.css`.
Their light defaults are in `themes/light.css`.

| Role | Used by |
|---|---|
| `--prose-text` | About paragraphs and FAQ answers; excludes question headings and photo captions |
| `--search-text` | Typed/selected text in catalog search, searchable quick jumps and B2B quick add |
| `--search-placeholder` | Hints in those search fields, including Tom Select's empty item |
| `--search-focus-border` | The catalog's inner focus ring and searchable Tom Select's active border |
| `--search-focus-bg` | Focused/open searchable Tom Select controls |
| `--search-focus-shadow` | The halo around focused/open searchable Tom Select controls |
| `--faq-question-text` | A closed FAQ question's heading |
| `--faq-question-open-text` | An open FAQ question's heading |
| `--faq-question-hover-bg` | A closed FAQ question under the pointer |
| `--faq-question-open-bg` | The open FAQ question's heading background |
| `--menu-cart-glow` | Warm shadow reused by primary actions and catalog cards/controls; navbar dropdown icons use `--menu-dropdown-*` |

The FAQ maps its roles onto the common accordion locally, so its colours do not
change Previous orders. `common/search.css` styles only actual search controls;
size and sort selects keep their component palette. The generic `--focus-ring`
continues to control other components, independently of search focus.

## Navbar separator and link hover

`--menu-edge` controls the line between the header and the page. Dark
mixes it to a muted gold (45% accent-750 into the menu blue), so the edges
frame quietly and only what is lit shines; the panels' top light keeps
accent-750 itself. Both palettes
set it explicitly, independently of `--menu-chosen`. The phone bar's outline
follows it through `--menu-bar-edge`; override that separately when needed.

Navbar links have no hover underline in either theme. `--menu-link-glow` is
`none` in light and a soft yellow radial gradient in dark; by night it lights
the current page, while hover and keyboard focus take the pointer's moonlit
glow (`--state-pointer-glow`, Here, pointer and rest). On phones the halo sits
behind the label. The current-page crown and keyboard focus outline remain visible.
This navbar effect does not change the landing menu's own animation or the
selected-language marker.

## Night lights

By night three sources light the dark palette, each a role in
`themes/dark.css` (none by day): `--landing-moon-halo`, a soft moonlight
halo round the start page's logo (the logo is the moon);
`--catalog-shelf-glow`, a faint warm light along the catalog's shelf, whose
stripes are blue at night (`--catalog-shelf-stripe`, `-alt`; yellow by day);
and `--product-label-glow`, a faint lantern light behind an opened
product's label, outside its edge only.

## Product photos and product text

`--photo-filter` (none by day; slightly dimmer and less saturated by night)
applies to product photos on cards, the product page and cart lines, so
their white backgrounds do not glare on the night palette; About's photos
keep theirs. `--product-prose-text` colours a product's Description and
Ingredients (light: body text; dark: moonlight). Catalog cards no longer
lift on hover; their shadow, sheen and name light show they open.

## FAQ, missing product photos and customer footer

These roles are defined in both theme files, next to comments describing where
only these colours apply:

| Role | Used for |
| --- | --- |
| `--faq-question-hover-text` | Closed FAQ question text on hover; separate from general strong text and open questions. |
| `--catalog-placeholder-bg` | Missing product photo background, in catalog cards and product detail. |
| `--catalog-placeholder-text` | Translatable “No photo for this product” message, independent of labels and body copy. |
| `--catalog-placeholder-crown` | Crown above that message. |
| `--footer-logo` | Customer footer wordmark. |
| `--footer-crown` | Customer footer logo's crown. |
| `--footer-link` | Footer social/contact icons and account links. |
| `--footer-link-hover` | Those links on hover and keyboard focus. |

The missing-photo artwork remains an SVG crown plus translated HTML text,
so it stays sharp, accessible and themeable without raster image variants.
Its crown is optically offset to the right; the crown/message group sits a
little lower in the image area.

The footer uses `includes/ui/logo.html` with `layout="wide"`. The original
letter paths are reused side by side, with the crown above the final s in Sweets.
Header, landing and login retain the default stacked arrangement. Footer
colours are scoped locally and do not change the menu logo.

## Catalog cart button and neutral steps

Catalog cards and product detail share `--catalog-cart-*` roles. These do not
change delivery action buttons, the navbar cart or the in-cart badge:

| Role | Used for |
| --- | --- |
| `--catalog-cart-bg` | Ready button background. |
| `--catalog-cart-ink` | Cart icon. |
| `--catalog-cart-border` | Button outline. |
| `--catalog-cart-hover-bg` | Background on hover. |
| `--catalog-cart-active-bg` | Background while pressed. |
| `--catalog-cart-focus` | Keyboard focus outline. |
| `--catalog-cart-muted-bg` | Background before choosing a size. |
| `--catalog-cart-muted-ink` | Icon before choosing a size. |
| `--catalog-cart-muted-border` | Outline before choosing a size. |

Light retains a pale green ready button. Dark uses a primary-750 fill with a moonlight icon and border,
changing to gold with the navbar cart glow on hover/focus and gold while pressed. The muted state remains clickable so it can
prompt the customer to choose a size; it is not a disabled action.

The warm neutral scale in `tokens.css` now includes every whole hundred from
100 to 900. New 400 and 500 steps bridge the existing 300 and 600; existing
primitive colours are preserved. Dark general `--text-muted` uses 400 for a
quieter grey. Page-specific text such as `--label-muted` retains its own role.
The previously undefined neutral-150 body-text reference now uses neutral-200.

The footer wordmark is 8–10rem wide. Its crown is enlarged and positioned over
the final s, at the right end of Sweets; the menu's stacked logo is unchanged.

## Catalog input, close and feedback details

- `--catalog-close-ink`, `--catalog-close-border`, `--catalog-close-bg` own
  the product-detail close button. `--catalog-close-hover-ink` and
  `--catalog-close-hover-bg` control hover. Dark uses primary-400 for the
  normal cross/edge and primary-800 behind it.
- `--catalog-cart-hover-ink` / `--catalog-cart-hover-border` and
  `--catalog-cart-active-ink` / `--catalog-cart-active-border` let the cart
  icon and edge follow interaction independently of its normal ink.
- Quantity and variant controls share a quiet full outline at rest; there is
  no quantity underline. On focus (including touch), their stronger ring,
  background and text follow the `--catalog-control-focus-*` roles, which
  default to the search focus roles and current label text.
- Label loading/success/error keep `--label-bg`. The success/error edge and
  burst use `--catalog-burst-success`, `--catalog-burst-error`, and
  `--catalog-burst-halo`. Catalog feedback uses the cart mark; recent-order additions use row flashes.
- `--cart-remove-ink`, `--cart-remove-hover-ink` and `--cart-remove-flash`
  colour the cart page/dropdown trash and row removal flash. Shared ops delete
  controls, added-row flashes, navbar cart bump and animation timings are
  unaffected.

The wide footer crown uses the original crown/letter overlap and rightward
bias as its reference, with the crown enlarged a further 20%. Its viewBox
includes the full crown so it is not clipped at the wordmark's right edge.

## Green and red primitive scales

`tokens.css` defines `--color-green-100` through `--color-green-900` and
`--color-red-100` through `--color-red-900`. Low numbers are pale; high numbers
are dark. Lightness decreases at every step, with saturation adjusted to keep
a coherent family rather than rotating through unrelated hues.

| Step | Green | Red |
| --- | --- | --- |
| 100 | `#ddf4e4` | `#fee2e2` |
| 200 | `#cdeed8` | `#fecaca` |
| 300 | `#bce5c9` | `#fca5a5` |
| 400 | `#83d9a2` | `#ec6c6c` |
| 500 | `#4bb875` | `#d94848` |
| 600 | `#248f4e` | `#a62929` |
| 700 | `#166534` | `#991b1b` |
| 800 | `#0e3f20` | `#7f1d1d` |
| 900 | `#082b15` | `#501010` |

Most steps preserve existing delivery, success, danger and removal colours.
Green 500/900 and red 900 fill gaps. Matching theme hex values now reference
these primitives without changing their rendered colour. Existing off-scale
reds and RGB channel triplets remain explicit to preserve current colours and
alpha-based effects. Themes still own semantic roles: use, for example,
`--catalog-cart-ink: var(--color-green-300)` to tune one component instead of
changing the global primitive for every consumer.

## Saved credentials and entrance errors

Autofilled `.form-field` inputs (username, password, reset email and other form
fields) keep the current theme's surface and text colour. The `:autofill` /
`:-webkit-autofill` rule paints an inset layer over the browser's protected
background and preserves the normal outer focus/error shadow. On login/reset,
focused autofill uses `--entrance-field-focus-bg` and the existing yellow ring.
Autocomplete remains enabled; no timers or JavaScript erase autofilled values.

`--entrance-error-text` and `--entrance-error-mark` control login/reset error
copy and its left edge separately from links and focus. Dark uses accent-800
for both, a deeper gold than accent-600; light keeps its previous appearance.

## Catalog feedback with the cart icon

The catalog no longer renders the decorative bag/scoop shelf above its tools.
During add, the actual submit button's cart icon spins at the former scoop's
0.55s cycle while the request is pending. There is no minimum wait or settle delay.
At the success/error mark the whole button disappears, and a green cart/halo
or the existing error cross appears inside the label. Mark growth and hold
times are unchanged; navbar cart refresh/bump still starts
450ms after the success mark. Product-detail feedback follows the same flow.
Reduced-motion disables the spin/settle motion while retaining feedback.

This is the local `--feedback-burst-style: button` / `--feedback-burst-mark:
cart` override. Other burst users keep their current styles and timings.
Success colour and halo still use `--catalog-burst-success` and
`--catalog-burst-halo` in the theme files.

## Catalog card hover and quiet controls

The card's picture gets a subtle themeable sheen and glow (gold in dark), with a 3px lift on fine
pointer hover. The product-name text brightens too. The shelf stays still.
Movement/glow is suppressed over the ordering controls, during add, and while
the card folds. Keyboard focus on the product-name link gets the same glow.
Reduced-motion removes the lift and transitions. Colours live in each theme:

| Variable | Purpose |
| --- | --- |
| `--catalog-card-hover-text` | Product-name link hover/focus text. |
| `--catalog-card-hover-sheen` | Overlay gradient over the product picture. |
| `--catalog-card-hover-shadow` | Soft glow around the picture. |
| `--catalog-control-idle-text` | Quantity and selected/placeholder variant text at rest. |
| `--catalog-control-idle-border` | Quiet full outline at rest. |
| `--catalog-control-idle-bg` | Resting field background. |
| `--catalog-control-hover-border` | Edge when pointed at. |
| `--catalog-control-focus-text` | Text when editing/selecting (defaults to label text). |
| `--catalog-control-focus-border` | Focus/open outline (defaults to search focus border). |
| `--catalog-control-focus-bg` | Focus/open background (defaults to search focus background). |
| `--catalog-control-focus-shadow` | Focus/open halo (defaults to search focus halo). |

Dark uses `--interactive-text` (primary-200) for idle quantity/variant text
and uses `--selected-accent` (accent-600) on focus/open. Light uses neutral-700 for legibility on paper.
The open variant menu retains its existing item colours; only the control
face shares these states with quantity. Native select fallback is styled too.

Standalone bag/scoop SVG snapshots and the earlier shelf animations are
preserved in `design/animations_ideas/`. Runtime template originals remain
available as unused source artwork; live feedback no longer includes them.

## Dark semantic text roles

Dark uses neutral-100 for `--text-main` (ordinary list/product text and amounts).
Linked names use `--line-link-text` (primary-200), with primary-100 hover/focus;
order-history links retain this role. Find Sweets and cart/order product names
use their component moonlight aliases instead.
Addresses and metadata keep neutral muted text.

Secondary actions use `--quiet-link-text` (primary-200) and
`--quiet-link-hover-text` / `--quiet-link-focus-text` (primary-100).
`quiet-link--clear-cart` has independent `--cart-clear-text` and
`--cart-clear-hover-text` roles: red-400 normally and on hover/focus in dark.
The modifier is applied to both cart pages and the B2B order review.

Warnings use accent-800 text and matching RGB channels `243 153 18` for
translucent backgrounds/borders. Keep these channels aligned if accent-800
changes. Catalog label status uses green-400, accent-800 and red-400, giving
success/warning/failure readable contrast on the dark label surface.

Entrance information uses `--entrance-copy-text` (neutral-200) and
`--entrance-help-text` (neutral-400). Entrance links use
`--entrance-link-text` / `--entrance-link-hover-text` (primary-200/100).
The transient failed-login cross uses `--entrance-error-icon` (red-400);
the subsequent error message retains its separate accent-800 roles.
Light supplies the original colours as defaults for these roles.

## Catalog values: editable fields, fixed weight and price

In dark, quantity and the variant picker use `--catalog-control-idle-text`,
which follows `--interactive-text` (primary-200). Their focus/open state keeps
`--catalog-control-focus-text` (`--selected-accent`), with a soft gold border
and warm outer halo. A product without a variant choice renders fixed weight instead of
a picker; it does not receive an interactive treatment.

| Role | Dark | Scope |
| --- | --- | --- |
| `--catalog-control-idle-text` | `--interactive-text` | Editable quantity and variant selector, including its caret and native fallback |
| `--catalog-control-focus-text` | `--selected-accent` | Quantity focus and focused/open variant selector |
| `--catalog-package-text` | neutral-300 | Fixed weight/package when there is no variant choice |
| `--catalog-price-text` | accent-400 | Price tag text; a deeper gold than the accent-200 label ink |

These roles apply to cards and product detail, in both retail and B2B. Light
keeps its existing appearance by mapping fixed weight and price to `--label-text`.
Other label text and status colours are unchanged. Variant list options have
their own roles, described below.

## Catalog desktop layout and variant list contrast

The wall uses auto-fill with a 13.5rem minimum card width. As available space
shrinks (including browser zoom), it drops columns before making cards narrower
than that minimum. A quarter-container minimum caps the wall at four columns,
even with smaller browser font preferences. Cards can grow into spare space.
At 479px and below, the minimum becomes 9.5rem so ordinary phones retain two
columns; very narrow viewports use one. The minimum is capped at 100% to avoid
horizontal overflow when even one full-size card cannot fit.

`--tile-min-width` in `public/catalog.css` owns this layout size. It is not a
colour role and does not belong in the theme files. Light and dark share the
same grid. There is no forced desktop column count or JavaScript zoom handler.

On desktop the product image and label occupy bounded, centred grid tracks.
The label fills its track, so unused space no longer collects at its right
edge. This applies to direct product pages and the catalog overlay.

Variant dropdown rows have separate theme roles: `--catalog-option-text`
for available rows before hover, `--catalog-option-active-text` for the
existing light active/selected backgrounds, and `--catalog-option-muted-text`
for unavailable sizes. These cover both cards and product detail and do not
change shared ops selects.

## Product title proportions and stock messages

When a catalog card opens, its name's actual text width and font size determine
the detail title size. The band padding scales with the source band. A
ResizeObserver updates the ratio after viewport/zoom changes and disconnects
when the overlay closes. Direct links retain the default detail typography.

Product detail only displays the stock line below the existing threshold of
10 units, including zero stock. Healthy stock is hidden in server-rendered
HTML as well as after choosing a variant or toggling a special offer. The
existing availability labels and ordering/stock rules are unchanged.

## Stable navbar geometry

Desktop navigation links always reserve the crown's right margin, including
inactive links. Selecting Shop, Find Sweets, FAQ or About therefore changes
colour/crown without moving neighbouring links. Phone links keep zero right
margin in their fixed grid slots.

Customer pages with a site header reserve a stable root scrollbar gutter so
the navbar and content stay aligned between short and scrolling pages, and
when the catalog overlay locks page scrolling. Entrances without a header
retain their full-width canvas. This layout behaviour is shared by both themes.

## Status table row surfaces

The shared data table uses `--table-tone-warning-bg`, `--table-tone-info-bg`,
`--table-tone-success-bg` and `--table-tone-danger-bg`, plus their corresponding
`-hover-bg` roles. Orders map placed/packed/delivered/cancelled to those tones.
These are shared table roles, so future dark ops tables can use the same
palette without order-history-specific selectors.

Dark uses `--table-tone-strength: 15%` (FAQ itself now uses only light),
and `--table-tone-hover-strength: 22%`. Placed uses accent-600 gold, packed
information blue, delivered success green and cancelled danger red. Warning
copy remains orange independently of the gold surface. Each hue has its own
role and can be tuned separately. Touch hover retains the normal background.

`--table-clickable-hover-bg` keeps the existing generic blue hover in light.
Dark clears that override (`initial`) so a clickable row uses its own status
hover role instead. Non-status rows retain the blue fallback.

Light maps the roles to the original RGB/alpha values, preserving current light
and ops appearances. Ops remains light. Mobile order history keeps its existing
line layout and coloured status icon circles; this change targets table rows.

## Local selection, sort headings and row edges

In dark, `--local-selected-accent` (accent-700) feeds active table-sort text/marker.
Section tabs instead share `--selected-accent` (accent-600) with navigation. Navbar selection and primary
actions keep their separate roles. Idle sort headings and section tabs follow
`--interactive-text`; section-tab hover uses the solid gold ink and light below. Active
sort headings stay gold on hover, with the arrow inheriting that text colour.

The component mappings are `--section-nav-text`, `--section-nav-hover-text`,
`--section-nav-active-text`, `--section-nav-marker`, `--table-sort-text`,
`--table-sort-active-text`, `--table-sort-hover-text`,
`--table-sort-active-hover-text`, `--table-sort-marker` and `--table-sort-arrow`.
`--table-row-marker` controls the clickable row's left hover edge and keyboard
focus outline; dark maps it to `--interactive-border`.

Light defines the same mappings using its previous values, preserving its
current appearance and ops. [DESIGN.md](../DESIGN.md) owns the visual principles;
this document owns variable mappings, previews and implementation details.

## Shared interaction light

The finished dark treatment has three independent layers. Their paint lives in
`themes/dark.css`; geometry and state selectors live in `common/navigation.css`,
`common/interaction-light.css` and the owning component.

| Role | Current dark value / control |
| --- | --- |
| `--selected-accent` | accent-600; solid selected/hover ink |
| `--menu-link-glow` | Radial gold stops at 0.06, 0.05 and 0.04 opacity, fading to transparent |
| `--menu-link-glow-blur` | 10px; softens the radial halo |
| `--interaction-glow-strength` | 0.85; shared dark gold emission strength without changing spread |
| `--interaction-halo-opacity` | 1; additional scaling of the broad halo for hover/focus |
| `--interaction-selected-opacity` | Follows halo opacity for selected/open states |
| `--interaction-text-shadow` | Centred 3px, 9px and 18px shadows, each at 0.15 opacity |
| `--interaction-icon-filter` | Centred 3px/0.28 and 9px/0.16 SVG drop shadows |
| `--interaction-glow-filter` | Halo blur plus lateral ±12px/4px drop shadows at 0.45 opacity |
| `--menu-crown-shadow` | Small warm emission around the current-page crown |

`--interaction-glow-strength` is 0.85 in dark (1 in light), multiplying the
base alpha values above for gold halos, letters, icons, crowns, catalog sheen
and the warm cart/action shadows. Set it to 1 to restore the previous strength.
It does not change selected ink, status feedback, blur radii or halo dimensions.
For individual changes, edit alpha in the relevant role. To change spread,
edit blur radii or lateral offsets. Text shadows follow actual glyph shapes,
including the outside letters; SVG filters follow painted icon shapes. No
per-character markup, copied text or gradient-filled glyphs is required.

Navbar and section links keep their light while current. Open FAQ titles and
chevrons emit separately, with transparent heading backgrounds. Find Sweets
shop names and pins emit independently; addresses and FAQ answers stay
neutral. The navigation's light for "here" and for the pointer is set in
`common/states.css` (Here, pointer and rest): by night the logo on the start
page and login is gold with its crown and light, and the pointer (hover,
focus, the chosen item on the start page and in the Menu) moonlight. With
`data-landing-live`, only the chosen landing item emits: moving from
keyboard to pointer input does not leave a second light behind.

`--interaction-glow` and `--interaction-glow-blur` alias the menu halo for local
components. `--menu-dropdown-*` is the day's light for the icon-only cart and
Menu buttons (`--nav-trigger-*` point at it by day). The cart and the Menu
keep their light and a crown on their own pages while closed. Crown shadows are applied to a wrapper
around the masked silhouette so their outside light is not clipped.

Light has no shared text-link halo/emission, but selected language choices and
icon dropdowns have their own subtle gold light. Forced colours hides halos
and crowns, removes emission and keeps explicit selection/focus indicators.
Reduced motion disables movement without hiding selection or feedback.

## Select contrast and catalog light

Enhanced selects, including country, use `--select-option-text`,
`--select-option-active-text/bg` and `--select-option-selected-text/bg`.
Dark active options have dark blue text on light blue; selected options have
dark blue text on pale gold. Catalog variants retain their own
`--catalog-option-*` mappings; light/ops keep the original palette.

Ready catalog cart buttons use moonlight ink/edge. Hover/focus uses
selected gold and `--catalog-cart-hover-shadow`; success feedback stays green.
`--catalog-cart-hover-border` maps directly to `--selected-accent` in dark,
independently of the navbar's icon-only cart. Card hover uses warm gold sheen
and shadow. Quantity/size fields remain blue at rest; focus/open uses selected
gold, a soft gold edge and `--catalog-control-focus-shadow`. Search keeps blue
focus. Catalog pagination has its own 350ms minimum loading time; adding a
product has no artificial minimum loading or settle delay.

## Primary action palette

Main solid place/default buttons use these shared roles:

| Role | Dark palette / purpose |
| --- | --- |
| `--action-primary-bg` | primary-800 background |
| `--action-primary-text`, `--action-primary-default-text` | selected gold text |
| `--action-primary-border` | selected gold edge |
| `--action-primary-hover-bg` | same navy background |
| `--action-primary-hover-text`, `--action-primary-hover-border` | selected gold |
| `--action-primary-active-bg/border` | pressed navy surface / gold edge |
| `--action-primary-shadow` | shared warm cart glow |
| `--action-primary-hover-transform` | small lift; no widening that clips a full-width button's edge |
| `--action-primary-text-shadow`, `--action-primary-icon-filter` | shared emission |
| `--entrance-action-primary-bg` | same navy on login/reset pages |


Light/ops retain yellow primary buttons. Green/red/status action tones keep
their palettes. Disabled solid buttons do not glow. The login/reset primary
button uses its entrance mapping without changing the action's semantics.

## Settings colours

`--preferences-option` sets available language text, `--preferences-selected`
the gold selected text, and `--preferences-selected-shadow` its emission.
`--preferences-selected-glow`, `--preferences-selected-glow-filter` and
`--preferences-selected-glow-opacity` control the halo. Hover/focus uses
`--preferences-hover` and the shared interaction shadows.
`common/language-switcher.css` reads these roles directly. In the Menu the
choice in use and the one pointed at read `--menu-choice-active-*` and
`--menu-choice-pointer-*` on top (Here, pointer and rest).

The Menu's surface, border, links, title, divider and Return read
`--account-menu-*` (`-bg`, `-border`, `-shadow` for the desktop rectangle,
`-text`, `-selected`, `-divider`); its button reads
`--preferences-trigger-ink`. The staff's view switch (the house and the
wrench in the corner) reads `--panel-chrome-ink` at rest and
`--site-switch-here-ink` / `--site-switch-pointer-ink` for the view they are
in and the one pointed at.
`accounts/account_menus.py` composes allowed destinations; templates
render those destinations and never choose links from user roles.

The theme choices (sun and moon) are language options in their colours and
light (`--preferences-option`, `--preferences-selected`); only the icons'
size lives in `common/theme-switch.css`. The language and theme in use read
`--menu-choice-active-*` ("here": gold, the others dimmed by
`--menu-choice-idle-opacity`), the one pointed at `--menu-choice-pointer-*`
(by night moonlight).

## Mobile scrollports and dropdown input

The catalog category row scrolls horizontally on phones; that scrollport also
clips vertical paint. Its top padding now reserves 24px for emitted light, with
12px of the existing search/category gap reclaimed. Do not use
`overflow-y: visible` alongside `overflow-x: auto`: browsers compute vertical
overflow as auto, so the light would remain clipped. Category widths and
horizontal scrolling are unchanged.

Dropdown triggers apply hover colour, light and movement only under
`(hover: hover) and (pointer: fine)`. Open, keyboard-focus-visible and current-page
states remain available everywhere. A touch closing a panel that is not on
its own page returns its button to rest; the Menu or cart on its own page
keeps its gold and crown.
Keyboard dismissal still restores a visible focus indicator.


## Centred cards and mobile sheets

From 768px up the Menu and the cart open as centred rounded boxes (38rem
wide; the Menu at least `--site-menu-min-height`, 31rem, so every level and
account has the same height and going into Settings does not resize it; no
edge, `--site-menu-box-bg`: by day the navbar's blue, by night the night sky
`--color-primary-1000`) over the dimmed, softly blurred page (`--menu-backdrop-bg`,
`--menu-backdrop-filter`), each with its title fixed at the top and a quiet
cross in its corner; they fade and scale in (180ms) and out (140ms). The Menu
takes its natural height, scrolling only on a short window; the cart stays
between 26rem and 44rem high and its list scrolls inside. Below 768px they
become full sheets under the header: `mobile-menu.js` measures the header and
the fixed bottom navigation, and the sheets reveal downward from the header
and retract upward. A two-layer clipped silhouette draws their V edge and the
close circle sits at its tip as a normal 44px focusable button; there is no
top border against the header. Open panels lock page scrolling and make the
covered content inert; closing restores both. Switching panels closes the
current one before revealing the next; rapid taps keep the latest choice.
Reduced motion skips the animations. Cart rows and retail contact fields
scroll within the frame, above its V and close circle.

The sun and moon say day and night through their icons and accessible
names, without a duplicate Day/Night label; the one in use is pressed and
lit. Guest footers say Login. The start page shows Login, or a protected
POST Log out when signed in, at the bottom, and the Menu button at the top
(with the cart beside it on wider screens once it holds something).

On mobile the catalog row gap is 5rem: the hanging cart clears the shelf by
about 14px. Empty catalogs reuse `catalog/no_photo.html` with the empty-catalog
message and the existing `--catalog-placeholder-*` paint. FAQ records collapse
at its start so the question/chevron light extinguishes within 100ms, before
the answer's 280ms slide ends. A fresh hover/focus can light the closed row again.

## Product close control and navbar cart feedback

The detail view's close control sits diagonally over the image's top-left
corner. Narrow phones reserve extra image gutter so its button and focus ring
stay inside the viewport; the label's proportions and type scaling are unchanged.

Navbar feedback keeps its existing jump and 1.6s duration. Light uses
`--menu-cart-feedback-animation: site-nav-cart-flash` with the original filled
flash. Dark selects `site-nav-cart-glow`: the icon becomes green-400 when adding
and red-400 when removing, with no painted circular surface or shadow around the
hit area. Separate pseudo-element/icon animations emit a blurred light and fade
back to the normal selected/hover state. The existing animation-end cleanup
accepts both theme animations, including with reduced motion.

`--menu-cart-feedback-added-ink`, `--menu-cart-feedback-removed-ink` and
`--menu-cart-feedback-count-ink` own feedback colours. Dark halo/icon emission
uses `--menu-cart-feedback-halo`, `--menu-cart-feedback-halo-filter` and
`--menu-cart-feedback-icon-filter`; their animation roles share the same 1.6s
clock. Other dropdown icons keep their current appearance.

Dropdown links extend the navigation: `--font-size-nav-link` and
`--font-weight-nav-link` are shared with the desktop navbar. Below 768px the
panels use the landing menu's Fredoka heading family/weight and
`--font-size-landing-link`, with a compact size on short landscape screens.
Language and Theme are centred groups in Settings at every width. The
Menu's links use `menu-panel-link` to reuse the nav/landing halo, glyph
emission and selected light; their colours come from `--account-menu-*`
(the panel's ink) and `--menu-link-*` (here and pointer).

On phones only (below 768px), Find Sweets, FAQ and catalog let light paint
past their `.page-section` edges. The full-width `.site-main` clips horizontal
paint at the screen edge, preventing sideways document scrolling. The catalog
category scrollport also reserves 32px of padding/negative margin on each side:
its tabs keep their positions and widths while first/last halos can cross the
content gutter. Desktop keeps its original clipping. In light, the theme
switch track follows `--menu-bg`, matching the navbar blue behind the yellow sun;
dark retains its own track role.

The stable scrollbar gutter is reserved only on desktop (768px and up).
Mobile sheets hide scrolling, so a reserved classic desktop scrollbar gutter
would otherwise leave an empty right strip when previewing a phone layout on
a large monitor. Open mobile sheets now span the full viewport, while desktop
keeps its existing stable alignment between pages.

Missing photos, empty catalogs and searches with no matches all reuse the
crown/text illustration in `catalog/no_photo.html`. Search still toggles its
hidden state as results appear/disappear; `.catalog__empty[hidden]` explicitly
wins over the illustration's grid layout. Dark crown and caption roles both
follow `--display-stamped` (currently #63718f), matching FAQ/About titles.
Light retains its own muted placeholder palette. Empty catalogs/searches paint
directly on the page; only missing product photos keep a placeholder surface.


## Editable cart and shared form focus

`common/cart-panel.css` owns the shared row geometry, responsive cart frame and
checkout section. `includes/cart/line.html` is used by both cart pages and
both navbar carts; B2B quick-add search options retain their compact layout.
The existing quantity stepper gains an opt-in trash at its minimum; other quantity controls keep their existing minimum behaviour.

| Roles | Purpose |
| --- | --- |
| `--cart-name`, `--cart-amount`, `--cart-total` | Clickable product name, ordinary amounts, subtotal |
| `--cart-row-line` | Quiet separator between cart rows and details |
| `--cart-remove-hover` | Trash at the stepper's minimum |
| `--cart-disabled-ink`, `--cart-disabled-bg`, `--cart-disabled-border` | Incomplete checkout action |
| `--menu-backdrop-bg` | Veil behind any open navbar disclosure, both viewport sizes |
| `--field-focus-color`, `--field-focus-shadow` | Border and diffuse light for focused form inputs and enhanced selects |
| `--entrance-field-focus-shadow` | Entrance form emission, following its menu accent |

Desktop has a compact quick cart (up to 38rem): product rows, quantity
steppers and Go to cart. This opens the real cart page, with contact details
below the products for retail, or Previous orders/product search for B2B.
Desktop cart, review and placed share an unframed page surface.
Both have a cumulative timeline. The full editor uses the same 36rem column as its timeline and customer details. Both
email fields share the same width; postal code uses one of four columns and town uses three. Country stays France.

On mobile, `responsive-cart.js` hosts cart, review and placed content in the
same sheet. It fetches server-rendered cart content on first opening, initializes
only explicitly marked editor scripts, and moves the live DOM between sheet
and page on viewport changes. Fields, quantity handlers and scroll survive
navbar refreshes. Mobile cart links in the shop/catalog open the sheet; desktop links navigate
to the cart page. Landing has no mobile cart icon and its desktop cart icon
always navigates directly, so no cart panel animates from the landing header. Without JavaScript these are ordinary
server pages and POST forms. Forms retain explicit action URLs.

There is one live details form, moved between the page and mobile panel.
Navbar fragments contain only preview rows; they do not construct a second
form or require field prefixes/synchronisation. `base.html` loads the shared
quantity-stepper script; public cart/catalog templates add only their own
controllers.

The Continue button requires browser-valid fields and matching emails; Django
still validates delivery, ownership, stock and payment locks. Only confirmation
blocks paste/drop. Ordinary password fields and autofill retain their behaviour.

The centred desktop boxes (the Menu, the cart) round all four corners.
Mobile sheets keep their V-shaped bottom, with rounded joins at the left and
right. Outlines reuse `--menu-edge`, the gold line beneath the navbar.
Outside click and Escape dismiss every panel. The cart's list scrolls inside
its box; the Menu grows with its contents until the viewport cap, and scrolls
only once that cap is reached.
`menu-scroll.js` shows a position thumb only when contents overflow; its theme
roles are `--menu-scroll-thumb` and `--menu-scroll-track`. Native scrollbars
remain the fallback without JavaScript.

B2B Previous orders uses `--cart-previous-text` for ready text and
`--cart-previous-active` / `--cart-previous-glow` for open, hover and focus.
These cart-scoped roles leave the ops version of Previous orders unchanged.

Dark panel surfaces now map `--preferences-bg` to `--menu-bg`, matching navbar
and landing; light keeps its existing surface. A decorative top layer uses
`--menu-panel-edge-glow` to let the gold edge fade down into the panel. Light
sets this to `none`. Cart and review use their timeline instead of a second
visible page heading. Settings and account have no extra panel heading.

FAQ and the cart's Previous orders (including each nested order) opt into
`glow-accordions`. Their common roles are defined near the start of each theme:

| Role | Controls |
| --- | --- |
| `--dropdown-title-text` | Closed heading text |
| `--dropdown-title-hover-text` | Hover/focus heading text |
| `--dropdown-title-active-text` | Open heading text |
| `--dropdown-title-glow`, `--dropdown-title-glow-filter` | Diffuse light behind the text and chevron |
| `--dropdown-title-text-shadow`, `--dropdown-title-icon-filter` | Emission from the actual letters and icon |

FAQ and cart mappings remain below these shared roles for local overrides.
The ops Previous orders does not opt into these customer accordion effects.
An empty retail panel centres its message and holds Browse shop near the lower
edge; when height is insufficient, its contents scroll above the fixed close
control on mobile; the full desktop cart uses the same empty-state layout.

`menu-scroll-ready` suppresses the native scrollbar with sufficient specificity
to win over the cart's base styles, leaving one custom position marker. Product
search results scroll only inside `.ts-dropdown-content`, not the outer dropdown
as well. Rich product name/meta/offer labels inherit their active or selected
row's contrasting text colour. In the cart, the result list flows with the
editor so its own scroll area remains reachable instead of being clipped.

## Panel light sequence and order journey

Panels start without internal emission. Once the slide (320ms) or centred-card
opening (180ms) finishes,
`mobile-menu.js` sets `data-panel-lit`; the edge, selected controls and mobile
timeline illuminate over 140ms. Closing extinguishes them before retracting
for 240ms; centred cards fade/scale out over 140ms instead. Reduced motion
skips these waits and the flow animations.

`includes/orders/progress.html` and `common/order-progress.css` show Cart →
Review order → Order placed. Reached points, labels and lines remain lit;
future steps stay blue and the current stage has `aria-current="step"`.
`order-flow.js` hides content during an opted-in submit and places the existing
status burst centrally below the persistent timeline. Only after the real
server response does the next connector illuminate left to right (450ms),
its dot flash (280ms), and new content reveal top to bottom (350ms).
Validation errors render the returned form/messages without advancing. Transport
failures restore the content and offer a GET reload: POSTs are never retried.
Browser Back/Forward and explicit edit links also fetch authoritative pages.

Retail payment submits normally to preserve hosted-provider redirects. While
leaving, the central burst waits for navigation. On verified return the journey
animates the final connector only for confirmed payment. Failed or uncertain
payments remain at review. B2B reaches placed after the server creates its
order; historical order details omit the journey unless just placed.

On mobile the sheet stays open through all stages. The close circle becomes
Back during review, then Close again after placement. Covered content is inert;
page links hide, while logo/home and header icons remain visible. The open
icon keeps gold light; the bottom close/back control remains available. Escape follows the same back/close behavior, and
cannot interrupt an in-flight submit. On desktop all stages retain the same unframed page geometry.
The navbar cart is locked on later stages; an existing mobile flow host remains
open rather than opening a second editor. Server payment locks still apply.

| Role | Purpose |
| --- | --- |
| `--order-progress-ready`, `--order-progress-lit` | Future versus reached steps and lines |
| `--order-progress-shadow`, `--order-progress-dot-shadow` | Text and point/connector emission |
| `--catalog-outline-shadow` | Quiet external rim around product image and label, separate from hover |

Light defaults the external catalog rim to transparent. Dark uses a small,
low-opacity emission based on the label border. Hover keeps its stronger role.

Customer order-history hover/focus markers use `--order-history-row-marker`,
scoped through `[data-order-history]`; ops retains its separate table marker.
The default `--status-burst-halo` is a transparent gold in both themes. Scoped
cart feedback continues to override it with green. The placed stage adds
`--space-8` above its content after the normal timeline gap, on all viewports.

The checkout shell and timeline keep their DOM identity during forward/back
transitions. `order-flow-surface` fixes equal width and padding for every stage;
only `order-flow-content` is replaced. Editor initialization belongs to the new
content node so returning to cart binds new product rows correctly. Back shrinks
the gold connector right-to-left over 450ms after the response, then reveals
its content. The timeline margin is identical for every step.

`navbar_cart_current` and `navbar_cart_locked` cover the complete journey,
including cart itself and verified placed destinations. Other header selections
are cleared. The cart count hides while its crown is current. The mobile host
can still display the existing journey, while desktop cannot open a second
quick cart. Header icons remain available when sheets open; switching to settings
or account from a directly visited mobile flow and dismissing it returns to
that flow. Requests cannot close/switch away during a pending submit.
Landing's `.menu-panel-toplight` is hidden because it has no navbar edge.

Previous-order repeat and single-line add actions no longer use a status burst
or minimum loading delay. Their buttons stay visible and disabled while the
request runs, then confirmed rows flash green and the navbar cart catches the
change. Refusals remain next to the order. The shared live burst template and
CSS no longer load scoop/bag artwork; SVG ideas remain archived.

Clear cart uses the shared confirmation dialog on retail cart, B2B cart and B2B
review, including when review is opened directly. Cancel sends no mutation;
confirmation submits the normal CSRF-protected POST once. Successful clear
redirects to the corresponding catalog; retail payment-lock errors stay on cart.
The confirmation question is translated into French.
Clear-cart success messages carry the `cart-notice` tag. The messages include
renders these as small confirmations anchored near the navbar cart, rather
than full-width banners. `cart-notice.js` follows the icon on resize/scroll and
removes the notice after about three seconds. Other messages do not expire.
Paint belongs to `--cart-notice-bg/text/border/shadow` in both themes.

The start page's Menu opens centred at every width: on a phone in the
pennant shape with its close circle at the tip, from 768px up as the
navbar's rectangle (`public/landing.css`). Its viewport covers the screen;
the backdrop dismisses on outside click, and Escape or the cross restore the
button. It fades and scales in rather than sliding from a navbar.

B2B quick-add events resolve the current form/select through document delegation,
including keyboard submit. They do not retain listeners on a replaced TomSelect
input after review/back. Previous orders and quick add each leave `--space-10`
before the following block. JSON successes only update rows and cart feedback.
Native quick-add fallback success uses `cart-flow-notice`: a three-second notice
anchored below the timeline. Other server messages on flow pages also render
inside the content after the timeline, never before its shell.

The Menu and the cart use centred rounded desktop boxes throughout the site:
a fixed title at the top (`.panel-title`), a quiet cross in the corner
(`.panel-corner-close`), each in its panel's `--panel-chrome-ink` and
`--panel-chrome-hover` (the cart's from `--cart-sheet-close-ink`,
`--cart-sheet-close-hover`; its shadow `--cart-sheet-shadow`). A long cart
scrolls inside its box with the panels' own scroll marker (menu-scroll.js).

The cart box stays between 26rem and 44rem high (less on a short window);
then its list scrolls. Its summary row is held at the bottom: the subtotal
for a retail cart, "Your order · N products" for a business order
(includes/cart/summary.html), beside a smaller Go to cart. With more below
(menu-scroll.js sets `data-more-below`), the row's edge shows:
`--cart-summary-fade` (a fade, by night), `--cart-summary-border` and
`--cart-summary-shadow` (a line and a soft shadow, by day);
`--cart-summary-label` and `--cart-summary-value` colour its text. The
phone's sheet has the same row for the order flow's cart step
(`.order-flow-summary` in the cart pages), and the page's own button for
that step steps aside there.

An empty cart (includes/cart/empty.html), in the box, the sheet and on the
cart pages, shows the crown in `--catalog-placeholder-crown` (as for a
product without a photo), "Cart is empty" in `--catalog-placeholder-text`,
and its way on below.

The retail details form keeps "Continue to review" pressable while fields
are missing (muted, `.is-incomplete`): a press marks each empty field with
a yellow dot (`--field-missing-dot`) and each filled in but wrong one with a
red dot (`--field-invalid-dot`), the same dot as ops's changed fields, and
takes the visitor to the first.
The centred boxes reach 38rem wide. The start page's Menu is centred on
mobile too (a pennant); other mobile panels keep their V-shaped sheets. The
centred boxes fade/scale; mobile sheets slide. Backdrop, close and Escape
remain.

Checkout layout lives in `public/checkout.css` and `common/cart-panel.css`:
One 36rem column for the persistent timeline, product rows and details, with
26rem email fields and 18rem phone. Checkout actions use natural
width with a 16rem minimum and more space above; existing field gaps remain.
The timeline's normal bottom gap is `--space-10`; placed content adds
`--space-8` above the crown on both desktop and mobile without moving the timeline.

The payment receipt reuses the line presentation with order snapshots and
existing text/total roles. Receipt data is supplied only for confirmed payment
in the owning session; the public return URL alone does not reveal it. The
server's redundant B2B placed success banner has been removed.

### Natural panel height

The Menu (including the start page's on mobile) uses content height with
`clamp()` spacing; its frame sets the viewport cap and it scrolls only when
it fills the available screen height. The desktop cart stays between 26rem
and 44rem high and its list scrolls inside, under its title and above its
summary row. The close control remains outside the scroll area.
The inner card padding reserves room for link halos so their pseudo-elements
do not create a small, premature scroll range. Normal mobile sheets retain
their full available height and internal scrolling.

## Moonlight and in-place language changes (2026-10-19)

Dark's `--moonlight` mixes white (85%) with primary-100 (15%). Change
this role to tune the shared cool near-white. Its component aliases are
`--menu-logo` (the navbar logo now rests light blue: `--logo-rest-ink`),
`--state-pointer-ink`, `--menu-cart-ink`, `--catalog-cart-ink/border`,
`--cart-name`, `--cart-control-ink/border`, `--find-sweets-name` and
`--faq-question-text`. Ordinary navigation remains blue. In the navigation
the pointer is moonlight and "here" gold (Here, pointer and rest); on the
page, hover and selection keep gold and its glow; success and failure remain
green/red.
`--cart-quantity-ink` and `--cart-control-active` use selected gold.
`--cart-clear-text` uses red-400. The minimum quantity's trash uses
`--cart-remove-ink`. Primary buttons use `--action-primary-*` gold ink/edge
at rest with navy fill; glow is still a hover/focus treatment.

`language-switch.js` compares a current-language server render with the
response to Django's ordinary CSRF-protected language POST. Matching text,
accessible labels, placeholders and translated data labels are updated in the
live document. Nodes, event listeners, input values, open menus, scroll and
checkout state are retained. It does not replace HTML, execute fetched scripts
or alter input values/URLs. Different-shaped subtrees and ambiguous translations
are skipped rather than paired with unrelated content; transient client-only
messages absent from the server renders are not translated. Subsequent server
responses use the selected cookie language. Network failures fall back to the
normal form POST. Theme controls resync their translated tooltip afterwards.

Catalog `.tile__status` and `.product__status` set both
`--feedback-min-loading` and `--feedback-burst-rest` to `0ms`. Actual network
requests still finish before success appears. Navbar feedback keeps its 450ms
delay after that mark; pagination and other submit feedback retain their timings.

## Completed order and cart row feedback

A verified placed order adds `.is-complete` to its timeline, including on a
normal page load. During an animated advance the connector still travels in
gold and the last point lights/blinks in gold first. The entire timeline then
changes to success green with one 460ms pulse, retaining green afterwards.
`--order-progress-complete`, `--order-progress-complete-shadow` and
`--order-progress-complete-dot-shadow` own that colour and emission. Reduced
motion skips both pulses/travel and shows the final state immediately. Failed
or uncertain payment responses retain their review state; no success is inferred
from the animation or return URL.

Product removal sets `data-confirm-tone="danger"`; the dialog uses
`--confirm-remove-text` for its title/question (red-700 in light, the darker trash ink
`--cart-remove-ink` in dark). Other confirmation/help text retains its current role.

Inside the cart panel, the inner `.order-flow-page` allows horizontal paint
overflow so added/removed row flashes reach beyond the content column. The
outer `.cart-panel-scroll` remains the single scrolling/clipping boundary;
row widths, panel geometry and the folding removal animation are unchanged.

## Light text after the accent scale update

Accent-800–950 are now luminous orange/gold, so their index no longer implies
sufficient contrast for text on pale or yellow surfaces. The scales themselves
stay intact. Light's `--color-accent-text-standard` uses primary-900; label band
names and primary action text map to that role. Default/hover action text also
aliases `--action-primary-text`, retaining navy while the fill changes.

FAQ/previous-order hover titles and footer link hover use primary-900 in
light; the Menu's links and choices are white and gold on its blue (Here,
pointer and rest).
`--display-shadow` uses neutral-600 to retain the stamped lettering's dark
inner shading without an orange cast. Dark's intentional gold selections and
orange warnings retain their roles.

`--order-progress-lit-label` separates text contrast from the gold connectors
and dots: navy on light, gold on dark; the completed state uses success green
for both. It does not change the travel/pulse sequence.

The footer wordmark uses `--footer-logo: var(--color-primary-200)` in both
themes. This is independent of the navbar/landing moonlight wordmark in dark;
the footer crown stays gold and footer link roles remain separate.

### Filter chips and status toggles

On the public and business sites the filter chips (the orders' statuses
on /my/) and the status toggles (Listed / Not listed) have no pills: only
the word. The one on is lit by a soft light behind it (by night gold,
by day dark ink with a warm light), the one pointed at by a cooler one
(by night moonlight), the rest are plain. The themes set `--chip-rest-ink`,
`--chip-here-ink`, `--chip-here-glow`, `--chip-pointer-ink`,
`--chip-pointer-glow` and take the pill away with `--chip-pill-bg`,
`--chip-pill-border` and `--chip-here-bg`; ops sets none of them and keeps
its pills.

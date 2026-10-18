# CSS structure and themes

The visual principles and ownership overview are in [DESIGN.md](../DESIGN.md).
This file describes loading, previews and the workflow for implementation.

Status (2026-10-18): the public/B2B dark theme is approved and merged into
main. FAQ, About, Find Sweets, accounts, carts/checkout and catalog share its
finished semantic palette and interaction rules. Labels have a separate palette
per theme; photos and About's polaroid retain their own light surfaces.
Light remains the default. A full light-theme review and the dark ops rollout
are still separate work; ops is explicitly held in light mode.

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

## Theme selection and shared settings

A single gear icon opens the same settings disclosure in the customer navbar,
landing and entrance/error pages, at every screen size. Language uses EN/FR
text buttons and the existing Django POST endpoint. The selected language is
gold with a soft glow inside the open panel; no radio circles are drawn.
Language submission works without JavaScript. Staff get a text link at the
bottom of settings to navigate to Public site or Ops dashboard. The navigation
builder chooses the opposite destination, including on the shared staff profile
page. Ops has no theme switch and stays light.
Logout lives in the separate account dropdown, alongside Profile and (for
business customers) Order history. It remains a CSRF-protected POST action.

The pill-shaped theme button uses `role="switch"`, a stable "Dark theme"
accessible name and `aria-checked`. In day mode its thumb is on the left and
the yellow sun on the right. In night mode the thumb moves right and the white
moon appears on the left, against the dark track. The sun sets and the moon
rises along an arc, each with a soft shadow following its shape. Reduced
motion disables the transition. The switch is hidden without JavaScript.
Escape closes the panel and restores
focus to its gear button; clicking outside closes it as well.

The choice uses the existing sessionStorage preview key, survives navigation
and reload in the current tab, and overrides auto mode until explicitly
requesting `?theme=auto` again. An existing `theme` query is updated on change;
other query parameters, hashes and catalog history state are preserved.

`theme.js` owns `window.siteTheme.set(light|dark)`; `theme-switch.js` handles
the switch and synchronization with auto changes. Language is a native form.
`includes/language_switcher.html` owns the shared panel, including
`includes/theme_switch.html` for customer theme choices. Common
`preferences.css` owns panel layout and `theme-switch.css` owns the orbit.
`--preferences-*` and `--theme-switch-*` in the theme files own their colours
and shadows. `details-popover.js` provides the existing dismissal behaviour.

At viewport widths of 1200px and above, customer header content can grow to
1200px. Page/catalog content retains `--width-page` (1040px), its four-column
maximum and existing card widths. Ops header sizing is unchanged.

Navbar cart, settings and account triggers are icons with transparent hit areas, no
painted circular border/background. Hover, keyboard focus and the open state
share gold icon emission and a halo. Keyboard focus retains a visible outline;
the cart keeps its existing add/remove feedback animation and item count.
Its navbar artwork is 1.375rem with a 12-unit stroke in its 201-unit viewBox;
this local override does not change cart icons elsewhere. The account uses
a single-person SVG and shares the dropdown emission.
`--menu-dropdown-*` roles tune this light independently of catalog buttons.

The right-hand controls appear in this order: cart, account, settings.
Guests use the same account icon with a Login-only dropdown. Signed-in users
get Profile/history/logout; My account also has Log out below Change password.
The customer footer omits signed-in identity/logout; ops keeps its own footer.
The account and cart icons retain selected ink, halo and a crown on their pages,
even while their dropdowns are closed. `config.context_processors.navigation`
selects account/profile/history versus cart/checkout destinations; catalog pages
select neither. Settings is an overlay and never claims a page selection.
The cart count moves to the opposite corner from the crown. `navbar-cart.js`
preserves the current-page marker when replacing the cart HTML via AJAX.


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

`--menu-edge` controls the line between the header and the page. Both palettes
set it explicitly, independently of `--menu-chosen`. The phone bar's outline
follows it through `--menu-bar-edge`; override that separately when needed.

Navbar links have no hover underline in either theme. `--menu-link-glow` is
`none` in light and a soft yellow radial gradient in dark, shown on hover,
keyboard focus and the current page. On phones the halo sits behind the label. The current-page crown and keyboard focus outline remain visible.
This navbar effect does not change the landing menu's own animation or the
selected-language marker.

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

Light retains a pale green ready button. Dark uses a primary-750 fill with a primary-200 icon and border,
changing to gold with the navbar cart glow on hover/focus, and blue while pressed. The muted state remains clickable so it can
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
  `--catalog-burst-halo`. Catalog feedback now uses the cart mark; other bags and recent-order
  feedback keep their existing appearance.
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
0.55s cycle, then settles from its current angle over the same 260ms rest.
At the success/error mark the whole button disappears, and a green cart/halo
or the existing error cross appears inside the label. The minimum loading,
mark growth and hold times are unchanged; navbar cart refresh/bump still starts
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
available for the other components that use them.

## Dark semantic text roles

Dark uses neutral-100 for `--text-main` (ordinary list/product text and amounts).
Linked names use `--line-link-text` (primary-200), with primary-100 hover/focus;
this includes Find Sweets, order-history links and linked cart products.
Addresses and metadata keep neutral muted text.

Secondary actions use `--quiet-link-text` (primary-200) and
`--quiet-link-hover-text` / `--quiet-link-focus-text` (primary-100).
`quiet-link--clear-cart` has independent `--cart-clear-text` and
`--cart-clear-hover-text` roles: blue normally, red-400 on hover/focus.
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

Navbar/section links keep light while current. Open FAQ titles and chevrons
emit separately, with transparent heading backgrounds. Find Sweets shop names
and pins emit independently; addresses and FAQ answers stay neutral. The login
home logo shares the navbar logo's gold hover/focus light. With
`data-landing-live`, only the chosen landing item emits: moving from keyboard
to pointer input does not leave a second light behind.

`--interaction-glow` and `--interaction-glow-blur` alias the menu halo for local
components. `--menu-dropdown-*` separately paints icon-only cart/account/settings
triggers. Current cart/account pages retain light and a crown while closed;
settings has no current-page state. Crown shadows are applied to a wrapper
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

Ready catalog cart buttons use interactive blue ink/edge. Hover/focus uses
selected gold and `--catalog-cart-hover-shadow`; success feedback stays green.
`--catalog-cart-hover-border` maps directly to `--selected-accent` in dark,
independently of the navbar's icon-only cart. Card hover uses warm gold sheen
and shadow. Quantity/size fields remain blue at rest; focus/open uses selected
gold, a soft gold edge and `--catalog-control-focus-shadow`. Search keeps blue
focus. Catalog pagination has its own 350ms minimum loading time; adding a
product retains its separate timing.

## Primary action palette

Main solid place/default buttons use these shared roles:

| Role | Dark palette / purpose |
| --- | --- |
| `--action-primary-bg` | primary-800 background |
| `--action-primary-text`, `--action-primary-default-text` | interactive blue text |
| `--action-primary-border` | interactive blue edge |
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
`common/language-switcher.css` reads these roles directly; there is no second
menu-language palette or local alias layer to override them.

Panel surface/border/gear remain independent `--preferences-*` roles.
`--account-menu-*` owns the account panel and links, including the blue Log out.
`--preferences-site-text`, `--preferences-site-hover` and
`--preferences-site-divider` paint the staff site link.
`accounts/account_menus.py` composes allowed destinations; templates
render those destinations and never choose links from user roles.

`--theme-switch-track`, `--theme-switch-border`, `--theme-switch-thumb` and
`--theme-switch-thumb-shadow` paint the pill. Sun/moon colour and shadow use
`--theme-switch-sun`, `--theme-switch-sun-glow`, `--theme-switch-moon` and
`--theme-switch-moon-glow`. Geometry and motion stay in common CSS.

## Mobile scrollports and dropdown input

The catalog category row scrolls horizontally on phones; that scrollport also
clips vertical paint. Its top padding now reserves 24px for emitted light, with
12px of the existing search/category gap reclaimed. Do not use
`overflow-y: visible` alongside `overflow-x: auto`: browsers compute vertical
overflow as auto, so the light would remain clipped. Category widths and
horizontal scrolling are unchanged.

Dropdown triggers apply hover colour, light and movement only under
`(hover: hover) and (pointer: fine)`. Open, keyboard-focus-visible and current-page
states remain available everywhere. A touch closing a non-current dropdown
returns its icon to blue; current account/cart icons keep their gold/crown.
Keyboard dismissal still restores a visible focus indicator.


## Compact dropdowns and mobile sheets

`common/preferences.css` and `common/account-menu.css` keep desktop panels at
12.5rem. `common/mobile-menu.css` turns only account/settings into a sheet
below 768px. `mobile-menu.js` measures the header and fixed bottom navigation,
locks page scrolling and makes covered content inert; closing restores both.
The sheet uses the existing preferences/account surface, border and ink roles.
A two-layer clipped silhouette draws its V edge; the close button stays a normal
44px focusable button. Reduced motion skips the entry animation. The cart has
not moved into this sheet system.

The theme pill communicates day/night through its sun/moon and accessible
switch state, without a duplicate Day/Night label. `--theme-switch-sun` uses
accent-600; the moon keeps its white emission. Guest footers say Login. Landing
shows a protected POST Log out at the bottom when signed in, with the account
icon next to settings at the top.

On mobile the catalog row gap is 5rem: the hanging cart clears the shelf by
about 14px. Empty catalogs reuse `catalog/no_photo.html` with the empty-catalog
message and the existing `--catalog-placeholder-*` paint. FAQ records collapse
at its start so the question/chevron light extinguishes within 100ms, before
the answer's 280ms slide ends. A fresh hover/focus can light the closed row again.

# CSS structure and themes

The visual principles and ownership overview are in [DESIGN.md](../DESIGN.md).
This file describes loading, previews and the workflow for implementation.

Status: structure, theme selection and a first dark palette for customer pages
are implemented. FAQ, About, Find Sweets, account pages and the shared catalog
use semantic colour roles. Labels have a separate palette in each theme;
polaroids retain dark ink on light paper.
Light remains the default; ops stays light.

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

## Verification

The initial refactor was compared to main on 26 rendered views at 390px and
1280px: no differences in the checked element positions, dimensions, font
sizes, text, background or border colours in light. The browser loaded all
CSS/fonts/images without asset errors; no horizontal overflow was found in
either theme. Dark remains a preview for visual review before making it a
user-facing default. It is not a claim of a measured loading-speed gain.

The Python suite passed (1329 tests), as did the seven standalone theme-selector
checks. Browser interactions were also exercised in dark: FAQ open/close,
focused login fields, a size dropdown with a sold-out option, adding a retail
variant, the cart quantity field and the B2B product overlay. The overlay's
paper label kept dark ink on its light background.

## Shared roles in the dark theme

`themes/dark.css` defines shared roles first, followed by component mappings.
Primitive colour scales stay in `tokens.css`. Component CSS continues to use
its existing variables; the dark theme maps those variables to shared roles.
This changes organisation without changing the rendered palette. Light and
ops retain their existing definitions.

| Shared role | Component mappings / purpose |
| --- | --- |
| `--text-primary` | Ordinary main text and headings |
| `--text-secondary` | Body/field ink and login/reset information |
| `--text-reading` | `--prose-text`: About paragraphs and FAQ answers |
| `--text-muted` | Muted metadata and entrance help |
| `--interactive-text` | Quiet links, linked names, entrance links, closed FAQ questions and catalog cart hover/press ink |
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
| `--menu-cart-glow` | The navbar cart's yellow shadow on hover, keyboard focus or while open |

The FAQ maps its roles onto the common accordion locally, so its colours do not
change Previous orders. `common/search.css` styles only actual search controls;
size and sort selects keep their component palette. The generic `--focus-ring`
continues to control other components, independently of search focus.

## Navbar separator and link hover

`--menu-edge` controls the line between the header and the page. Both palettes
set it explicitly, independently of `--menu-chosen`. The phone bar's outline
follows it through `--menu-bar-edge`; override that separately when needed.

Navbar links have no hover underline in either theme. `--menu-link-glow` is
`none` in light and a soft yellow radial gradient in dark, shown on hover and
keyboard focus. On phones the halo sits behind the label, outside its text
clipping. The current-page crown and keyboard focus outline remain visible.
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

Light retains a pale green ready button. Dark uses a primary-750 fill with a light green icon and border,
changing the icon and border to primary-200 on hover, focus and press. The muted state remains clickable so it can
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
  icon and edge follow interaction independently of its normal green ink.
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

The card's picture gets a subtle blue sheen and glow, with a 3px lift on fine
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

Dark uses accent-700 for idle quantity/variant text and restores the current
label text colour on focus. Light uses neutral-700 for legibility on paper.
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

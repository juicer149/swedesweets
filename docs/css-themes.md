# CSS structure and themes

The visual principles and ownership overview are in [DESIGN.md](../DESIGN.md).
This file describes loading, previews and the workflow for implementation.

Status: structure, theme selection and a first dark palette for customer pages
are implemented. FAQ, About, Find Sweets, account pages and the shared catalog
use semantic colour roles. Labels and polaroids retain dark ink on light paper.
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
Their text stays dark. Status text on the dark page uses brighter colours,
while light controls and labels keep their own darker ink.

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
letter paths are reused side by side, with the crown above the S in Sweets.
Header, landing and login retain the default stacked arrangement. Footer
colours are scoped locally and do not change the menu logo.

# Static asset loading audit

Baseline: `main` (before daylight-menu-theme). This document records an initial source-level audit, not a measured performance benchmark.

## Current loading

- Every page extending `templates/base.html` loads `static/css/main.css`, which imports 33 stylesheets (including the fonts, tokens, and base layers).
- The same base template globally loads the Tom Select vendor bundle, `enhanced_selects.js`, `quick_jumps.js`, `details-popover.js`, `status_burst.js`, `submit_burst.js`, and `line_flash.js`, and renders the shared status-burst fragment.
- Both the retail and B2B catalog templates extend a common base and add page-specific catalog scripts. The retail area has `templates/storefront/base.html`, but B2B and ops templates commonly extend `base.html` directly. Splitting only by template inheritance is therefore insufficient: identify the actual zone from existing routing/context or migrate template parents deliberately.
- The stylesheet imports mix shared primitives with feature-specific CSS: `dashboard.css`, `inventory.css`, `products.css`, `orders.css`, `catalog.css`, `landing.css`, `on-blue.css`, etc. This sends rules to pages that do not use them, though HTTP caching and browser parsing behavior mean a performance gain is not yet quantified.

## Proposed boundaries

1. **Core**: typography, design tokens, reset/base, shared navigation/layout, buttons, forms, reusable dialogs and UI components.
2. **Public/B2B**: landing, public catalog, customer portal, cart and checkout. Keep B2B-only ordering scripts separate from retail checkout scripts.
3. **Ops**: dashboard, product administration, inventory, order administration, ops-specific tables and forms.
4. **Page-level**: scripts/styles that are needed only for a specific view, included through explicit template blocks.

## Audit before moving code

- Build a dependency map of CSS selectors against rendered templates, JS DOM selectors, and dynamically inserted markup; a filename alone does not establish ownership.
- Inspect CSS cascade and import order, especially `responsive.css`, which currently loads last and may override multiple features.
- Inspect whether the global Tom Select library and `enhanced_selects.js` are necessary on every page, and whether any other global script has cross-page listeners or dynamic behavior.
- Keep shared UI (catalog components used by both B2B and retail, status feedback, dialogs) in core or an explicit shared bundle rather than duplicating it.
- Review the loading order and `defer` behavior of dependent scripts before relocating them.
- Audit routes and template inheritance: ops, B2B and retail do not yet each have an isolated base template.
- Ensure the daylight theme branch's `tokens.css`, navbar, landing, auth and early theme-selection script integrate cleanly **after** it is tested and merged; do not copy that unmerged work into this branch.

## Safe implementation sequence

1. Inventory asset usage and record a before baseline (network bytes/requests, transferred bytes with cold and warm cache, DOMContentLoaded and Lighthouse metrics on representative ops, B2B, retail, login pages).
2. Introduce explicit asset blocks/bundles without altering selectors or behavior; test each zone and shared login/account pages.
3. Move truly feature-specific CSS from the global import chain, preserving order and verifying responsive behavior.
4. Move global JS to zone/page templates only after checking dependencies and dynamic content.
5. Measure again, compare requests and transfer size, run CI and manually verify responsive navigation, catalog, forms, cart, ops actions, auth and translations.

## Guardrails

- No visual redesign, behavioral changes, or deletion of rules based solely on their names.
- Do not confuse fewer requests with guaranteed faster rendering: measure before claiming gains.
- Preserve shared catalog behavior between retail and B2B; preserve the distinct ops navbar and pages.
- Prefer small commits and fast-forward merges into `main` after review.

## Initial conclusion

A zone-based split is warranted for maintainability and likely avoids unnecessary CSS/JS on public pages. The exact performance impact and safe ownership of each file require a selector/dependency inventory and runtime measurements before implementation.

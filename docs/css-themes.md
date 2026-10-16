# CSS structure and themes

Status: structure, theme selection and a first dark palette for customer pages
are implemented. FAQ, About, Find Sweets, account pages and the shared catalog
use semantic colour roles. Labels and polaroids retain dark ink on light paper.
Light remains the default; ops stays light. Browser verification is in progress.

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

Validation: `make lint check collectstatic`,
`DJANGO_DEBUG=True .venv/bin/python -m pytest config/tests/test_static_assets.py`,
and `node --test tools/tests/theme.test.cjs`.

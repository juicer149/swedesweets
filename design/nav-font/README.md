# Navbar font kit

`nav-font-kit.svg` is the source of `static/fonts/swedesweets-nav.woff2`, the
typeface of the navbar's links. One cell per character the links need in
English and French, in the wordmark's own units (logo pixels).

- **Dark blue, "(logo)"**: the wordmark's own letters (S, s, w, e) or cut out
  of it (d, t). Keep them, or adjust them lightly.
- **Pale blue, "(draft)"**: I, l, i and v are made from the wordmark's T stem,
  crown dot and W; every other letter is a rough Fredoka draft. Redraw these in
  the wordmark's style.

The guides: the solid line is the baseline; dashed lines are the x-height (the
wordmark's e), the cap height (its W), the ascender (its D) and the
descender. The wordmark is close to unicase: its lower case uses capital forms
(W as w, D as d, T as t).

## Round trip through Figma

1. Import `nav-font-kit.svg` into Figma.
2. Draw inside each `g-<name>` group: any number of filled shapes; strokes are
   ignored, so outline strokes first. Leave the `cell-<name>` frames where they
   are, and keep the groups' names.
3. Export the page as SVG with **Include "id" attribute** turned on, and save it
   over `nav-font-kit.svg`.
4. `python tools/nav_font.py build` (options: `--thickness`, the navbar's stroke
   as a share of the cap height, the wordmark's is about 0.20; `--sidebearing`).

`python tools/nav_font.py kit` regenerates the kit from scratch and overwrites
your drawing, so only use it to start over.

# Wordmark font kit

`wordmark-font-kit.svg` is the source of `static/fonts/swedesweets-wordmark.woff2`,
the typeface of the Q & A and About page titles. One cell per character those
titles need in English and French, in the wordmark's own units (logo pixels).

- **Dark blue, "(logo)"**: the wordmark's own letters (s, w, W, e). Keep them,
  or adjust them lightly.
- **Pale blue, "(draft)"**: i is the wordmark's T stem and crown dot; every
  other character is a rough Fredoka draft. Redraw these in the wordmark's
  style.

The guides: the solid line is the baseline; dashed lines are the x-height (the
wordmark's e), the cap height (its W), the ascender (its D) and the
descender. The wordmark is close to unicase: its lower case uses capital forms
(W as w, D as d, T as t).

## Round trip through Figma

1. Import `wordmark-font-kit.svg` into Figma.
2. Draw inside each `g-<name>` group: any number of filled shapes; strokes are
   ignored, so outline strokes first. Leave the `cell-<name>` frames where they
   are, and keep the groups' names.
3. Export the page as SVG with **Include "id" attribute** turned on, and save it
   over `wordmark-font-kit.svg`.
4. `python tools/wordmark_font.py build` (options: `--thickness`, the stroke as a share
   of the cap height, the wordmark's is about 0.20; `--sidebearing`).

`python tools/wordmark_font.py kit` regenerates the kit from scratch and overwrites
your drawing, so only use it to start over.

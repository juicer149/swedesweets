# Animation ideas

Editable, standalone SVG snapshots of the earlier candy-bag/scoop artwork.
Open an SVG in a browser or vector editor to continue experimenting.
These files are not loaded by the live site.

- `pick-and-mix.svg`: the shelf with bags and scoops; includes the original
  sway/breathe animations and reduced-motion handling.
- `scoop.svg`: the loading scoop artwork.
- `bag.svg`: the paper bag artwork.

The SVG geometry is preserved from `templates/includes/ui/`. The shelf and
bag reference `../../static/images/swedesweets-logo.png`, so keep the repo
layout when opening them. Runtime template originals are retained because
other feedback components may still use them. Catalog add feedback uses the
spinning cart button and the green cart mark instead.

The former scoop spin was 0.55s per revolution, followed by a 260ms settling
transition. The shelf animations are 4.5s (scoops) and 5s (bags).

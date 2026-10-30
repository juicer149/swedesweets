"""A typeface for page titles, drawn from the SwedeSweets wordmark.

    python tools/wordmark_font.py kit     # writes design/wordmark-font/wordmark-font-kit.svg
    python tools/wordmark_font.py build   # kit -> static/fonts/swedesweets-wordmark.woff2

The wordmark (static/images/swedesweets-logo.svg) is the model: "Swede
Sweets" uses capital-shaped letters for the lower case (W as w, D as d, T as
t), so the face is close to unicase. `kit` lays out one cell per character
the titles need (the Q & A and About page titles, English and French), in the wordmark's own units
(logo pixels), ready to open in Figma:

  * s, w, W, e: the wordmark's own paths, untouched;
  * i: the wordmark's T stem with one of its crown's dots;
  * every other letter: a rough draft (Fredoka, narrowed to the wordmark's
    proportions) in a paler blue, to redraw in the wordmark's style.

Each cell holds a group `g-<name>` (the glyph: draw anything inside it, any
number of shapes), a frame `cell-<name>` and guide lines. Keep the frames
where they are; the baseline is the solid line. In Figma, export the page as
SVG with "Include id attribute" on, save it over the kit, then run `build`:
it reads each `g-<name>`, sets the stroke weight (--thickness) and writes
the font. Spacing is automatic (ink width plus
--sidebearing on each side); there is no kerning.

Needs fonttools (with brotli), Pillow, numpy, scipy and scikit-image
(development only; the site just serves the .woff2). Fredoka is SIL OFL
(see static/fonts/SwedeSweetsWordmark-OFL.txt).
"""

from __future__ import annotations

import argparse
import math
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.transform import Transform
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from skimage import draw as skdraw
from skimage import measure

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "static" / "images" / "swedesweets-logo.svg"
FREDOKA = ROOT / "static" / "fonts" / "fredoka.woff2"
KIT = ROOT / "design" / "wordmark-font" / "wordmark-font-kit.svg"
OUT = ROOT / "static" / "fonts" / "swedesweets-wordmark.woff2"
SVGNS = "http://www.w3.org/2000/svg"

# The characters the titles use, in English and French: "Q & A" / "Q & R"
# (set in lower case by the CSS) and "Who we are?" / "Qui sommes-nous ?". Add a character here and run
# `kit` (which starts the drawing over) to get a cell for it.
CHARS = "AQRW" "aehimnoqrsuw" "&?-"
SPECIAL = {"À": "Agrave", "ù": "ugrave", "&": "ampersand", "?": "question", "-": "hyphen"}

# Metrics, in the wordmark's units (logo pixels), measured on it.
CAP = 715  # W
XH = 679  # e
ASC = 760  # D and the S
DESC = 250
STROKE = 140  # the wordmark's typical stroke (S 136, e 132, W 193)
# The drafts' lower case is as tall as the capitals and the & (full unicase,
# like the wordmark's w), with short ascenders.
XH_DRAFT = 725  # the &'s height
ASC_DRAFT = XH_DRAFT + 70

# Kit layout.
CW, CH, BASE, LEFT, COLS = 1200, 1600, 1150, 150, 7
EXACT, DRAFT = "#2669FF", "#9DB7FF"


def gname(ch: str) -> str:
    if ch in SPECIAL:
        return ("upper-" if ch.isupper() else "lower-") + SPECIAL[ch] if ch.isalpha() else SPECIAL[ch]
    return ("upper-" if ch.isupper() else "lower-") + ch


# -- geometry -----------------------------------------------------------------


class FlatPen(BasePen):
    """Collects contours as polylines (curves flattened)."""

    def __init__(self):
        super().__init__(None)
        self.contours, self.cur = [], []

    def _moveTo(self, p):
        self._flush()
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 13)[1:]:
            u = 1 - t
            self.cur.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                             u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 9)[1:]:
            u = 1 - t
            self.cur.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                             u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        self._flush()

    _endPath = _closePath

    def _flush(self):
        if len(self.cur) > 2:
            self.contours.append(np.array(self.cur, float))
        self.cur = []


def rasterize(contours, scale, x0, y0, w, h):
    """Nonzero fill of contours (units) into a w x h bool mask: px = (u - x0) * scale."""
    wind = np.zeros((h, w), np.int16)
    for c in contours:
        cols = (c[:, 0] - x0) * scale
        rows = (c[:, 1] - y0) * scale
        area = 0.5 * np.sum(cols * np.roll(rows, -1) - np.roll(cols, -1) * rows)
        rr, cc = skdraw.polygon(rows, cols, (h, w))
        wind[rr, cc] += 1 if area > 0 else -1
    return wind != 0


def trace(mask, scale, x0, y0, tol=0.45):
    """Bool mask -> polygons in units (inverse of rasterize)."""
    out = []
    padded = np.pad(mask, 1)
    for c in measure.find_contours(padded.astype(float), 0.5):
        a = measure.approximate_polygon(c, tol)
        if len(a) > 1 and np.allclose(a[0], a[-1]):
            a = a[:-1]
        if len(a) < 3:
            continue
        out.append(np.stack([(a[:, 1] - 1) / scale + x0, (a[:, 0] - 1) / scale + y0], 1))
    return out


def nesting(polys):
    return [sum(1 for j, q in enumerate(polys) if j != i and measure.points_in_poly(p[:1], q)[0])
            for i, p in enumerate(polys)]


def on_curve(p):
    n, flags = len(p), []
    for i in range(n):
        v1, v2 = p[i] - p[i - 1], p[(i + 1) % n] - p[i]
        flags.append(abs(math.degrees(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1 @ v2))) > 40)
    return flags


def segments(p):
    """Quadratic B-spline segments of a polygon: [('M', pt), ('L', pt) | ('Q', [offs], pt)]."""
    pts = [tuple(map(float, q)) for q in p]
    flags, n = on_curve(p), len(p)
    if not any(flags):  # all control points: start at a midpoint
        mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        segs, start = [("M", mid(pts[-1], pts[0]))], mid(pts[-1], pts[0])
        for i in range(n):
            segs.append(("Q", [pts[i]], mid(pts[i], pts[(i + 1) % n]) if i < n - 1 else start))
        return segs
    i0 = flags.index(True)
    seq = [(pts[(i0 + k) % n], flags[(i0 + k) % n]) for k in range(n)] + [(pts[i0], True)]
    segs, run = [("M", seq[0][0])], []
    for pt, on in seq[1:]:
        if on:
            segs.append(("Q", run, pt) if run else ("L", pt))
            run = []
        else:
            run.append(pt)
    return segs


def svg_d(polys):
    """Polygons (units, y down) -> SVG path data, outer contours and holes wound oppositely."""
    out = []
    for p, depth in zip(polys, nesting(polys)):
        area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
        if (area > 0) != (depth % 2 == 0):
            p = p[::-1]
        for seg in segments(p):
            if seg[0] == "M":
                out.append("M%.1f %.1f" % seg[1])
            elif seg[0] == "L":
                out.append("L%.1f %.1f" % seg[1])
            else:
                offs, end = seg[1], seg[2]
                for k, c in enumerate(offs):  # implied on-curve midpoints between control points
                    e = end if k == len(offs) - 1 else ((c[0] + offs[k + 1][0]) / 2, (c[1] + offs[k + 1][1]) / 2)
                    out.append("Q%.1f %.1f %.1f %.1f" % (c[0], c[1], e[0], e[1]))
        out.append("Z")
    return "".join(out)


# -- the wordmark ---------------------------------------------------------------


def logo_paths():
    root = ET.parse(LOGO).getroot()
    out = []
    for el in root.iter(f"{{{SVGNS}}}path"):
        pen = FlatPen()
        parse_path(el.get("d"), pen)
        allp = np.concatenate(pen.contours)
        out.append(dict(d=el.get("d"), fill=el.get("fill").upper(), contours=pen.contours,
                        box=(allp[:, 0].min(), allp[:, 1].min(), allp[:, 0].max(), allp[:, 1].max())))
    return out


def pick(paths, x, y):
    """The blue path whose box contains (x, y)."""
    for p in paths:
        b = p["box"]
        if p["fill"] == EXACT.upper() and b[0] <= x <= b[2] and b[1] <= y <= b[3]:
            return p
    raise LookupError((x, y))


ROW1, ROW2 = 1112, 1913  # the wordmark's two baselines (bottom of each W)
SC = 2.0  # raster scale for cutting pieces out of the wordmark
KIT_TOL = 1.4  # px: fewer, editable nodes in the kit


def raster_of(p, pad=40):
    b = p["box"]
    x0, y0 = b[0] - pad, b[1] - pad
    w, h = int((b[2] - b[0] + 2 * pad) * SC), int((b[3] - b[1] + 2 * pad) * SC)
    return rasterize(p["contours"], SC, x0, y0, w, h), x0, y0


def split_at_gap(mask, lo, hi, x0):
    """Cut a ligature at the column (between unit x lo and hi) with the least ink."""
    a, b = int((lo - x0) * SC), int((hi - x0) * SC)
    col = a + int(np.argmin(mask[:, a:b].sum(0)))
    left, right = mask.copy(), mask.copy()
    left[:, col:] = False
    right[:, :col] = False
    return left, right


def largest(mask):
    lab, n = ndi.label(mask)
    if n <= 1:
        return mask
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))


def logo_glyphs():
    """name -> (polys in units relative to (origin x, baseline), exact?)"""
    paths = logo_paths()
    res = {}

    def place(polys, baseline):
        allp = np.concatenate(polys)
        ox = allp[:, 0].min()
        return [p - np.array([ox, baseline]) for p in polys]

    def verbatim(p, baseline):
        """The wordmark's own path data, moved so its ink starts at x 0 on the baseline."""
        return dict(polys=place(p["contours"], baseline), d=p["d"], shift=(-p["box"][0], -baseline), exact=True)

    def traced(polys, exact):
        return dict(polys=polys, d=None, shift=None, exact=exact)

    S1 = pick(paths, 400, 700)  # first S, row 1
    S2 = pick(paths, 2800, 1500)  # last S, row 2 (the wordmark's "s")
    W2 = pick(paths, 700, 1500)
    E2 = pick(paths, 1300, 1500)
    res["upper-S"] = verbatim(S1, ROW1)
    res["upper-W"] = verbatim(pick(paths, 900, 700), ROW1)
    res["lower-s"] = verbatim(S2, ROW2)
    res["lower-w"] = verbatim(W2, ROW2)
    res["lower-e"] = verbatim(E2, ROW2)

    def ucol(x, x0):
        return int(round((x - x0) * SC))

    def urow(y, y0):
        return int(round((y - y0) * SC))

    # d: the D of "ed", without the e's tail (it joins the stem low down);
    # the little flag at the top left of the D stays.
    ed = pick(paths, 2100, 700)
    m, x0, y0 = raster_of(ed)
    cols = m.sum(0)
    stem_left = int(np.argmax(cols >= 0.9 * cols.max()))
    d = m.copy()
    d[:, :ucol(1815, x0)] = False
    d[urow(650, y0):, :stem_left] = False
    res["lower-d"] = traced(place(trace(largest(d), SC, x0, y0, KIT_TOL), ROW1), True)

    # t: the T of "eT": keep the whole bar, drop the e's tail under it.
    et = pick(paths, 2300, 1300)
    m, x0, y0 = raster_of(et)
    cols = m.sum(0)
    full = np.where(cols >= 0.95 * cols.max())[0]  # the stem's columns
    t = m.copy()
    t[:, :ucol(2030, x0)] = False
    t[urow(1305, y0):, :full.min()] = False
    t = largest(t)
    res["lower-t"] = traced(place(trace(t, SC, x0, y0, KIT_TOL), ROW2), True)

    # The T's stem, full height, gives I, l and i.
    stem = np.zeros_like(t)
    stem[:, full.min():full.max() + 1] = t[:, full.min():full.max() + 1]
    stem_polys = trace(largest(stem), SC, x0, y0, KIT_TOL)
    sb = np.concatenate(stem_polys)
    stem_h = ROW2 - sb[:, 1].min()

    def stretch(polys, height):
        """The stem, cut or lengthened at the top to `height` above the baseline."""
        out = []
        for p in polys:
            q = p.copy()
            q[:, 1] = ROW2 - (ROW2 - q[:, 1]) * height / stem_h
            out.append(q)
        return place(out, ROW2)

    res["upper-I"] = traced(stretch(stem_polys, CAP), False)
    res["lower-l"] = traced(stretch(stem_polys, ASC), False)
    i_top = XH - 150
    i_stem = stretch(stem_polys, i_top)
    # the dot: the smallest of the crown's dots, centred a little above the stem
    dot = min((p for p in paths if p["fill"] == "#F9B51A"), key=lambda p: p["box"][2] - p["box"][0])
    dc0 = np.concatenate(dot["contours"]).mean(0)
    dot = dict(contours=[(c - dc0) * 1.5 + dc0 for c in dot["contours"]])  # survives the thinning
    da = np.concatenate(dot["contours"])
    sa = np.concatenate(i_stem)
    dx = (sa[:, 0].min() + sa[:, 0].max()) / 2 - (da[:, 0].min() + da[:, 0].max()) / 2
    dy = (-i_top - 55) - da[:, 1].max()
    res["lower-i"] = traced(i_stem + [c + np.array([dx, dy]) for c in dot["contours"]], False)

    # v: the left V of the wordmark's W, mirrored about its bottom point
    m, x0, y0 = raster_of(W2)
    rows = np.where(m.any(1))[0]
    low = m[rows.max() - int(0.08 * (rows.max() - rows.min())):rows.max() + 1].any(0)
    run = np.where(low)[0]
    gaps = np.where(np.diff(run) > 1)[0]
    first_end = run[gaps[0]] if len(gaps) else run[-1]
    c = (run[0] + first_end) // 2  # centre of the left V's foot
    half = m.copy()
    half[:, c + 1:] = False
    v = half.copy()
    w = m.shape[1]
    for x in range(max(0, 2 * c - w + 1), c):
        v[:, 2 * c - x] |= half[:, x]
    res["lower-v"] = traced(place(trace(largest(v), SC, x0, y0, KIT_TOL), ROW2), False)
    return res


# -- drafts from Fredoka ------------------------------------------------------

DRAFT_SQUEEZE = 0.72


def fredoka_drafts(names_chars):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "f.ttf")
        f = instancer.instantiateVariableFont(TTFont(FREDOKA), {"wght": 600})
        f.flavor = None
        f.save(path)
        S = 1000  # px per em while drafting
        font = ImageFont.truetype(path, S)
        out = {}
        stroke_px = 0.15 * S  # Fredoka 600's stem
        # Fredoka's real x-height (its 'x'), so the lower case lands on XH_DRAFT
        # after the strokes are brought to the wordmark's weight (which shrinks it).
        xim = Image.new("L", (S, 2 * S), 0)
        ImageDraw.Draw(xim).text((10, int(1.3 * S)), "x", font=font, fill=255, anchor="ls")
        xs_ = np.where((np.array(xim) > 127).any(1))[0]
        x_px = xs_.max() - xs_.min() + 1
        k_lower = XH_DRAFT / x_px
        for _ in range(3):
            dy_l = round((STROKE / k_lower - stroke_px) / 2)
            k_lower = XH_DRAFT / (x_px + 2 * min(dy_l, 0))
        for name, ch in names_chars:
            if ch in ACCENTED:
                continue
            lower = ch.islower()
            # caps: Fredoka's cap height (0.70 em) -> CAP; lower case: its x -> XH_DRAFT
            k = k_lower if lower else (CAP / 0.70) / S  # units per px
            im = Image.new("L", (int(1.8 * S), int(2.0 * S)), 0)
            ox, oy = int(0.2 * S), int(1.3 * S)
            ImageDraw.Draw(im).text((ox, oy), ch, font=font, fill=255, anchor="ls")
            m = np.array(im) > 127
            ys, xs = np.where(m)
            t = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            t = np.array(Image.fromarray((t * 255).astype(np.uint8)).resize(
                (max(2, int(t.shape[1] * DRAFT_SQUEEZE)), t.shape[0]), Image.LANCZOS)) > 127
            # bring the stroke to the wordmark's weight
            target_px = STROKE / k
            dx = int(round((target_px - stroke_px * DRAFT_SQUEEZE) / 2))
            dy = int(round((target_px - stroke_px) / 2))
            pad = np.pad(t, 120)
            if dx > 0:
                pad = ndi.maximum_filter1d(pad.astype(np.uint8), 2 * dx + 1, axis=1).astype(bool)
            if dy > 0:
                pad = ndi.maximum_filter1d(pad.astype(np.uint8), 2 * dy + 1, axis=0).astype(bool)
            if dy < 0:
                pad = ndi.minimum_filter1d(pad.astype(np.uint8), 2 * -dy + 1, axis=0).astype(bool)
            pad = ndi.distance_transform_edt(pad) > 6
            pad = ndi.distance_transform_edt(~pad) <= 6
            top_px = ys.min() - 120
            polys = trace(pad, 1 / k, 0, 0, 1.1)
            # to units, baseline at 0: y = (row + top_px - oy) * k
            polys = [np.stack([p[:, 0], p[:, 1] + (top_px - oy) * k], 1) for p in polys]
            if lower:
                polys = [warp_lower(p) for p in polys]
            allp = np.concatenate(polys)
            out[name] = dict(polys=[p - np.array([allp[:, 0].min(), 0]) for p in polys], d=None, shift=None, exact=False)
        return out


ACCENTED = {"À": "A", "ù": "u"}


def grave(cx, top):
    """A grave accent: a capsule as thick as the wordmark's strokes, falling to the right."""
    length, r, ang = 150, 0.4 * STROKE, math.radians(28)
    d = np.array([math.cos(ang), math.sin(ang)])
    n = np.array([-d[1], d[0]])
    centre = np.array([cx - 15, top - 70 - r])
    a, b = centre - d * length / 2, centre + d * length / 2
    pts = []
    for t in np.linspace(-math.pi / 2, math.pi / 2, 12):  # round end at b
        pts.append(b + r * (math.cos(t) * d + math.sin(t) * n))
    for t in np.linspace(math.pi / 2, 3 * math.pi / 2, 12):  # round end at a
        pts.append(a + r * (math.cos(t) * d + math.sin(t) * n))
    return np.array(pts)


def accented(glyphs):
    """À and ù: the base letter's draft (or logo letter) with a grave above."""
    out = {}
    for ch, base in ACCENTED.items():
        g = glyphs[gname(base)]
        polys = [p.copy() for p in g["polys"]]
        allp = np.concatenate(polys)
        cx = (allp[:, 0].min() + allp[:, 0].max()) / 2
        out[gname(ch)] = dict(polys=polys + [grave(cx, allp[:, 1].min())], d=None, shift=None, exact=False)
    return out


def warp_lower(p):
    """Keep ascenders and descenders short, as in the wordmark (d is barely taller than e)."""
    q = p.copy()
    y = -q[:, 1]  # height above the baseline
    asc_src = 0.75 * XH_DRAFT / 0.466
    up = y > XH_DRAFT
    y[up] = XH_DRAFT + (y[up] - XH_DRAFT) * (ASC_DRAFT - XH_DRAFT) / (asc_src - XH_DRAFT)
    desc_src = 0.24 * XH_DRAFT / 0.466
    dn = y < 0
    y[dn] = y[dn] * DESC / desc_src
    q[:, 1] = -y
    return q


# -- kit --------------------------------------------------------------------------


def cell_xy(i):
    return (i % COLS) * CW, (i // COLS) * CH


def write_kit(path: Path):
    glyphs = logo_glyphs()
    need = [(gname(c), c) for c in CHARS]
    glyphs.update(fredoka_drafts([(n, c) for n, c in need if n not in glyphs]))
    glyphs.update(accented(glyphs))
    rows = math.ceil(len(need) / COLS)
    W, H = COLS * CW, rows * CH
    out = [f'<svg xmlns="{SVGNS}" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           f'<rect id="background" x="0" y="0" width="{W}" height="{H}" fill="#FFF6E3"/>']
    for i, (name, ch) in enumerate(need):
        cx, cy = cell_xy(i)
        gi = glyphs[name]
        exact = gi["exact"]
        lines = [(BASE, "#2669FF", 3, "baseline"), (BASE - XH, "#F9B51A", 2, "x-height"),
                 (BASE - CAP, "#F9B51A", 2, "cap"), (BASE - ASC, "#E0A000", 1, "ascender"),
                 (BASE + DESC, "#E0A000", 1, "descender")]
        out.append(f'<g id="guides-{name}">')
        out.append(f'<rect id="cell-{name}" x="{cx + 10}" y="{cy + 10}" width="{CW - 20}" height="{CH - 20}" '
                   f'fill="none" stroke="#D9CFB8" stroke-width="4"/>')
        for y, col, sw, lab in lines:
            dash = "" if lab == "baseline" else ' stroke-dasharray="16 12"'
            out.append(f'<line x1="{cx + 30}" y1="{cy + y}" x2="{cx + CW - 30}" y2="{cy + y}" stroke="{col}" '
                       f'stroke-width="{sw * 2}"{dash}/>')
        label = ch if ch != "&" else "&amp;"
        tag = "logo" if exact else "draft"
        out.append(f'<text x="{cx + 40}" y="{cy + 110}" font-family="sans-serif" font-size="90" '
                   f'fill="#4F5A7D">{label}  ({tag})</text>')
        out.append("</g>")
        fill = EXACT if exact else DRAFT
        if gi["d"]:
            sx, sy = gi["shift"]
            out.append(f'<g id="g-{name}"><path d="{gi["d"]}" fill="{fill}" '
                       f'transform="translate({cx + LEFT + sx:.2f} {cy + BASE + sy:.2f})"/></g>')
        else:
            moved = [p + np.array([cx + LEFT, cy + BASE]) for p in gi["polys"]]
            out.append(f'<g id="g-{name}"><path d="{svg_d(moved)}" fill="{fill}"/></g>')
    out.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n")
    print(f"{path}: {len(need)} cells")


# -- build ------------------------------------------------------------------------


def parse_transform(s):
    t = Transform()
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s or ""):
        a = [float(v) for v in re.split(r"[\s,]+", args.strip()) if v]
        if name == "matrix":
            t = t.transform(a)
        elif name == "translate":
            t = t.translate(a[0], a[1] if len(a) > 1 else 0)
        elif name == "scale":
            t = t.scale(a[0], a[1] if len(a) > 1 else a[0])
        elif name == "rotate":
            if len(a) == 3:
                t = t.translate(a[1], a[2]).rotate(math.radians(a[0])).translate(-a[1], -a[2])
            else:
                t = t.rotate(math.radians(a[0]))
    return t


def shape_d(el):
    tag = el.tag.split("}")[-1]
    g = lambda k, d=0.0: float(el.get(k, d))
    if tag == "path":
        return el.get("d")
    if tag == "rect":
        x, y, w, h = g("x"), g("y"), g("width"), g("height")
        return f"M{x} {y}H{x + w}V{y + h}H{x}Z"
    if tag in ("circle", "ellipse"):
        cx, cy = g("cx"), g("cy")
        rx = g("r") if tag == "circle" else g("rx")
        ry = g("r") if tag == "circle" else g("ry")
        return (f"M{cx - rx} {cy}A{rx} {ry} 0 1 0 {cx + rx} {cy}A{rx} {ry} 0 1 0 {cx - rx} {cy}Z")
    if tag == "polygon":
        pts = el.get("points").split()
        return "M" + "L".join(pts) + "Z"
    return None


def read_kit(path: Path):
    """name -> (contours in units relative to the cell's (left+LEFT, baseline)), and cell origins."""
    root = ET.parse(path).getroot()
    cells, glyphs = {}, {}

    def walk(el, t, current):
        t = t.transform(parse_transform(el.get("transform"))) if el.get("transform") else t
        eid = el.get("id") or ""
        if eid.startswith("cell-"):
            x, y = t.transformPoint((float(el.get("x", 0)), float(el.get("y", 0))))
            cells[eid[5:]] = (x - 10, y - 10)
        if eid.startswith("g-"):
            current = eid[2:]
            glyphs.setdefault(current, [])
        if current and not eid.startswith("guides-"):
            d = shape_d(el)
            if d and el.get("fill", "") != "none":
                pen = FlatPen()
                parse_path(d, TransformPen(pen, t))
                glyphs[current].extend(pen.contours)
        for ch in el:
            walk(ch, t, current)

    walk(root, Transform(), None)
    # Figma may rename ids a little (e.g. "g-lower-a_2"): map back on the known names
    known = {gname(c) for c in CHARS}
    fix = lambda n: n if n in known else re.sub(r"[_ ]\d+$", "", n)
    cells = {fix(k): v for k, v in cells.items()}
    glyphs = {fix(k): v for k, v in glyphs.items()}
    out = {}
    for name, cs in glyphs.items():
        if name in cells and cs:
            cx, cy = cells[name]
            out[name] = [c - np.array([cx + LEFT, cy + BASE]) for c in cs]
    return out


def build(path: Path, out: Path, thickness: float, sidebearing: int):
    glyphs = read_kit(path)
    scale = 700 / CAP  # font units per kit unit: cap height 700/1000
    R = 2.0  # px per kit unit while thinning
    erode = max(0.0, (STROKE - thickness * CAP) / 2) * R
    fb_glyphs, metrics, cmap = {}, {}, {}
    order = [".notdef", "space"]
    pen = TTGlyphPen(None)
    for ring in (((60, 0), (60, 700), (420, 700), (420, 0)), ((120, 60), (360, 60), (360, 640), (120, 640))):
        pen.moveTo(ring[0])
        for p in ring[1:]:
            pen.lineTo(p)
        pen.closePath()
    fb_glyphs[".notdef"], metrics[".notdef"] = pen.glyph(), (480, 60)
    fb_glyphs["space"], metrics["space"] = TTGlyphPen(None).glyph(), (int(0.26 * 1000), 0)
    cmap[0x20] = cmap[0xA0] = cmap[0x202F] = "space"
    for ch in CHARS:
        name = gname(ch)
        if name not in glyphs:
            print("missing in kit:", name)
            continue
        cs = glyphs[name]
        allp = np.concatenate(cs)
        x0, y0 = allp[:, 0].min() - 30, allp[:, 1].min() - 30
        w = int((allp[:, 0].max() - x0 + 30) * R)
        h = int((allp[:, 1].max() - y0 + 30) * R)
        m = rasterize(cs, R, x0, y0, w, h)
        if erode > 0:
            m = ndi.distance_transform_edt(m) > erode
        polys = trace(m, R, x0, y0)
        ink = np.concatenate(polys)
        left = ink[:, 0].min()
        pen = TTGlyphPen(None)
        for p, depth in zip(polys, nesting(polys)):
            q = np.stack([(p[:, 0] - left) * scale + sidebearing, -p[:, 1] * scale], 1)
            area = 0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])
            if (area < 0) != (depth % 2 == 0):
                q = q[::-1]
            for seg in segments(q):
                if seg[0] == "M":
                    pen.moveTo(tuple(map(round, seg[1])))
                elif seg[0] == "L":
                    pen.lineTo(tuple(map(round, seg[1])))
                else:
                    pen.qCurveTo(*[tuple(map(round, c)) for c in seg[1]], tuple(map(round, seg[2])))
            pen.closePath()
        gl = f"uni{ord(ch):04X}"
        order.append(gl)
        fb_glyphs[gl] = pen.glyph()
        width = (ink[:, 0].max() - left) * scale
        metrics[gl] = (int(round(width + 2 * sidebearing)), sidebearing)
        cmap[ord(ch)] = gl
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(fb_glyphs)
    glyf = fb.font["glyf"]
    for n in order:
        glyf[n].recalcBounds(glyf)
        if glyf[n].numberOfContours:
            metrics[n] = (metrics[n][0], glyf[n].xMin)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=900, descent=-260)
    family = "SwedeSweets Wordmark"
    fb.setupNameTable({
        "familyName": family, "styleName": "Regular", "uniqueFontIdentifier": family + " 2.0",
        "fullName": family, "psName": "SwedeSweetsWordmark", "version": "Version 2.0",
        "copyright": "Letterforms from the SwedeSweets wordmark; drafts derived from Fredoka, "
                     "Copyright 2013 The Fredoka Project Authors (SIL Open Font License 1.1).",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, "
                              "Version 1.1. http://scripts.sil.org/OFL",
    })
    fb.setupOS2(sTypoAscender=900, sTypoDescender=-260, sTypoLineGap=0, usWinAscent=900, usWinDescent=260,
                sxHeight=round(XH * scale), sCapHeight=700, usWeightClass=400, fsType=0)
    fb.setupPost()
    with tempfile.TemporaryDirectory() as tmp:
        ttf = os.path.join(tmp, "nav.ttf")
        fb.save(ttf)
        font = TTFont(ttf)
        font.flavor = "woff2"
        out.parent.mkdir(parents=True, exist_ok=True)
        font.save(out)
    print(f"{out}: {len(order)} glyphs, {out.stat().st_size} bytes")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("kit", help="write the Figma kit (overwrites it!)")
    k.add_argument("--out", type=Path, default=KIT)
    b = sub.add_parser("build", help="kit -> woff2")
    b.add_argument("--kit", type=Path, default=KIT)
    b.add_argument("--out", type=Path, default=OUT)
    b.add_argument("--thickness", type=float, default=0.19,
                   help="stroke / cap height (the wordmark's: about 0.20; lower is thinner)")
    b.add_argument("--sidebearing", type=int, default=45, help="space each side of a letter, 1/1000 em")
    a = ap.parse_args()
    if a.cmd == "kit":
        write_kit(a.out)
    else:
        build(a.kit, a.out, a.thickness, a.sidebearing)


if __name__ == "__main__":
    main()

"""Build static/fonts/swedesweets-nav.woff2: the navbar links' typeface.

    python tools/build_nav_font.py
    python tools/build_nav_font.py --thickness 0.16 --squeeze 0.70

The wordmark (static/images/swedesweets-logo.svg) only has the letters
S, W, E, D and T, so it cannot set a whole navbar. Instead the closest
open typeface already in the repo is reshaped towards the wordmark's
letterforms. What was measured on the wordmark's traced S, W and e, and on
Fredoka, Sniglet and Nunito at the same letter height:

  * the wordmark's letters are ~0.72 times as wide as Fredoka's (S 0.52 vs
    0.71, W 0.95 vs 1.30, e 0.64 vs 0.95, width/height), so Fredoka (the
    closest of the three: stroke weight and round forms; Sniglet is too heavy,
    Nunito too wide) is squeezed by that factor;
  * the wordmark's strokes are 0.18 (S), 0.20 (e) and 0.27 (W) of the letter
    height; the navbar's are thinner on purpose (--thickness, 0.145 of the cap
    height) so the links do not weigh as much as the logo;
  * its terminals are cut flat with small rounded corners (about 0.03 of the
    height), where Fredoka's are half circles, so the tips are squared off
    and every corner rounded to that radius.

Each glyph is rendered large, shaped as a bitmap (as the wordmark itself was
made: a traced bitmap), traced back to outlines and written as a new font.
Kerning is not carried over: the CSS sets a little letter-spacing instead.

Needs fonttools, brotli, Pillow, numpy, scipy and scikit-image (development
only; the site just serves the .woff2). The output is deterministic.
Licence: derived from Fredoka, SIL Open Font License (SwedeSweetsNav-OFL.txt).
"""

from __future__ import annotations

import argparse
import math
import os
import tempfile
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from skimage import measure

FONTS = Path(__file__).resolve().parent.parent / "static" / "fonts"
SOURCE = FONTS / "fredoka.woff2"
OUT = FONTS / "swedesweets-nav.woff2"

S = 1200  # pixels per em while shaping
CAP = 0.7  # Fredoka's cap height, in em
MARGIN = 160  # pixels of room around a glyph while shaping
CODEPOINTS = (
    list(range(0x20, 0x7F))
    + list(range(0xA0, 0x100))
    + [0x152, 0x153, 0x178, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026, 0x20AC]
)

# Filled in by main() before the worker processes start.
CFG: dict = {}


# -- bitmap shaping -----------------------------------------------------------


def render(font_path: str, ch: str):
    """One glyph as a bool bitmap, and the pixel of its pen origin on the baseline."""
    font = ImageFont.truetype(font_path, S)
    pad = int(0.25 * S)
    im = Image.new("L", (int(1.6 * S) + 2 * pad, int(1.9 * S) + 2 * pad), 0)
    ox, oy = pad, pad + int(1.2 * S)
    ImageDraw.Draw(im).text((ox, oy), ch, font=font, fill=255, anchor="ls")
    return np.array(im) > 127, ox, oy


def disk_dilate(m, r):
    return m if r <= 0 else ndi.distance_transform_edt(~m) <= r


def disk_erode(m, r):
    return m if r <= 0 else ndi.distance_transform_edt(m) > r


def rect_dilate(m, rx, ry):
    u = m.astype(np.uint8)
    if rx > 0:
        u = ndi.maximum_filter1d(u, size=2 * rx + 1, axis=1)
    if ry > 0:
        u = ndi.maximum_filter1d(u, size=2 * ry + 1, axis=0)
    return u.astype(bool)


def rect_erode(m, rx, ry):
    u = m.astype(np.uint8)
    if rx > 0:
        u = ndi.minimum_filter1d(u, size=2 * rx + 1, axis=1)
    if ry > 0:
        u = ndi.minimum_filter1d(u, size=2 * ry + 1, axis=0)
    return u.astype(bool)


def stem_metrics(font_path: str):
    """Vertical stem of 'l' and horizontal bar of 'T', in pixels."""
    ml, _, _ = render(font_path, "l")
    stem = int(ml[ml.shape[0] // 2].sum())
    mt, _, _ = render(font_path, "T")
    xs = np.where(mt.any(axis=0))[0]
    col = mt[:, xs[0] + int((xs[-1] - xs[0]) * 0.12)]
    ys = np.where(col)[0]
    bar = int(col[ys[0]:].argmin()) if col[ys[0]:].min() == 0 else len(ys)
    return stem, bar


def shape(m, p):
    """Thickness per axis, flat terminals, then rounded corners (pixels)."""
    dx, dy = int(round(p["dx"])), int(round(p["dy"]))
    if dx > 0 or dy > 0:
        m = rect_dilate(m, max(dx, 0), max(dy, 0))
    if dx < 0 or dy < 0:
        m = rect_erode(m, max(-dx, 0), max(-dy, 0))
    s = int(round(p["sq"]))
    if s > 0:
        # Square the tips, but let it grow at most g px so narrow gaps
        # (the S's apertures) never close.
        flat = disk_erode(rect_dilate(m, s, s), s)
        m = m | (flat & disk_dilate(m, 0.45 * s))
    m = disk_dilate(disk_erode(m, p["rc"]), p["rc"])  # convex corners
    m = disk_erode(disk_dilate(m, p["rf"]), p["rf"])  # concave corners
    return m


# -- tracing ------------------------------------------------------------------


def glyph(cp):
    """(codepoint, contours in font units or None, advance)."""
    path, cmap, hmtx, sx, dx = CFG["path"], CFG["cmap"], CFG["hmtx"], CFG["sx"], CFG["p"]["dx"]
    adv = hmtx[cmap[cp]][0]
    new_adv = int(round(adv * sx + 2 * dx / S * 1000 + CFG["tracking"]))
    m, ox, oy = render(path, chr(cp))
    if not m.any():
        return cp, None, new_adv
    ys, xs = np.where(m.any(1))[0], np.where(m.any(0))[0]
    t = m[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
    width = max(2, int(round(t.shape[1] * sx)))
    t = np.array(Image.fromarray((t * 255).astype(np.uint8)).resize((width, t.shape[0]), Image.LANCZOS)) > 127
    left, top = (xs[0] - ox) * sx, oy - ys[0]
    pad = np.zeros((t.shape[0] + 2 * MARGIN, t.shape[1] + 2 * MARGIN), bool)
    pad[MARGIN:MARGIN + t.shape[0], MARGIN:MARGIN + t.shape[1]] = t
    out = shape(pad, CFG["p"])
    polys = []
    for c in measure.find_contours(out.astype(float), 0.5):
        a = measure.approximate_polygon(c, 0.42)
        if len(a) > 1 and np.allclose(a[0], a[-1]):
            a = a[:-1]
        if len(a) < 3:
            continue
        x = (left + dx + (a[:, 1] - MARGIN)) / S * 1000
        y = (top - (a[:, 0] - MARGIN)) / S * 1000
        polys.append(np.stack([x, y], 1))
    return cp, polys, new_adv


def orient(polys):
    """TrueType winding: outer contours clockwise, holes counter-clockwise."""
    out = []
    for i, p in enumerate(polys):
        depth = sum(1 for j, q in enumerate(polys) if j != i and measure.points_in_poly(p[:1], q)[0])
        area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
        if (area < 0) != (depth % 2 == 0):
            p = p[::-1]
        out.append(p)
    return out


def to_glyph(polys):
    """Quadratic outlines: sharp turns (> 40 degrees) on-curve, the rest control points."""
    pen = TTGlyphPen(None)
    for p in orient(polys):
        n = len(p)
        pts = [(int(round(x)), int(round(y))) for x, y in p]
        on = []
        for i in range(n):
            v1, v2 = p[i] - p[i - 1], p[(i + 1) % n] - p[i]
            on.append(abs(math.degrees(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1 @ v2))) > 40)
        if not any(on):
            pen.qCurveTo(*pts, None)
            pen.closePath()
            continue
        i0 = on.index(True)
        seq = [(pts[(i0 + k) % n], on[(i0 + k) % n]) for k in range(n)]
        pen.moveTo(seq[0][0])
        run = []
        for pt, is_on in seq[1:] + [seq[0]]:
            if is_on:
                pen.qCurveTo(*run, pt) if run else pen.lineTo(pt)
                run = []
            else:
                run.append(pt)
        pen.closePath()
    return pen.glyph()


# -- font ---------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--weight", type=int, default=600, help="Fredoka weight to start from")
    ap.add_argument("--squeeze", type=float, default=0.72, help="horizontal scale (the wordmark's)")
    ap.add_argument("--thickness", type=float, default=0.145, help="stroke / cap height (wordmark: 0.18-0.27)")
    ap.add_argument("--corner", type=float, default=0.03, help="terminal corner radius / cap height")
    ap.add_argument("--tracking", type=int, default=14, help="extra advance per glyph, 1/1000 em")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "base.ttf")
        static = instancer.instantiateVariableFont(TTFont(SOURCE), {"wght": a.weight})
        static.flavor = None
        static.save(path)
        base = TTFont(path)
        cmap, hmtx = base.getBestCmap(), base["hmtx"]
        stem, bar = stem_metrics(path)
        cap, thick = CAP * S, a.thickness * CAP * S
        CFG.update(
            path=path, cmap=cmap, hmtx=hmtx, sx=a.squeeze, tracking=a.tracking,
            p=dict(
                dx=(thick - a.squeeze * stem) / 2,  # after the squeeze, the stems regain their width
                dy=(thick - bar) / 2,
                sq=max(0, thick / 2 - a.corner * cap),
                rc=0.018 * S,
                rf=0.012 * S,
            ),
        )
        cps = [c for c in CODEPOINTS if c in cmap]
        with Pool() as pool:  # fork: workers inherit CFG
            res = pool.map(glyph, cps, chunksize=4)
        names = {cp: cmap[cp] for cp in cps}

    order, glyphs, metrics, cm = [".notdef"], {}, {}, {}
    pen = TTGlyphPen(None)  # .notdef: an open box
    for ring in (((60, 0), (60, 700), (420, 700), (420, 0)), ((120, 60), (360, 60), (360, 640), (120, 640))):
        pen.moveTo(ring[0])
        for pt in ring[1:]:
            pen.lineTo(pt)
        pen.closePath()
    glyphs[".notdef"], metrics[".notdef"] = pen.glyph(), (480, 60)
    for cp, polys, adv in res:
        name = names[cp]
        order.append(name)
        glyphs[name] = to_glyph(polys) if polys else TTGlyphPen(None).glyph()
        cm[cp] = name
        metrics[name] = (adv, 0)

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cm)
    fb.setupGlyf(glyphs)
    glyf = fb.font["glyf"]
    for n in order:
        glyf[n].recalcBounds(glyf)
        metrics[n] = (metrics[n][0], glyf[n].xMin if glyf[n].numberOfContours else 0)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=974, descent=-236)
    family = "SwedeSweets Nav"
    fb.setupNameTable({
        "familyName": family, "styleName": "Regular", "uniqueFontIdentifier": family + " 1.0",
        "fullName": family, "psName": "SwedeSweetsNav", "version": "Version 1.0",
        "copyright": "Derived from Fredoka, Copyright 2013 The Fredoka Project Authors "
                     "(SIL Open Font License 1.1). Reshaped for SwedeSweets.",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, "
                              "Version 1.1. http://scripts.sil.org/OFL",
    })
    fb.setupOS2(sTypoAscender=974, sTypoDescender=-236, sTypoLineGap=0, usWinAscent=974,
                usWinDescent=236, sxHeight=500, sCapHeight=700, usWeightClass=400, fsType=0)
    fb.setupPost()
    with tempfile.TemporaryDirectory() as tmp:
        ttf = os.path.join(tmp, "nav.ttf")
        fb.save(ttf)
        font = TTFont(ttf)
        font.flavor = "woff2"
        a.out.parent.mkdir(parents=True, exist_ok=True)
        font.save(a.out)
    print(f"{a.out.relative_to(Path.cwd()) if a.out.is_relative_to(Path.cwd()) else a.out}: "
          f"{len(order)} glyphs, {a.out.stat().st_size} bytes")


if __name__ == "__main__":
    main()

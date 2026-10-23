"""Draw the day theme's engraved clouds as SVG files.

    python tools/draw_clouds.py

Writes static/images/clouds/: the logo's cloud (logo.svg, and a plainer
logo-small.svg for the navbar), and one cloud for each of the navbar's
links and buttons (nav-<name>.svg). Each cloud is a heap of lumps drawn
back to front: each lump white with its own outline, short broken
curved strokes shading its lower right side, so a lump in front leaves
an inner contour on the one behind it. The middle lumps (behind the
words) stay clean. The drawing is deterministic (a fixed seed), so
running it again gives the same files.

The files stretch to the box they are drawn in (preserveAspectRatio
"none"), the strokes keeping their width (non-scaling-stroke), so a
longer word in another language only stretches its cloud.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "static" / "images" / "clouds"
INK = "#5f78c0"


@dataclass(frozen=True)
class Lump:
    cx: float
    cy: float
    rx: float
    ry: float
    contour: bool = True
    hatch: float = 1.0


@dataclass(frozen=True)
class Cloud:
    name: str
    width: int
    height: int
    lumps: tuple[Lump, ...]
    rows: int  # hatch rows on a fully hatched lump
    outline: float  # stroke widths, in px on the page
    contour: float
    stroke: tuple[float, float]  # thinnest and thickest hatch stroke


def _n(value: float) -> str:
    # whole units: the boxes are 600 and 200 wide, finer is not seen
    return f"{value:.0f}"


def _ellipse(lump: Lump, **attrs: str) -> str:
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return (
        f'<ellipse cx="{_n(lump.cx)}" cy="{_n(lump.cy)}" '
        f'rx="{_n(lump.rx)}" ry="{_n(lump.ry)}"{extra}/>'
    )


def _arc(
    cx: float, cy: float, rx: float, ry: float, a0: float, a1: float, steps: int
) -> str:
    points = [
        (
            cx + rx * math.cos(a0 + (a1 - a0) * k / steps),
            cy + ry * math.sin(a0 + (a1 - a0) * k / steps),
        )
        for k in range(steps + 1)
    ]
    return "M" + " ".join(f"{_n(x)},{_n(y)}" for x, y in points)


def draw(cloud: Cloud) -> str:
    rng = random.Random(4)
    pad_x, pad_y = cloud.width * 0.02, cloud.height * 0.08
    view = (
        f"{_n(-pad_x)} {_n(-pad_y)} "
        f"{_n(cloud.width + 2 * pad_x)} {_n(cloud.height + 1.4 * pad_y)}"
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" '
        'preserveAspectRatio="none">',
        "<defs>",
        *(
            f'<clipPath id="c{i}">{_ellipse(lump)}</clipPath>'
            for i, lump in enumerate(cloud.lumps)
        ),
        "</defs>",
        f'<g fill="none" stroke="{INK}" stroke-width="{cloud.outline}" '
        'vector-effect="non-scaling-stroke">',
        *(_ellipse(lump, vector_effect="non-scaling-stroke") for lump in cloud.lumps),
        "</g>",
    ]
    for i, lump in enumerate(cloud.lumps):
        out.append(_ellipse(lump, fill="#fff"))
        if lump.contour:
            path = _arc(
                lump.cx,
                lump.cy,
                lump.rx,
                lump.ry,
                math.radians(150),
                math.radians(390),
                24,
            )
            out.append(
                f'<path d="{path}" fill="none" stroke="{INK}" '
                f'stroke-width="{cloud.contour}" stroke-linecap="round" '
                'opacity=".85" vector-effect="non-scaling-stroke"/>'
            )
        rows = round(cloud.rows * lump.hatch)
        if not rows:
            continue
        group = [
            f'<g clip-path="url(#c{i})" fill="none" stroke="{INK}" '
            'stroke-linecap="round">'
        ]
        for k in range(rows):
            share = k / max(rows - 1, 1)
            radius = 0.55 + 0.45 * share
            ox, oy = -lump.rx * 0.30, -lump.ry * 0.48
            width = cloud.stroke[0] + (cloud.stroke[1] - cloud.stroke[0]) * share
            opacity = 0.35 + 0.5 * share
            t = math.radians(-10)
            strokes = []
            while t < math.radians(150):
                seg = math.radians(rng.uniform(9, 18))
                gap = math.radians(rng.uniform(3, 7))
                strokes.append(
                    _arc(
                        lump.cx + ox,
                        lump.cy + oy,
                        lump.rx * radius * 1.02,
                        lump.ry * radius * 1.02,
                        t,
                        t + seg,
                        3,
                    )
                )
                t += seg + gap
            # (a row's broken strokes as one path)
            group.append(
                f'<path d="{"".join(strokes)}" stroke-width="{width:.2f}" '
                f'opacity="{opacity:.2f}" '
                'vector-effect="non-scaling-stroke"/>'
            )
        group.append("</g>")
        out += group
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _scaled(lumps: list[tuple], sx: float, sy: float) -> tuple[Lump, ...]:
    return tuple(
        Lump(cx * sx, cy * sy, rx * sx, ry * sy, *rest)
        for cx, cy, rx, ry, *rest in lumps
    )


# The logo's cloud: two tops behind the logo, small lumps at its far ends.
LOGO = [
    (205, 118, 105, 80, True, 0.9),
    (385, 98, 120, 92, True, 1.0),
    (100, 182, 82, 62, True, 1.0),
    (500, 178, 85, 64, True, 1.0),
    (52, 228, 50, 38, True, 1.0),
    (552, 228, 48, 36, True, 1.0),
    (300, 170, 175, 95, False, 0.0),
    (300, 248, 240, 38, False, 1.2),
]

# The navbar's: each its own heap, in a 200 x 100 box.
NAV = {
    "lollipop": [
        (60, 42, 44, 34),
        (116, 36, 52, 40),
        (164, 52, 36, 28),
        (100, 64, 92, 26, False, 0.0),
        (100, 82, 96, 16, False, 1.2),
    ],
    "map-pin": [
        (36, 56, 32, 26),
        (80, 38, 44, 36),
        (128, 44, 36, 30),
        (168, 58, 28, 24),
        (100, 66, 92, 24, False, 0.0),
        (100, 82, 96, 16, False, 1.2),
    ],
    "question": [
        (72, 40, 48, 38),
        (132, 46, 40, 32),
        (100, 64, 88, 26, False, 0.0),
        (100, 82, 92, 16, False, 1.2),
    ],
    "info": [
        (52, 50, 36, 30),
        (104, 36, 52, 40),
        (152, 52, 32, 26),
        (100, 66, 92, 24, False, 0.0),
        (100, 82, 96, 16, False, 1.2),
    ],
    "menu": [
        (68, 44, 44, 36),
        (124, 38, 44, 38),
        (100, 64, 88, 26, False, 0.0),
        (100, 82, 92, 16, False, 1.2),
    ],
    "cart": [
        (92, 40, 56, 40),
        (148, 54, 36, 28),
        (100, 64, 88, 26, False, 0.0),
        (100, 82, 92, 16, False, 1.2),
    ],
}


def clouds() -> list[Cloud]:
    result = [
        Cloud(
            "logo",
            600,
            300,
            _scaled(LOGO, 1, 1),
            rows=11,
            outline=2.5,
            contour=1.6,
            stroke=(0.7, 1.6),
        ),
        Cloud(
            "logo-small",
            600,
            300,
            _scaled(LOGO, 1, 1),
            rows=5,
            outline=1.2,
            contour=0.8,
            stroke=(0.5, 0.9),
        ),
    ]
    for name, lumps in NAV.items():
        # (small: no inner contours, which would run behind the word)
        full = [(*lump, False, 1.0) if len(lump) == 4 else lump for lump in lumps]
        result.append(
            Cloud(
                f"nav-{name}",
                200,
                100,
                _scaled(full, 1, 1),
                rows=3,
                outline=1.2,
                contour=0.8,
                stroke=(0.5, 0.9),
            )
        )
    return result


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for cloud in clouds():
        path = OUT / f"{cloud.name}.svg"
        path.write_text(draw(cloud), encoding="utf-8")
        print(
            f"{path.relative_to(OUT.parent.parent.parent)}  "
            f"{path.stat().st_size // 1024} kB"
        )


if __name__ == "__main__":
    main()

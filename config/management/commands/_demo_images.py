"""Drawn product pictures for the demo catalogue (seed_demo_data --with-images).

Each product gets its own picture, the same on every run: a heap of
sweets on a soft light background, their shape and colours read from the
product's name ("Hallon Lakrits Skalle" -> red and black skulls, "Cola"
-> brown, "Svamp" -> mushrooms), chips and dip-mix sachets for the savoury
ones, and a simple garment for the merch. Pure Pillow, no network and no
third-party pictures; the JPEG goes through the normal product-image
upload (products.image_services), so thumbnails are made as for a real
upload.
"""

from __future__ import annotations

import hashlib
import math
import random
from io import BytesIO

from PIL import Image, ImageDraw, ImageFilter

SIZE = 800
BACKGROUND = (255, 249, 238)

# Name word -> colours (first match wins, so specific words come first).
COLOUR_WORDS: tuple[tuple[tuple[str, ...], tuple[tuple[int, int, int], ...]], ...] = (
    (
        ("salmiak", "lakrits", "licorice", "tyrkisk", "peber"),
        ((32, 28, 30), (70, 60, 62)),
    ),
    (("cola",), ((110, 56, 30), (176, 104, 52))),
    (
        ("hallon", "raspberry", "smultron", "jordgubb", "strawberr", "körsbär"),
        ((214, 38, 60), (238, 86, 104)),
    ),
    (("citron", "lemon"), ((246, 214, 52), (252, 236, 120))),
    (("pear", "päron", "mint", "pastell"), ((132, 196, 116), (196, 228, 170))),
    (("melon", "vattenmelon"), ((226, 70, 88), (92, 176, 92))),
    (("banan", "banana"), ((248, 210, 70), (120, 78, 44))),
    (("choklad", "kexchoklad", "chocolate", "punsch"), ((104, 62, 40), (150, 98, 66))),
    (
        ("kola", "fudge", "caramel", "karamel", "toffee", "grädd"),
        ((222, 164, 92), (244, 214, 160)),
    ),
    (
        ("skum", "foam", "cocos", "pärlsocker", "milkshake"),
        ((250, 196, 210), (255, 244, 236)),
    ),
    (("berry", "bär", "pomegranate", "blåbär"), ((120, 52, 150), (220, 60, 110))),
    (("bubblegum", "bubblizz"), ((120, 196, 238), (250, 150, 200))),
    (("sur", "sour", "syrlig", "fizzy"), ((140, 210, 60), (250, 200, 40))),
)

CANDY_COLOURS = (
    (236, 72, 90),
    (250, 168, 40),
    (250, 214, 60),
    (110, 196, 92),
    (80, 160, 230),
    (160, 100, 210),
    (250, 130, 170),
    (255, 120, 60),
)

# Name word -> shape (first match wins).
SHAPE_WORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("dipmix",), "sachet"),
    (("chips",), "chip"),
    (("skalle",), "skull"),
    (("ring",), "ring"),
    (("skruv", "twist", "lakritsflaska", "dynamit"), "rod"),
    (("svamp", "kantarell"), "mushroom"),
    (("banan",), "banana"),
    (("boll", "pärl"), "ball"),
    (("kola", "fudge", "karamel", "kexchoklad", "praliner", "guf"), "wrapped"),
    (("hallon", "smultron", "jordgubb", "sommarbär", "körsbär", "båtar"), "berry"),
    (("ovals", "snäckor", "diamond", "bilar", "limousiner"), "oval"),
)

MERCH_SHAPES = {"hoodie": "hoodie", "t-shirt": "shirt", "cap": "cap"}

BRAND_BLUE = (20, 74, 200)
BRAND_YELLOW = (246, 181, 30)


def product_picture_jpeg(*, name: str, brand: str = "") -> bytes:
    """A JPEG picture of the product called `name` (same name, same picture)."""

    text = f"{brand} {name}".lower()
    rng = random.Random(hashlib.sha256(text.encode()).hexdigest())

    image = _background(rng)

    merch_shape = _merch_shape(name)
    if merch_shape:
        _draw_merch(image, merch_shape)
    else:
        shape = _first_match(SHAPE_WORDS, text) or rng.choice(("blob", "oval", "ball"))
        colours = _name_colours(text) or tuple(rng.sample(CANDY_COLOURS, 3))
        if shape == "sachet":
            _draw_sachet(image, rng, colours, name)
        else:
            _draw_heap(image, rng, shape, colours)

    output = BytesIO()
    image.convert("RGB").save(output, format="JPEG", quality=86)
    return output.getvalue()


def _first_match(table, text):
    for words, value in table:
        if any(word in text for word in words):
            return value
    return None


def _name_colours(text: str):
    """The colours of the flavours the name mentions: one flavour gives
    its two tones; several ("Citron Lakrits") give the main tone of each."""

    groups = [
        colours for words, colours in COLOUR_WORDS if any(w in text for w in words)
    ]
    if len(groups) == 1:
        return groups[0]
    return tuple(colours[0] for colours in groups[:3])


def _merch_shape(name: str) -> str:
    lowered = name.lower()
    for word, shape in MERCH_SHAPES.items():
        if word in lowered:
            return shape
    return ""


# ----------------------------------------------------------------------
# background and heap
# ----------------------------------------------------------------------


def _background(rng: random.Random) -> Image.Image:
    """Cream with a soft round light behind the heap."""

    image = Image.new("RGBA", (SIZE, SIZE), BACKGROUND + (255,))
    tint = rng.choice(
        ((255, 236, 200), (255, 228, 230), (232, 244, 255), (236, 248, 228))
    )
    # Transparent pixels carry the tint too, so the blur fades to cream
    # rather than to a grey edge. Blurred small and scaled up: cheaper.
    glow = Image.new("RGBA", (SIZE // 4, SIZE // 4), tint + (0,))
    ImageDraw.Draw(glow).ellipse(
        (22, 30, SIZE // 4 - 22, SIZE // 4 - 15), fill=tint + (255,)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(18)).resize(
        (SIZE, SIZE), Image.Resampling.BICUBIC
    )
    return Image.alpha_composite(image, glow)


def _draw_heap(image, rng, shape, colours) -> None:
    """About forty sweets piled in a low mound, back to front, over one
    soft shadow."""

    pieces = []
    for _ in range(42):
        angle = rng.uniform(0, math.tau)
        radius = rng.random() ** 0.7
        x = SIZE / 2 + math.cos(angle) * radius * 250
        y = SIZE * 0.56 + math.sin(angle) * radius * 150 - (1 - radius) * 70
        pieces.append(
            (y, x, rng.choice(colours), rng.uniform(0, 360), rng.uniform(0.85, 1.15))
        )

    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    for y, x, colour, rotation, scale in sorted(pieces):
        piece = _piece(shape, colour, rng, scale)
        piece = piece.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)
        left, top = int(x - piece.width / 2), int(y - piece.height / 2)
        layer.alpha_composite(piece, (max(left, 0), max(top, 0)))

    _composite_with_shadow(image, layer)


def _piece(shape, colour, rng, scale) -> Image.Image:
    size = 150
    piece = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(piece)
    dark = _shade(colour, 0.72)
    light = _shade(colour, 1.35)
    c = size / 2

    match shape:
        case "ring":
            draw.ellipse((c - 50, c - 50, c + 50, c + 50), fill=colour)
            draw.ellipse((c - 22, c - 22, c + 22, c + 22), fill=(0, 0, 0, 0))
            draw.arc((c - 44, c - 44, c + 44, c + 44), 200, 280, fill=light, width=6)
        case "rod":
            draw.rounded_rectangle(
                (c - 66, c - 14, c + 66, c + 14), radius=14, fill=colour
            )
            for offset in range(-56, 60, 16):
                draw.line(
                    (c + offset, c - 13, c + offset + 10, c + 13), fill=dark, width=4
                )
        case "mushroom":
            draw.rounded_rectangle(
                (c - 14, c - 4, c + 14, c + 40), radius=10, fill=(250, 240, 220)
            )
            draw.pieslice((c - 46, c - 40, c + 46, c + 24), 180, 360, fill=colour)
            draw.arc((c - 38, c - 32, c + 38, c + 16), 205, 260, fill=light, width=5)
        case "banana":
            draw.arc((c - 60, c - 70, c + 60, c + 40), 20, 160, fill=colour, width=26)
            draw.arc((c - 54, c - 64, c + 54, c + 34), 40, 70, fill=light, width=6)
        case "ball":
            draw.ellipse((c - 36, c - 36, c + 36, c + 36), fill=colour)
            for _ in range(10):
                dx, dy = rng.uniform(-24, 24), rng.uniform(-24, 24)
                draw.ellipse(
                    (c + dx - 3, c + dy - 3, c + dx + 3, c + dy + 3),
                    fill=(255, 255, 255),
                )
        case "wrapped":
            draw.polygon(((c - 64, c - 22), (c - 40, c), (c - 64, c + 22)), fill=light)
            draw.polygon(((c + 64, c - 22), (c + 40, c), (c + 64, c + 22)), fill=light)
            draw.rounded_rectangle(
                (c - 42, c - 24, c + 42, c + 24), radius=10, fill=colour
            )
            draw.line((c - 30, c - 12, c + 10, c - 12), fill=light, width=5)
        case "berry":
            for dx, dy in (
                (0, -22),
                (-18, -6),
                (18, -6),
                (-10, 14),
                (10, 14),
                (0, 30),
                (0, 2),
            ):
                draw.ellipse(
                    (c + dx - 16, c + dy - 16, c + dx + 16, c + dy + 16), fill=colour
                )
                draw.ellipse(
                    (c + dx - 9, c + dy - 10, c + dx - 2, c + dy - 3), fill=light
                )
        case "skull":
            draw.ellipse((c - 40, c - 44, c + 40, c + 28), fill=colour)
            draw.rounded_rectangle(
                (c - 24, c + 10, c + 24, c + 40), radius=10, fill=colour
            )
            draw.ellipse((c - 24, c - 18, c - 6, c + 2), fill=dark)
            draw.ellipse((c + 6, c - 18, c + 24, c + 2), fill=dark)
        case "chip":
            points = [
                (
                    c + math.cos(t) * (52 + rng.uniform(-8, 8)),
                    c + math.sin(t) * (38 + rng.uniform(-6, 6)),
                )
                for t in (i * math.tau / 14 for i in range(14))
            ]
            draw.polygon(points, fill=(236, 186, 84))
            for _ in range(5):
                dx, dy = rng.uniform(-30, 30), rng.uniform(-20, 20)
                draw.ellipse(
                    (c + dx - 3, c + dy - 3, c + dx + 3, c + dy + 3), fill=colour
                )
        case "oval":
            draw.ellipse((c - 52, c - 30, c + 52, c + 30), fill=colour)
            draw.ellipse((c - 36, c - 20, c - 4, c - 8), fill=light)
        case _:  # blob: a jelly sweet
            draw.rounded_rectangle(
                (c - 42, c - 34, c + 42, c + 34), radius=30, fill=colour
            )
            draw.ellipse((c - 28, c - 24, c - 6, c - 10), fill=light)

    scaled = int(size * scale)
    return piece.resize((scaled, scaled), Image.Resampling.LANCZOS)


def _shade(colour, factor):
    return tuple(max(0, min(255, int(channel * factor))) for channel in colour)


# ----------------------------------------------------------------------
# sachets and merch
# ----------------------------------------------------------------------


def _draw_sachet(image, rng, colours, name) -> None:
    """A dip-mix sachet: a pouch in the flavour's colour, crimped edges."""

    del rng, name
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    colour = colours[0] if colours else (92, 160, 92)
    box = (250, 180, 550, 620)
    draw.rounded_rectangle(box, radius=26, fill=colour)
    for x in range(box[0] + 10, box[2] - 6, 18):
        draw.line((x, box[1] + 6, x, box[1] + 30), fill=_shade(colour, 0.8), width=6)
        draw.line((x, box[3] - 30, x, box[3] - 6), fill=_shade(colour, 0.8), width=6)
    draw.rounded_rectangle((290, 320, 510, 480), radius=20, fill=(255, 250, 240))
    draw.ellipse((360, 350, 440, 430), fill=_shade(colour, 1.2))
    _composite_with_shadow(image, layer)


def _draw_merch(image, shape) -> None:
    """A SwedeSweets garment in the brand's blue with a yellow mark."""

    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    if shape == "cap":
        draw.pieslice((220, 230, 580, 590), 180, 360, fill=BRAND_BLUE)
        draw.ellipse((360, 400, 640, 470), fill=_shade(BRAND_BLUE, 0.8))
        draw.ellipse((385, 330, 415, 360), fill=BRAND_YELLOW)
    else:
        body = (
            (300, 200),
            (230, 240),
            (170, 380),
            (240, 410),
            (270, 360),
            (270, 640),
            (530, 640),
            (530, 360),
            (560, 410),
            (630, 380),
            (570, 240),
            (500, 200),
            (460, 240),
            (340, 240),
        )
        draw.polygon(body, fill=BRAND_BLUE)
        if shape == "hoodie":
            draw.ellipse((330, 150, 470, 270), fill=_shade(BRAND_BLUE, 0.85))
            draw.rounded_rectangle(
                (330, 470, 470, 560), radius=20, fill=_shade(BRAND_BLUE, 0.85)
            )
        draw.ellipse((370, 300, 430, 360), fill=BRAND_YELLOW)

    _composite_with_shadow(image, layer)


def _composite_with_shadow(image, layer) -> None:
    """The layer over a soft shadow of itself (blurred at half size)."""

    half = (SIZE // 2, SIZE // 2)
    alpha = layer.getchannel("A").resize(half).point(lambda a: a * 0.25)
    shadow = Image.new("RGBA", half, (60, 40, 30, 0))
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(7)).resize(image.size)
    image.alpha_composite(shadow, (8, 14))
    image.alpha_composite(layer)

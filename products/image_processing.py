"""From one uploaded product picture to the three files a product keeps.

    original   the upload, cleaned: turned the right way up and copied into
               a new image, so no EXIF (a phone photo's GPS position, the
               camera), XMP or comment follows it. JPEG stays JPEG, PNG
               stays PNG with its transparency (a cut-out product must not
               get a white box on the cream page). The source of truth the
               other two are made from.
    display    WebP, at most 1600 px: the product page and "Open image".
    thumbnail  WebP, at most 640 px: tiles, cart and order lines, lists.

The approach follows event-guestbook's normalize_original, which flattens
everything to JPEG; product pictures keep PNG and its alpha instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

THUMBNAIL_MAX_SIZE = (
    640,
    640,
)
THUMBNAIL_QUALITY = 78

DISPLAY_MAX_SIZE = (
    1600,
    1600,
)
DISPLAY_QUALITY = 82

ORIGINAL_JPEG_QUALITY = 92
JPEG_BACKGROUND = (255, 255, 255)


@dataclass(frozen=True, slots=True)
class ProcessedProductImage:
    original: ContentFile
    display: ContentFile
    thumbnail: ContentFile


def process_product_image(
    image_file: BinaryIO,
    *,
    original_name: str,
) -> ProcessedProductImage:
    """Clean the original and make the display picture and thumbnail.

    original_name decides the original's format (.jpg/.jpeg or .png).
    The supplied file is rewound before returning.
    """

    suffix = _original_suffix(original_name)

    image_file.seek(0)

    with Image.open(image_file) as source:
        icc_profile = (
            source.info.get("icc_profile")
            if source.mode in {"RGB", "RGBA"}
            else None
        )

        oriented = ImageOps.exif_transpose(source)

        original = _encode_original(
            oriented,
            suffix=suffix,
            icc_profile=icc_profile,
        )
        display = _encode_webp(
            oriented,
            max_size=DISPLAY_MAX_SIZE,
            quality=DISPLAY_QUALITY,
        )
        thumbnail = _encode_webp(
            oriented,
            max_size=THUMBNAIL_MAX_SIZE,
            quality=THUMBNAIL_QUALITY,
        )

    image_file.seek(0)

    return ProcessedProductImage(
        original=ContentFile(
            original,
            name=f"{uuid4().hex}{suffix}",
        ),
        display=ContentFile(
            display,
            name=f"{uuid4().hex}.webp",
        ),
        thumbnail=ContentFile(
            thumbnail,
            name=f"{uuid4().hex}.webp",
        ),
    )


def has_metadata(
    image_file: BinaryIO,
) -> bool:
    """Whether a stored picture still carries EXIF, XMP or a comment (an
    original saved before originals were cleaned). Rewinds the file."""

    image_file.seek(0)

    with Image.open(image_file) as image:
        found = bool(image.getexif()) or any(
            key in image.info
            for key in ("exif", "xmp", "XML:com.adobe.xmp", "comment")
        )

    image_file.seek(0)

    return found


def product_original_filename(
    original_name: str,
) -> str:
    """Generate a storage-safe name while preserving JPEG/PNG format."""

    return f"{uuid4().hex}{_original_suffix(original_name)}"


def _original_suffix(
    original_name: str,
) -> str:
    suffix = Path(original_name).suffix.lower()

    if suffix == ".jpeg":
        suffix = ".jpg"

    if suffix not in {".jpg", ".png"}:
        raise ValueError("Unsupported product image extension.")

    return suffix


def _encode_original(
    image: Image.Image,
    *,
    suffix: str,
    icc_profile: bytes | None,
) -> bytes:
    """The picture's pixels in a new image (no metadata), as JPEG or PNG."""

    output = BytesIO()

    if suffix == ".png":
        clean = _clean_copy(image)
        options: dict[str, object] = {"format": "PNG", "optimize": True}
    else:
        clean = _clean_rgb_on_white(image)
        options = {
            "format": "JPEG",
            "quality": ORIGINAL_JPEG_QUALITY,
            "optimize": True,
        }

    if icc_profile:
        options["icc_profile"] = icc_profile

    clean.save(output, **options)

    return output.getvalue()


def _encode_webp(
    image: Image.Image,
    *,
    max_size: tuple[int, int],
    quality: int,
) -> bytes:
    resized = _clean_copy(image)
    resized.thumbnail(max_size, Image.Resampling.LANCZOS)

    output = BytesIO()
    resized.save(output, format="WEBP", quality=quality, method=6)

    return output.getvalue()


def _has_alpha(image: Image.Image) -> bool:
    return (
        image.mode in {"RGBA", "LA", "PA"}
        or (image.mode == "P" and "transparency" in image.info)
    )


def _clean_copy(
    image: Image.Image,
) -> Image.Image:
    """RGB, or RGBA when the picture has transparency, in a new image.

    A new image starts with an empty info dictionary, so nothing from the
    source (EXIF, XMP, comments) can follow it when it is saved.
    """

    mode = "RGBA" if _has_alpha(image) else "RGB"
    converted = image.convert(mode)

    clean = Image.new(mode, converted.size)
    clean.paste(converted)

    return clean


def _clean_rgb_on_white(
    image: Image.Image,
) -> Image.Image:
    """RGB in a new image; any transparency is laid on white (JPEG has
    no alpha)."""

    if not _has_alpha(image):
        return _clean_copy(image)

    rgba = image.convert("RGBA")
    clean = Image.new("RGB", rgba.size, JPEG_BACKGROUND)
    clean.paste(rgba, mask=rgba.getchannel("A"))

    return clean

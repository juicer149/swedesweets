"""Clean originals, the display picture, and rebuilding them."""

from __future__ import annotations

from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from PIL import Image

from products.image_processing import has_metadata, process_product_image
from products.image_services import change_product_image
from products.images import product_display_url
from products.tests.factories import product_factory

GPS_IFD = 0x8825
MAKE = 0x010F
ORIENTATION = 0x0112


def phone_photo(*, width: int = 3000, height: int = 2000) -> bytes:
    """A JPEG like a phone's: camera make, a GPS position, and rotated
    (orientation 6: the pixels lie on their side)."""

    exif = Image.Exif()
    exif[MAKE] = "PhoneMaker"
    exif[ORIENTATION] = 6
    gps = exif.get_ifd(GPS_IFD)
    gps[1] = "N"
    gps[2] = (45.0, 55.0, 1.0)

    output = BytesIO()
    Image.new("RGB", (width, height), (200, 40, 40)).save(
        output, format="JPEG", exif=exif.tobytes()
    )
    return output.getvalue()


def cut_out_png() -> bytes:
    """A PNG with a transparent background around a red square."""

    image = Image.new("RGBA", (800, 800), (0, 0, 0, 0))
    image.paste((255, 0, 0, 255), (200, 200, 600, 600))

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _open(field) -> Image.Image:
    with field.storage.open(field.name, "rb") as stored:
        image = Image.open(BytesIO(stored.read()))
        image.load()
    return image


def test_original_loses_exif_and_gps_and_is_turned_upright():
    source = BytesIO(phone_photo())
    assert has_metadata(source)

    processed = process_product_image(source, original_name="IMG_0001.JPEG")
    original_bytes = processed.original.read()
    original = Image.open(BytesIO(original_bytes))

    assert original.format == "JPEG"
    assert processed.original.name.endswith(".jpg")
    assert original.size == (2000, 3000)
    assert not original.getexif()
    assert not original.getexif().get_ifd(GPS_IFD)
    assert not has_metadata(BytesIO(original_bytes))


def test_display_and_thumbnail_are_webp_within_their_sizes():
    processed = process_product_image(
        BytesIO(phone_photo()), original_name="photo.jpg"
    )

    display = Image.open(BytesIO(processed.display.read()))
    thumbnail = Image.open(BytesIO(processed.thumbnail.read()))

    assert display.format == thumbnail.format == "WEBP"
    assert max(display.size) == 1600
    assert max(thumbnail.size) == 640


def test_png_keeps_its_transparency():
    processed = process_product_image(
        BytesIO(cut_out_png()), original_name="cut-out.png"
    )

    original = Image.open(BytesIO(processed.original.read()))
    thumbnail = Image.open(BytesIO(processed.thumbnail.read()))

    assert original.format == "PNG"
    assert original.mode == "RGBA"
    assert original.getpixel((0, 0))[3] == 0
    assert thumbnail.mode == "RGBA"
    assert thumbnail.getpixel((0, 0))[3] == 0


@pytest.mark.django_db
def test_upload_stores_a_clean_original_and_a_display_picture(tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path):
        product = product_factory()

        change = change_product_image(
            product=product,
            uploaded_image=SimpleUploadedFile(
                "IMG_0001.jpg", phone_photo(), content_type="image/jpeg"
            ),
        )
        change.commit()
        profile = product.profile
        profile.refresh_from_db()

        assert not _open(profile.image).getexif()
        assert profile.display.name.startswith("products/display/")
        assert max(_open(profile.display).size) == 1600
        assert product_display_url(profile) == profile.display.url


@pytest.mark.django_db
def test_removing_the_picture_removes_the_display_picture_too(tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path):
        product = product_factory()
        change_product_image(
            product=product,
            uploaded_image=SimpleUploadedFile(
                "a.png", cut_out_png(), content_type="image/png"
            ),
        ).commit()
        profile = product.profile
        profile.refresh_from_db()
        display_name = profile.display.name

        change_product_image(product=product, remove_image=True).commit()
        profile.refresh_from_db()

        assert not profile.display
        assert not profile.display.storage.exists(display_name)


@pytest.mark.django_db
def test_rebuild_command_cleans_old_originals_and_adds_display(tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path):
        product = product_factory()
        profile = product.profile
        # As before originals were cleaned: stored as uploaded, no display.
        profile.image.save("old.jpg", ContentFile(phone_photo()), save=False)
        profile.save(update_fields=["image"])
        old_name = profile.image.name

        call_command("rebuild_product_images", "--missing-only")
        profile.refresh_from_db()

        assert profile.display
        assert profile.thumbnail
        assert profile.image.name != old_name
        assert not profile.image.storage.exists(old_name)
        assert not _open(profile.image).getexif()


@pytest.mark.django_db
def test_rebuild_leaves_a_clean_original_as_it_is(tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path):
        product = product_factory()
        change_product_image(
            product=product,
            uploaded_image=SimpleUploadedFile(
                "a.png", cut_out_png(), content_type="image/png"
            ),
        ).commit()
        profile = product.profile
        profile.refresh_from_db()
        original_name = profile.image.name
        old_display = profile.display.name

        call_command("rebuild_product_images")
        profile.refresh_from_db()

        assert profile.image.name == original_name
        assert profile.display.name != old_display
        assert not profile.display.storage.exists(old_display)

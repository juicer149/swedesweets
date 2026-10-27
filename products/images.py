from __future__ import annotations

from hashlib import sha256

from django.conf import settings
from django.core.cache import cache

from products.models import Product, ProductProfile


def product_image_url(
    product: Product,
) -> str | None:
    """The product's small picture, else its full one, else None."""

    try:
        profile = product.profile
    except ProductProfile.DoesNotExist:
        return None

    if profile.thumbnail:
        return _image_url(profile.thumbnail)

    if profile.image:
        return _image_url(profile.image)

    return None


def product_display_url(
    profile: ProductProfile | None,
) -> str | None:
    """The product's large picture (product page, "Open image"): the
    display picture, else the original, else None."""

    if profile is None:
        return None

    if profile.display:
        return _image_url(profile.display)

    if profile.image:
        return _image_url(profile.image)

    return None


def _image_url(field) -> str:
    """Reuse a signed URL briefly, leaving most of its one-hour life unused.

    Image names change on replacement. Storage identity keeps separate buckets
    apart, and only existing authorised page views expose these URLs.
    """
    if not getattr(settings, "USE_S3_MEDIA", False):
        return field.url
    storage = field.storage
    identity = "|".join(str(value) for value in (
        getattr(storage, "bucket_name", ""),
        getattr(storage, "endpoint_url", ""),
        field.name,
    ))
    key = "product-image-url:" + sha256(identity.encode()).hexdigest()
    return cache.get_or_set(key, lambda: field.url, timeout=300)

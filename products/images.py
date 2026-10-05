from __future__ import annotations

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
        return profile.thumbnail.url

    if profile.image:
        return profile.image.url

    return None

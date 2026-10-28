"""Compact customer variant metadata, shared by retail and business carts."""
from django.utils.translation import gettext

from products.models import Product, ProductProfile, ProductVariant


def cart_choice_label(product: Product, variant: ProductVariant) -> str:
    """Only a genuine choice; old sole variant names are internal data."""
    profile = getattr(product, "profile", None)
    merchandise = profile and profile.category == ProductProfile.Category.MERCHANDISE
    if not merchandise and len(list(product.variants.all())) < 2:
        return ""
    names = {product.name.casefold(), product.display_name.casefold()}
    return variant.label.strip() if variant.label.casefold() not in names else ""


def cart_variant_label(product: Product, variant: ProductVariant) -> str:
    """A size for merchandise; weight (and a genuine choice) for food.

    Callers prefetch variants so this does not introduce per-row queries.
    """
    label = cart_choice_label(product, variant)
    profile = getattr(product, "profile", None)
    if profile and profile.category == ProductProfile.Category.MERCHANDISE:
        return label
    weight = gettext("%(weight)s g") % {"weight": variant.weight_per_unit}
    if label.casefold().replace(" ", "") == weight.casefold().replace(" ", ""):
        return weight
    return f"{label} · {weight}" if label else weight

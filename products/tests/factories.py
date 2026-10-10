from __future__ import annotations

from products.models import Product, ProductVariant
from products.services import add_variant, create_product


def product_factory(
    *,
    brand: str = "OLW",
    name: str = "Grill Chips",
    weight_per_unit: int = 275,
    stock_unit: str = Product.StockUnit.BOX,
    internal_number: int | None = None,
    manufacturer: str = "",
    vegan: bool = False,
) -> Product:
    result = create_product(
        brand=brand,
        name=name,
        weight_per_unit=weight_per_unit,
        stock_unit=stock_unit,
        internal_number=internal_number,
        manufacturer=manufacturer,
        vegan=vegan,
    )
    return result.item


def variant_factory(
    *,
    product: Product,
    label: str,
    first_label: str = "Original",
    position: int | None = None,
    weight_per_unit: int | None = None,
    active: bool = True,
) -> ProductVariant:
    """Another variant of a product, through add_variant (product_factory
    gives each product its only, unlabelled variant; adding one labels that
    one `first_label`)."""

    variant = add_variant(
        product=product,
        label=label,
        first_label=first_label,
        weight_per_unit=weight_per_unit,
    )

    changed = []

    if position is not None:
        variant.position = position
        changed.append("position")

    if not active:
        variant.active = False
        changed.append("active")

    if changed:
        variant.save(update_fields=changed)

    return variant

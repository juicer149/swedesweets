from __future__ import annotations

from products.models import Product, ProductVariant
from products.services import create_product


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
    position: int | None = None,
    weight_per_unit: int | None = None,
    active: bool = True,
) -> ProductVariant:
    """Another variant of a product (product_factory gives each product its
    only variant). The SKU follows the rule for labelled variants: the
    product's SKU plus the label."""

    if position is None:
        position = product.variants.count() + 1

    return ProductVariant.objects.create(
        product=product,
        label=label,
        position=position,
        sku=f"{product.sku}-{label.upper().replace(' ', '')}",
        weight_per_unit=(
            weight_per_unit
            if weight_per_unit is not None
            else product.weight_per_unit
        ),
        active=active,
    )

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from django.db.models import QuerySet

from common.table_tools import normalize_sort
from products.models import Product

PRODUCT_FILTER_ALL = ""
PRODUCT_FILTER_ACTIVE = "active"
PRODUCT_FILTER_INACTIVE = "inactive"

DEFAULT_PRODUCT_SORT = "number"

PRODUCT_SORTS: dict[str, tuple[str, ...]] = {
    "number": ("internal_number", "brand", "name", "weight_per_unit", "sku"),
    "-number": ("-internal_number", "brand", "name", "weight_per_unit", "sku"),
    "product": ("name", "brand", "weight_per_unit", "sku"),
    "-product": ("-name", "brand", "weight_per_unit", "sku"),
    "brand": ("brand", "name", "weight_per_unit", "sku"),
    "-brand": ("-brand", "name", "weight_per_unit", "sku"),
    "manufacturer": ("manufacturer", "brand", "name", "sku"),
    "-manufacturer": ("-manufacturer", "brand", "name", "sku"),
    "sku": ("sku",),
    "-sku": ("-sku",),
    "weight": ("weight_per_unit", "brand", "name", "sku"),
    "-weight": ("-weight_per_unit", "brand", "name", "sku"),
    "unit": ("stock_unit", "brand", "name", "sku"),
    "-unit": ("-stock_unit", "brand", "name", "sku"),
    "status": ("active", "brand", "name", "weight_per_unit"),
    "-status": ("-active", "brand", "name", "weight_per_unit"),
    "vegan": ("-vegan", "brand", "name", "sku"),
    "-vegan": ("vegan", "brand", "name", "sku"),
}


def get_product_by_sku(*, sku: str) -> Product:
    return Product.objects.get(sku=sku.strip().upper())


def list_products(
    *,
    status: str | None = None,
    sort: str | None = None,
) -> QuerySet[Product]:
    normalized_sort = normalize_sort(
        sort,
        allowed_sorts=PRODUCT_SORTS,
        default_sort=DEFAULT_PRODUCT_SORT,
    )

    products = Product.objects.select_related("profile")

    if status == PRODUCT_FILTER_ACTIVE:
        products = products.filter(active=True)

    if status == PRODUCT_FILTER_INACTIVE:
        products = products.filter(active=False)

    return products.order_by(*PRODUCT_SORTS[normalized_sort])


class ProductActivityKind(StrEnum):
    CREATED = "created"
    EDITED = "edited"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"


@dataclass(frozen=True, slots=True)
class ProductActivity:
    occurred_at: datetime
    kind: ProductActivityKind
    product: Product


_PRODUCT_ACTIVITY_SPECS = (
    (
        "created_by",
        "created_at",
        ProductActivityKind.CREATED,
    ),
    (
        "edited_by",
        "edited_at",
        ProductActivityKind.EDITED,
    ),
    (
        "activated_by",
        "activated_at",
        ProductActivityKind.ACTIVATED,
    ),
    (
        "deactivated_by",
        "deactivated_at",
        ProductActivityKind.DEACTIVATED,
    ),
)


def list_product_activity_for_actor(
    *,
    actor,
    limit: int,
) -> tuple[ProductActivity, ...]:
    activities: list[ProductActivity] = []

    for actor_field, occurred_at_field, kind in _PRODUCT_ACTIVITY_SPECS:
        products = (
            Product.objects
            .filter(
                **{
                    actor_field: actor,
                    f"{occurred_at_field}__isnull": False,
                }
            )
            .order_by(f"-{occurred_at_field}")[:limit]
        )

        activities.extend(
            ProductActivity(
                occurred_at=getattr(
                    product,
                    occurred_at_field,
                ),
                kind=kind,
                product=product,
            )
            for product in products
        )

    return tuple(
        sorted(
            activities,
            key=lambda activity: activity.occurred_at,
            reverse=True,
        )[:limit]
    )

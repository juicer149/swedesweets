from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from catalog.models import Product, ProductCategory


def list_orderable_products():
    """
    Return active products that may be ordered.

    Conceptually this belongs to catalog because it answers:
    "Which products currently exist and are orderable?"
    """
    return list(
        Product.objects
        .filter(is_active=True)
        .select_related("category")
        .order_by("category__sort_order", "category__name", "code")
    )


def list_active_products_grouped_by_category():
    """
    Return categories with active products prefetched into `active_products`.

    This supports the public/store browsing view.
    """
    return (
        ProductCategory.objects
        .all()
        .prefetch_related(
            Prefetch(
                "products",
                queryset=Product.objects.filter(is_active=True),
                to_attr="active_products",
            )
        )
    )


def get_product_detail(*, product_id: int):
    """
    Return a single product with common related data loaded.
    """
    return get_object_or_404(
        Product.objects.select_related("category").prefetch_related("tags"),
        id=product_id,
    )

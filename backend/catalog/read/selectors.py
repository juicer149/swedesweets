from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from catalog.models import Product, ProductCategory


def list_orderable_products():
    """
    Return products that may currently be ordered by stores.

    This selector answers the catalog question:
    "Which products are orderable right now?"

    The result is used by the ordering app, but the source of truth
    for orderability lives in catalog.
    """
    return list(
        Product.objects
        .filter(is_orderable=True)
        .select_related("category")
        .order_by("category__sort_order", "category__name", "code")
    )


def list_visible_products_grouped_by_category():
    """
    Return categories with visible products prefetched into `visible_products`.

    This supports the public catalog page. Only categories containing at least
    one visible product are returned.
    """
    visible_products = Product.objects.filter(
        is_visible=True,
    ).select_related("category").prefetch_related("tags")

    return (
        ProductCategory.objects
        .filter(products__is_visible=True)
        .distinct()
        .prefetch_related(
            Prefetch(
                "products",
                queryset=visible_products.order_by("code"),
                to_attr="visible_products",
            )
        )
        .order_by("sort_order", "name")
    )


def get_product_detail(*, product_id: int):
    """
    Return one visible product with common related data loaded.

    Product detail is treated as a public catalog view, so invisible products
    are not exposed here.
    """
    return get_object_or_404(
        Product.objects
        .filter(is_visible=True)
        .select_related("category")
        .prefetch_related("tags"),
        id=product_id,
    )

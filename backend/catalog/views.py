from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from .models import ProductCategory, Product


def product_list(request):
    """
    Display active products grouped by category.

    Acts as the main browsing view for store users (mobile-first).
    """
    categories = ProductCategory.objects.all().prefetch_related(
            Prefetch(
                "products",
                queryset=Product.objects.filter(is_active=True),
                to_attr="active_products"
            )
        )

    return render(
        request,
        "catalog/product_list.html",
        {"categories": categories},
    )

def product_detail(request, product_id):
    """
    Display details for a single product.

    Acts as the main product detail view for store users (mobile-first).
    """
    product = get_object_or_404(Product, id=product_id)

    return render(
        request,
        "catalog/product_detail.html",
        {"product": product},
    )

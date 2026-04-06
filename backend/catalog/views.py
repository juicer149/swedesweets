from django.shortcuts import render

from .read.selectors import (
    get_product_detail,
    list_active_products_grouped_by_category,
)


def product_list(request):
    categories = list_active_products_grouped_by_category()

    return render(
        request,
        "catalog/product_list.html",
        {"categories": categories},
    )


def product_detail(request, product_id):
    product = get_product_detail(product_id=product_id)

    return render(
        request,
        "catalog/product_detail.html",
        {"product": product},
    )

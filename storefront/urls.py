from django.urls import path

from storefront import (
    cart_views,
    views,
    checkout_views,
)
from storefront.catalog import views as catalog_views


app_name = "storefront"


urlpatterns = [
    path(
        "",
        catalog_views.product_list,
        name="product_list",
    ),
    path(
        "products/<int:product_id>/",
        catalog_views.product_detail,
        name="product_detail",
    ),
    path(
        "cart/",
        cart_views.cart,
        name="cart",
    ),
    path(
        "cart/add/<int:product_id>/",
        catalog_views.add_to_cart,
        name="add_to_cart",
    ),
    path(
        "cart/navbar/",
        cart_views.navbar_cart_fragment,
        name="navbar_cart_fragment",
    ),
    path(
        "cart/lines/<int:cart_line_id>/quantity/",
        cart_views.set_cart_line_quantity,
        name="set_cart_line_quantity",
    ),
    path(
        "cart/lines/<int:cart_line_id>/remove/",
        cart_views.remove_cart_line,
        name="remove_cart_line",
    ),
    path(
        "checkout/cities/",
        checkout_views.checkout_cities,
        name="checkout_cities",
    ),
    path(
        "checkout/",
        checkout_views.checkout_details,
        name="checkout",
    ),
    path(
        "checkout/<uuid:checkout_id>/",
        checkout_views.checkout_review,
        name="checkout_review",
    ),
    path(
        "checkout/<uuid:checkout_id>/pay/",
        checkout_views.checkout_pay,
        name="checkout_pay",
    ),
    path(
        "payment/<uuid:checkout_id>/return/",
        views.payment_return,
        name="payment_return",
    ),
]

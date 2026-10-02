from __future__ import annotations

from django.urls import path

from business_portal import views
from business_portal.catalog import views as catalog_views
from business_portal.orders import navbar_views, repeat_views
from business_portal.orders import views as order_views
from business_portal.store import views as store_views

app_name = "business_portal"


urlpatterns = [
    path(
        "",
        views.index,
        name="index",
    ),
    path(
        "store/edit/",
        store_views.edit_store,
        name="edit_store",
    ),
    path(
        "orders/",
        order_views.orders,
        name="orders",
    ),
    path(
        "orders/<int:order_id>/",
        order_views.order_detail,
        name="order_detail",
    ),
    path(
        "orders/<int:order_id>/repeat/",
        repeat_views.repeat_order,
        name="repeat_order",
    ),
    path(
        "cart/",
        order_views.cart,
        name="cart",
    ),
    path(
        "cart/navbar/",
        navbar_views.navbar_cart_fragment,
        name="navbar_cart_fragment",
    ),
    path(
        "cart/review/",
        order_views.cart_review,
        name="cart_review",
    ),
    path(
        "cart/lines/<int:cart_line_id>/quantity/",
        order_views.set_cart_line_quantity,
        name="set_cart_line_quantity",
    ),
    path(
        "cart/lines/<int:cart_line_id>/remove/",
        order_views.remove_cart_line,
        name="remove_cart_line",
    ),
    path(
        "catalog/",
        catalog_views.catalog,
        name="catalog",
    ),
    path(
        "catalog/<int:product_id>/",
        catalog_views.product_detail,
        name="catalog_product",
    ),
    path(
        "catalog/<int:product_id>/add/",
        catalog_views.add_product,
        name="catalog_add_product",
    ),
    path(
        "contact/",
        views.contact,
        name="contact",
    ),
    path(
        "faq/",
        views.faq,
        name="faq",
    ),
]

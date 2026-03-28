from django.urls import path
from .views import product_list, product_detail

urlpatterns = [
    # Catalog of all products
    path("", product_list, name="product_list"),

    # Detail view for a single product
    path( "<int:product_id>/", product_detail, name="product_detail"),
]

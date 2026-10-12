from __future__ import annotations

from django.urls import path

from ops_portal.products import views

app_name = "ops_products"

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create, name="create"),
    path("<int:product_pk>/", views.detail, name="detail"),
    path("<int:product_pk>/edit/", views.edit, name="edit"),
    path(
        "<int:product_pk>/catalog/",
        views.edit_catalog,
        name="edit_catalog",
    ),
]

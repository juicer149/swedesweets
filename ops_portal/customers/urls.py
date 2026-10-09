from __future__ import annotations

from django.urls import path

from ops_portal.customers import views

app_name = "ops_customers"

urlpatterns = [
    path("", views.index, name="index"),
    path("new/", views.create, name="create"),
    path("invite/", views.invite, name="invite"),
    path(
        "<int:customer_pk>/invite/",
        views.invite_login,
        name="invite_login",
    ),
    path("<int:customer_pk>/", views.detail, name="detail"),
    path("<int:customer_pk>/edit/", views.edit, name="edit"),
]

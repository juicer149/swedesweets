from django.urls import path

from . import views

app_name = "ordering"

urlpatterns = [
    path("orders/new/", views.order_create, name="order_create"),
    path("portal/orders/", views.order_history, name="order_history"),
    path("portal/orders/<uuid:order_id>/", views.order_detail, name="order_detail"),
]

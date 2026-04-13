from django.urls import path

from . import views

app_name = "ordering"

urlpatterns = [
    path("orders/new/", views.order_create, name="order_create"),
    path("portal/orders/", views.order_history, name="order_history"),
    path("portal/orders/<uuid:order_id>/", views.order_detail, name="order_detail"),
    path("staff/orders/history/", views.staff_order_history, name="staff_order_history"),
    path("staff/orders/<uuid:order_id>/", views.staff_order_work, name="staff_order_work"),
]

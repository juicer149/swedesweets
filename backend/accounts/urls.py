from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("stores/", views.store_list, name="store_list"),
    path("portal/", views.portal, name="portal"),
    path("accounts/store/", views.store_portal, name="store_portal"),
    path("accounts/staff/", views.staff_portal, name="staff_portal"),
]

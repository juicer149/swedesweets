from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("stores/", views.store_list, name="store_list"),
    path("portal/", views.portal, name="portal"),
    path("accounts/store/", views.store_portal, name="store_portal"),
    path("accounts/staff/restricted/", views.restricted_staff_portal, name="restricted_staff_portal"),
    path("accounts/staff/", views.staff_portal, name="staff_portal"),
    path("accounts/staff/create/", views.account_create_choice, name="account_create_choice"),
    path("accounts/staff/create/store/", views.create_store_account_view, name="create_store_account"),
    path("accounts/staff/create/staff/", views.create_staff_account_view, name="create_staff_account"),
]

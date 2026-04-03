from django.urls import path
from . import views

urlpatterns = [
    path("stores/", views.store_list, name="store_list"),
    path("portal/", views.portal, name="portal"),
]

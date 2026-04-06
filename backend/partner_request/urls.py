from django.urls import path

from .views import apply, apply_thanks

urlpatterns = [
    path("apply/", apply, name="apply"),
    path("thanks/", apply_thanks, name="apply_thanks"),
]

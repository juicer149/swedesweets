from __future__ import annotations

from django.urls import path

from accounts import views

app_name = "accounts"


urlpatterns = [
    path(
        "me/",
        views.me,
        name="me",
    ),
    path(
        "inactive/",
        views.inactive,
        name="inactive",
    ),
]

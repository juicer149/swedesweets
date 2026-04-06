from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "login/", 
        auth_views.LoginView.as_view(template_name="auth/login.html"), 
        name="login"
        ),
    path(
        "logout/", 
        auth_views.LogoutView.as_view(next_page="pages:home"), 
        name="logout"
        ),

    path("", include("accounts.urls")), 
    path("", include("ordering.urls")),
    path("", include("pages.urls")),  # Home page and other static pages
    path("products/", include("catalog.urls")),  # Product listing and details
    path("", include("partner_request.urls")),  # Partner application form
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

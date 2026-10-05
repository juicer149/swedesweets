from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeView,
    PasswordResetView,
)
from django.urls import (
    include,
    path,
)

from accounts.forms import (
    AccountPasswordChangeForm,
    LoginForm,
    ResetRequestForm,
)
from config import views as config_views
from ops_portal.dashboard import views as dashboard_views
from storefront import views as storefront_views

urlpatterns = [
    path(
        "i18n/",
        include("django.conf.urls.i18n"),
    ),
    path(
        "",
        storefront_views.landing,
        name="index",
    ),
    path(
        "",
        include(
            "storefront.public_urls",
            namespace="public_site",
        ),
    ),
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "accounts/after-login/",
        config_views.after_login,
        name="after_login",
    ),
    path(
        "accounts/",
        include(
            "accounts.urls",
            namespace="accounts",
        ),
    ),
    # Before django.contrib.auth.urls, so these views win.
    path(
        "accounts/login/",
        LoginView.as_view(authentication_form=LoginForm),
        name="login",
    ),
    path(
        "accounts/password_reset/",
        PasswordResetView.as_view(form_class=ResetRequestForm),
        name="password_reset",
    ),
    path(
        "accounts/password_change/",
        PasswordChangeView.as_view(form_class=AccountPasswordChangeForm),
        name="password_change",
    ),
    path(
        "accounts/",
        include("django.contrib.auth.urls"),
    ),
    path(
        "ops/",
        dashboard_views.index,
        name="ops_dashboard",
    ),
    path(
        "ops/accounts/",
        include(
            "ops_portal.accounts.urls",
            namespace="ops_accounts",
        ),
    ),
    path(
        "ops/orders/",
        include(
            "ops_portal.orders.urls",
            namespace="ops_orders",
        ),
    ),
    path(
        "ops/inventory/",
        include(
            "ops_portal.inventory.urls",
            namespace="ops_inventory",
        ),
    ),
    path(
        "ops/products/",
        include(
            "ops_portal.products.urls",
            namespace="ops_products",
        ),
    ),
    path(
        "ops/customers/",
        include(
            "ops_portal.customers.urls",
            namespace="ops_customers",
        ),
    ),
    path(
        "my/",
        include(
            "business_portal.urls",
            namespace="business_portal",
        ),
    ),
    path(
        "payments/",
        include(
            "config.payment_urls",
            namespace="payments",
        ),
    ),
    path(
        "shop/",
        include(
            "storefront.urls",
            namespace="storefront",
        ),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

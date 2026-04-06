from django.apps import AppConfig


class AccountsConfig(AppConfig):    
    """
    App for internal store identity and store-facing access.

    The name 'accounts' is historical. In practice this app owns the Store
    entity and the views around public store discovery and partner portal access.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

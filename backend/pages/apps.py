from django.apps import AppConfig


class PagesConfig(AppConfig):
    """
    Thin public content app.

    This app exists to render simple public-facing pages such as the homepage,
    about page, and contact page. It intentionally contains no models and no
    business logic.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "pages"

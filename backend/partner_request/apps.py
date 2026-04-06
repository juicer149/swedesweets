from django.apps import AppConfig


class PartnerRequestConfig(AppConfig):
    """
    Public inbound app for partner interest requests.

    Responsibility:
    - Accept contact requests from potential retail partners
    - Store them for manual admin review

    Non-responsibility:
    - Account provisioning
    - Store creation
    - Internal onboarding workflows
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "partner_request"

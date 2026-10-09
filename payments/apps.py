from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = 'payments'

    def ready(self):
        from payments import checks  # noqa: F401  (registers the checks)

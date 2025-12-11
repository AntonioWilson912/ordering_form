from django.apps import AppConfig


class CompanyAppConfig(AppConfig):
    name = 'company_app'

    def ready(self):
        from . import signals  # noqa: F401
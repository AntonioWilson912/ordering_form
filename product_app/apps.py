from django.apps import AppConfig


class ProductAppConfig(AppConfig):
    name = 'product_app'

    def ready(self):
        from . import signals  # noqa: F401
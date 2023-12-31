from django.apps import AppConfig


class CheckwebConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "checkweb"

    def ready(self):
        import checkweb.signals

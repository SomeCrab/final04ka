from django.apps import AppConfig


class CrabookingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crabooking"


    def ready(self):
        from . import signals
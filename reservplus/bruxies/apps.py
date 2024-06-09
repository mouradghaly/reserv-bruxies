from django.apps import AppConfig
import scheduler


class BruxiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bruxies'

class AppNameConfig(AppConfig):
    name = 'bruxies'
    def ready(self):
        scheduler.start()
from django.apps import AppConfig


class AICoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'farman.apps.ai_core'
    verbose_name = 'هوش مصنوعی و پردازش داده'

    def ready(self):
        # Import signals if needed
        pass

from django.apps import AppConfig


class FilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.files'
    verbose_name = 'مدیریت فایل‌ها'

    def ready(self):
        # Import signals here
        pass

from django.apps import AppConfig

MODULE_NAME = 'payroll'


class PayrollConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = MODULE_NAME

import random
from django.apps import apps


class CodeGenerator:
    @classmethod
    def generate_unique_code(cls, app_label, model_name, code_field_name, length):
        allowed_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789'
        code = ''.join(random.choice(allowed_chars) for _ in range(length))

        while cls._code_exists(app_label, model_name, code_field_name, code):
            code = ''.join(random.choice(allowed_chars) for _ in range(length))

        return code

    @classmethod
    def _code_exists(cls, app_label, model_name, code_field_name, code):
        model = apps.get_model(app_label=app_label, model_name=model_name)
        try:
            return model.objects.filter(**{code_field_name: code}).exists()
        except model.DoesNotExist:
            return False

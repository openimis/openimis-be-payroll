from django.apps import AppConfig

from core.custom_filters import CustomFilterRegistryPoint

MODULE_NAME = 'payroll'

DEFAULT_CONFIG = {
    "gql_payment_point_search_perms": ["201001"],
    "gql_payment_point_create_perms": ["201002"],
    "gql_payment_point_update_perms": ["201003"],
    "gql_payment_point_delete_perms": ["201004"],
    "gql_payroll_search_perms": ["202001"],
    "gql_payroll_create_perms": ["202002"],
    "gql_payroll_delete_perms": ["202004"],
}


class PayrollConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = MODULE_NAME

    gql_payment_point_search_perms = None
    gql_payment_point_create_perms = None
    gql_payment_point_update_perms = None
    gql_payment_point_delete_perms = None
    gql_payroll_search_perms = None
    gql_payroll_create_perms = None
    gql_payroll_delete_perms = None

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(self.name, DEFAULT_CONFIG)
        self.__load_config(cfg)

    @classmethod
    def __load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(PayrollConfig, field):
                setattr(PayrollConfig, field, cfg[field])

        from social_protection.custom_filters import BenefitPlanCustomFilterWizard
        CustomFilterRegistryPoint.register_custom_filters(
            module_name=cls.name,
            custom_filter_class_list=[BenefitPlanCustomFilterWizard]
        )
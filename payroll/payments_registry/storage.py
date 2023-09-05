import logging
from typing import List

from payroll.payments_registry.registry_point import PaymentsMethodRegistryPoint
from payroll.strategies import StrategyOfPaymentInterface

logger = logging.getLogger(__name__)


class PaymentMethodStorage:

    @classmethod
    def get_all_available_payment_methods(cls) -> List[StrategyOfPaymentInterface]:
        return PaymentsMethodRegistryPoint.REGISTERED_PAYMENT_METHODS

    @classmethod
    def get_chosen_payment_method(cls, payment_method_name: str) -> StrategyOfPaymentInterface:
        chosen_method = None
        for method_info in PaymentsMethodRegistryPoint.REGISTERED_PAYMENT_METHODS:
            if method_info['name'] == payment_method_name:
                chosen_method = method_info['class_reference']
        return chosen_method

import logging
from typing import List

from payroll.payments_registry.registry_point import PaymentsMethodRegistryPoint
from payroll.strategies import StrategyOfPaymentInterface

logger = logging.getLogger(__name__)


class PaymentMethodStorage:

    @classmethod
    def get_all_available_payment_methods(cls) -> List[StrategyOfPaymentInterface]:
        return PaymentsMethodRegistryPoint.REGISTERED_PAYMENT_METHODS

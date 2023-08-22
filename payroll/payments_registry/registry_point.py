import logging

from typing import List

from payroll.strategies import StrategyOfPaymentInterface


logger = logging.getLogger(__name__)


class PaymentsMethodRegistryPoint:
    """
    Class responsible for handling the registration of payments method.

    REGISTERED_PAYMENT_METHODS:
    A dictionary that collects registered implementations of payments method.
    The structure of the dictionary is as follows:
    """

    REGISTERED_PAYMENT_METHODS = []

    @classmethod
    def register_payment_method(
        cls,
        payment_method_class_list: List[StrategyOfPaymentInterface]
    ) -> None:
        """
        Register payment methods which defines the strategy of payments including connection to adaptors.

        This method registers the provided list of objects as payment method.

        :param payment_method_class_list: A list of objects representing the payment method implementations.
        :type payment_method_class_list: list

        :return: This method does not return anything.
        :rtype: None
        """
        for payment_method_class in payment_method_class_list:
            cls.__collect_payment_method(payment_method_class)

    @classmethod
    def __collect_payment_method(
        cls,
        strategy_payment_method_class: StrategyOfPaymentInterface
    ) -> None:
        cls.REGISTERED_PAYMENT_METHODS.append({
            "class_reference": strategy_payment_method_class,
            "name": strategy_payment_method_class.__class__.__name__
        })

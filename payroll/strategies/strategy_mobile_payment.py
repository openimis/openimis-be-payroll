from payroll.strategies.strategy_of_payments_interface import StrategyOfPaymentInterface


class StrategyMobilePayment(StrategyOfPaymentInterface):

    @classmethod
    def accept_payroll(cls, **kwargs):
        pass

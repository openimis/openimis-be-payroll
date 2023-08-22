from payroll.strategies.strategy_of_payments_interface import StrategyOfPaymentInterface


class StrategyOnlinePayment(StrategyOfPaymentInterface):

    @classmethod
    def accept_payroll(cls, **kwargs):
        pass

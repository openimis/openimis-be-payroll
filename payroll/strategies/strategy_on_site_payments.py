from payroll.strategies.strategy_of_payments_interface import StrategyOfPaymentInterface


class StrategyOnSitePayment(StrategyOfPaymentInterface):

    @classmethod
    def accept_payroll(cls, payroll, user, **kwargs):
        pass

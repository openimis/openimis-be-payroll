from payroll.strategies.strategy_of_payments_interface import StrategyOfPaymentInterface


class StrategyPaymentBankTransferPayment(StrategyOfPaymentInterface):

    @classmethod
    def accept_payroll(cls, payroll, **kwargs):
        pass

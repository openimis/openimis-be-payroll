from payroll.strategies.strategy_of_payments_interface import StrategyOfPaymentInterface


class StrategyOnSitePayment(StrategyOfPaymentInterface):

    @classmethod
    def accept_payroll(cls, payroll, user, **kwargs):
        cls._change_status_to_ongoing(payroll, user)

    @classmethod
    def _change_status_to_ongoing(cls, payroll, user):
        from payroll.models import PayrollStatus
        payroll.status = PayrollStatus.ONGOING
        payroll.save(username=user.login_name)

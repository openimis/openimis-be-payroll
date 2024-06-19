import logging
from celery import shared_task

from core.models import User
from payroll.models import Payroll, PayrollStatus, BenefitConsumptionStatus
from payroll.strategies import StrategyOnlinePayment
from payroll.payments_registry import PaymentMethodStorage

logger = logging.getLogger(__name__)


@shared_task
def send_requests_to_gateway_payment(payroll_id, user_id):
    payroll = Payroll.objects.get(id=payroll_id)
    strategy = PaymentMethodStorage.get_chosen_payment_method(payroll.payment_method)
    if strategy:
        user = User.objects.get(id=user_id)
        strategy.initialize_payment_gateway()
        strategy.make_payment_for_payroll(payroll, user)


@shared_task
def send_request_to_reconcile(payroll_id, user_id):
    payroll = Payroll.objects.get(id=payroll_id)
    user = User.objects.get(id=user_id)
    strategy = StrategyOnlinePayment
    strategy.initialize_payment_gateway()
    benefits = strategy.get_benefits_attached_to_payroll(payroll, BenefitConsumptionStatus.APPROVE_FOR_PAYMENT)
    payment_gateway_connector = strategy.PAYMENT_GATEWAY
    benefits_to_reconcile = []
    for benefit in benefits:
        if payment_gateway_connector.reconcile(benefit.code, benefit.amount):
            benefits_to_reconcile.append(benefit)
        else:
            # Handle the case where a benefit payment is rejected
            logger.info(f"Payment for benefit ({benefit.code}) was rejected.")
    if benefits_to_reconcile:
        strategy.reconcile_benefit_consumption(benefits_to_reconcile, user)
    strategy.change_status_of_payroll(payroll, PayrollStatus.RECONCILED, user)

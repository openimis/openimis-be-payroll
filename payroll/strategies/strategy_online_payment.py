from django.db.models import Q, Sum
from django.db import transaction

from core.signals import register_service_signal
from payroll.strategies.strategy_of_payments_interface import StrategyOfPaymentInterface


class StrategyOnlinePayment(StrategyOfPaymentInterface):
    WORKFLOW_NAME = "payment-adaptor"
    WORKFLOW_GROUP = "openimis-coremis-payment-adaptor"

    @classmethod
    def accept_payroll(cls, payroll, user, **kwargs):
        cls._send_data_to_adaptor(payroll, user, **kwargs)

    @classmethod
    def acknowledge_of_reponse_view(cls, payroll, response_from_gateway, user, rejected_bills):
        # save response coming from payment gateway in json_ext
        cls._save_payroll_data(payroll, user, response_from_gateway)

    @classmethod
    @transaction.atomic
    def reconcile_payroll(cls, payroll, user):
        from payroll.models import PayrollStatus
        cls.change_status_of_payroll(payroll, PayrollStatus.RECONCILED, user)

    @classmethod
    def _create_bill_payment_for_paid_bill(cls, bill, user, current_date):
        from django.contrib.contenttypes.models import ContentType
        from invoice.models import DetailPaymentInvoice, PaymentInvoice
        from invoice.services import PaymentInvoiceService
        # Create a BillPayment object for the 'Paid' bill
        bill_payment = {
            "code_tp": bill.code_tp,
            "code_ext": bill.code_ext,
            "code_receipt": bill.code,
            "label": bill.terms,
            'reconciliation_status': PaymentInvoice.ReconciliationStatus.RECONCILIATED,
            "fees": 0.0,
            "amount_received": bill.amount_total,
            "date_payment": current_date,
            'payment_origin': "online payment",
            'payer_ref': 'payment reference',
            'payer_name': 'payer name',
            "json_ext": {}
        }

        bill_payment_details = {
            'subject_type': ContentType.objects.get_for_model(bill),
            'subject': bill,
            'status': DetailPaymentInvoice.DetailPaymentStatus.ACCEPTED,
            'fees': 0.0,
            'amount': bill.amount_total,
            'reconcilation_id': '',
            'reconcilation_date': current_date,
        }
        bill_payment_details = DetailPaymentInvoice(**bill_payment_details)
        payment_service = PaymentInvoiceService(user)
        payment_service.create_with_detail(bill_payment, bill_payment_details)

    @classmethod
    def _get_payroll_bills_amount(cls, payroll):
        from payroll.models import Payroll
        payroll_with_benefit_sum = Payroll.objects.filter(id=payroll.id).annotate(
            total_benefit_amount=Sum('payrollbenefitconsumption__benefit__amount')
        ).first()
        return payroll_with_benefit_sum.total_benefit_amount

    @classmethod
    def _get_benefits_attached_to_payroll(cls, payroll):
        from payroll.models import BenefitConsumption
        filters = Q(
            payrollbenefitconsumption__payroll_id=payroll.id,
            is_deleted=False,
            payrollbenefitconsumption__is_deleted=False,
            payrollbenefitconsumption__payroll__is_deleted=False,
        )
        benefits = BenefitConsumption.objects.filter(filters)
        return benefits

    @classmethod
    def _get_benefits_to_string(cls, benefits):
        benefits_uuids = [str(benefit.id) for benefit in benefits]
        benefits_uuids_string = ",".join(benefits_uuids)
        return benefits_uuids_string

    @classmethod
    def _send_data_to_adaptor(cls, payroll, user, **kwargs):
        total_amount = cls._get_payroll_bills_amount(payroll)
        bills = cls._get_benefits_attached_to_payroll(payroll)
        bill_uuids_string = cls._get_benefits_to_string(bills)
        # TODO - add here connection with gateway endpoint
        from payroll.models import PayrollStatus
        cls.change_status_of_payroll(payroll, PayrollStatus.APPROVE_FOR_PAYMENT, user)

    @classmethod
    def _save_payroll_data(cls, payroll, user, response_from_gateway):
        json_ext = payroll.json_ext if payroll.json_ext else {}
        json_ext['response_from_gateway'] = response_from_gateway
        payroll.json_ext = json_ext
        payroll.save(username=user.username)
        cls._create_payroll_reconcilation_task(payroll, user)

    @classmethod
    @register_service_signal('online_payments.create_task')
    def _create_payroll_reconcilation_task(cls, payroll, user):
        from payroll.apps import PayrollConfig
        from tasks_management.services import TaskService
        from tasks_management.apps import TasksManagementConfig
        from tasks_management.models import Task
        TaskService(user).create({
            'source': 'payroll_reconciliation',
            'entity': payroll,
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': PayrollConfig.payroll_reconciliation_event,
        })

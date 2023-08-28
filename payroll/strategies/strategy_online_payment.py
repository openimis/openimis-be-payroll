from django.db.models import Q, Sum

from payroll.strategies.strategy_of_payments_interface import StrategyOfPaymentInterface
from workflow.services import WorkflowService
from workflow.systems.base import WorkflowHandler


class StrategyOnlinePayment(StrategyOfPaymentInterface):
    WORKFLOW_NAME = "payment-adaptor"
    WORKFLOW_GROUP = "openimis-coremis-payment-adaptor"

    @classmethod
    def accept_payroll(cls, payroll, user, **kwargs):
        workflow = cls._get_payment_workflow(cls.WORKFLOW_NAME, cls.WORKFLOW_GROUP)
        cls._send_data_to_adaptor(workflow, payroll, user, **kwargs)

    @classmethod
    def _get_payment_workflow(cls, workflow_name: str, workflow_group: str):
        result = WorkflowService.get_workflows(workflow_name, workflow_group)
        workflows = result.get('data', {}).get('workflows')
        workflow = workflows[0]
        return workflow

    @classmethod
    def _get_payroll_bills_amount(cls, payroll):
        bills = cls._get_bill_attached_to_payroll(payroll)
        total_amount = str(bills.aggregate(total_amount=Sum('amount_total'))['total_amount'])
        return total_amount

    @classmethod
    def _get_bill_attached_to_payroll(cls, payroll):
        from invoice.models import Bill
        filters = [Q(payrollbill__payroll_id=payroll.uuid,
                     is_deleted=False,
                     payrollbill__is_deleted=False,
                     payrollbill__payroll__is_deleted=False,
                     status=Bill.Status.VALIDATED
                     )]
        bills = Bill.objects.filter(*filters)
        return bills

    @classmethod
    def _send_data_to_adaptor(cls, workflow: WorkflowHandler, payroll, user, **kwargs):
        total_amount = cls._get_payroll_bills_amount(payroll)
        workflow.run({
            'user_uuid': str(user.id),
            'payroll_uuid': str(payroll.uuid),
            'payroll_amount': total_amount,
        })
        from payroll.models import PayrollStatus
        payroll.status = PayrollStatus.ONGOING
        payroll.save(username=user.login_name)

    @classmethod
    def acknowledge_of_reponse_view(cls, payroll, response_from_gateway, user):
        # save response coming from payment gateway in json_ext
        from payroll.models import PayrollStatus
        payroll.json_ext = response_from_gateway
        payroll.status = PayrollStatus.AWAITING_FOR_RECONCILIATION
        payroll.save(username=user.username)
        # update bill attached to the payroll
        from invoice.models import Bill
        bills = cls._get_bill_attached_to_payroll(payroll)
        bills.update(status=Bill.Status.PAYED)

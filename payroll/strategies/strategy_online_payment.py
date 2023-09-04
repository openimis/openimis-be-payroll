from django.db.models import Q, Sum

from core.signals import register_service_signal
from payroll.strategies.strategy_of_payments_interface import StrategyOfPaymentInterface
from tasks_management.services import TaskService
from tasks_management.apps import TasksManagementConfig
from tasks_management.models import Task
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
    def acknowledge_of_reponse_view(cls, payroll, response_from_gateway, user):
        # save response coming from payment gateway in json_ext
        cls._save_payroll_data(payroll, user, response_from_gateway)
        # update bill attached to the payroll
        cls._save_bill_data(payroll)

    @classmethod
    def reconcile_payroll(cls, payroll, user):
        from payroll.models import PayrollStatus
        payroll.status = PayrollStatus.RECONCILIATED
        payroll.save(username=user.username)

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
    def _save_payroll_data(cls, payroll, user, response_from_gateway):
        from payroll.models import PayrollStatus
        json_ext = payroll.json_ext
        json_ext['response_from_gateway'] = response_from_gateway
        payroll.json_ext = json_ext
        payroll.status = PayrollStatus.AWAITING_FOR_RECONCILIATION
        payroll.save(username=user.username)
        cls._create_payroll_reconcilation_task(payroll, user)

    @classmethod
    def _save_bill_data(cls, payroll):
        from invoice.models import Bill
        bills = cls._get_bill_attached_to_payroll(payroll)
        bills.update(status=Bill.Status.PAYED)

    @register_service_signal('online_payments.create_task')
    def _create_payroll_reconcilation_task(self, payroll, user):
        from payroll.apps import PayrollConfig
        TaskService(user).create({
            'source': 'payroll_reconciliation',
            'entity': payroll,
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': PayrollConfig.payroll_reconciliation_event,
        })

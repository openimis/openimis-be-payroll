import logging

from django.db import transaction
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from core.custom_filters import CustomFilterWizardStorage
from core.services import BaseService
from core.signals import register_service_signal
from invoice.models import Bill
from payroll.apps import PayrollConfig
from payroll.models import PaymentPoint, Payroll, PayrollBill
from payroll.validation import PaymentPointValidation, PayrollValidation
from core.services.utils import output_exception, check_authentication
from social_protection.models import Beneficiary
from tasks_management.apps import TasksManagementConfig
from tasks_management.models import Task
from tasks_management.services import TaskService

logger = logging.getLogger(__name__)


class PaymentPointService(BaseService):
    OBJECT_TYPE = PaymentPoint

    def __init__(self, user, validation_class=PaymentPointValidation):
        super().__init__(user, validation_class)

    @register_service_signal('payment_point_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('payment_point_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal('payment_point_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)


class PayrollService(BaseService):
    OBJECT_TYPE = Payroll

    def __init__(self, user, validation_class=PayrollValidation):
        super().__init__(user, validation_class)

    @check_authentication
    @register_service_signal('payroll_service.create')
    def create(self, obj_data):
        try:
            with transaction.atomic():
                included_unpaid = obj_data.pop("included_unpaid", False)
                obj_data = self._adjust_create_payload(obj_data)
                bills_queryset = self._get_bills_queryset(obj_data, included_unpaid)
                obj_data_and_bills = {**obj_data, "bills": bills_queryset}
                self.validation_class.validate_create(self.user, **obj_data_and_bills)
                obj_ = self.OBJECT_TYPE(**obj_data)
                dict_representation = self.save_instance(obj_)
                payroll_id = dict_representation["data"]["id"]
                self._create_payroll_bills(bills_queryset, payroll_id)
                # create task for accepting or rejecting payroll
                self._create_accept_payroll_task(payroll_id, obj_data)
                return dict_representation
        except Exception as exc:
            return output_exception(model_name=self.OBJECT_TYPE.__name__, method="create", exception=exc)

    @register_service_signal('payroll_service.update')
    def update(self, obj_data):
        raise NotImplementedError()

    @check_authentication
    @register_service_signal('payroll_service.delete')
    def delete(self, obj_data):
        try:
            with transaction.atomic():
                self.validation_class.validate_delete(self.user, **obj_data)
                obj_ = self.OBJECT_TYPE.objects.filter(id=obj_data['id']).first()
                PayrollBill.objects.filter(payroll=obj_).delete()
                return self.delete_instance(obj_)
        except Exception as exc:
            return output_exception(model_name=self.OBJECT_TYPE.__name__, method="delete", exception=exc)

    @register_service_signal('payroll_service.create_task')
    def _create_accept_payroll_task(self, payroll_id, obj_data):
        payroll_to_accept = Payroll.objects.get(id=payroll_id)
        TaskService(self.user).create({
            'source': 'payroll',
            'entity': payroll_to_accept,
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': PayrollConfig.payroll_accept_event,
            'data': f"{obj_data}"
        })

    def _create_payroll_bills(self, bills_queryset, payroll_id):
        for bill in bills_queryset:
            payroll_bill = PayrollBill(bill_id=bill.id, payroll_id=payroll_id)
            payroll_bill.save(username=self.user.username)

    def _get_bills_queryset(self, obj_data, included_unpaid):
        benefit_plan_id = obj_data.get("benefit_plan_id")
        date_from = obj_data.get("date_valid_from")
        date_to = obj_data.get("date_valid_to")
        json_ext = obj_data.get("json_ext")

        custom_filters = [
            criterion["custom_filter_condition"]
            for criterion in json_ext.get("advanced_criteria", [])
        ] if json_ext else []

        beneficiaries_queryset = Beneficiary.objects.filter(
            benefit_plan__id=benefit_plan_id
        )

        if custom_filters:
            beneficiaries_queryset = CustomFilterWizardStorage.build_custom_filters_queryset(
                PayrollConfig.name,
                "BenefitPlan",
                custom_filters,
                beneficiaries_queryset,
            )

        beneficiary_ids = list(beneficiaries_queryset.values_list('id', flat=True))

        bills_queryset = Bill.objects.filter(
            is_deleted=False,
            date_bill__range=(date_from, date_to),
            subject_type=ContentType.objects.get_for_model(Beneficiary),
            subject_id__in=beneficiary_ids,
            status__in=[Bill.Status.VALIDATED],
        )

        bills_queryset = bills_queryset.filter(
            Q(payrollbill__isnull=True) | Q(payrollbill__is_deleted=True)
        )

        if included_unpaid:
            bills_queryset = bills_queryset.filter(json_ext__unpaid=True)
        else:
            bills_queryset = bills_queryset.filter(
                Q(json_ext__unpaid=False) |
                Q(json_ext__unpaid__isnull=True)
            )

        return bills_queryset

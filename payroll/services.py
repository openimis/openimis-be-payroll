import logging

from django.db import transaction

from core.custom_filters import CustomFilterWizardStorage
from core.services import BaseService
from core.signals import register_service_signal
from payroll.apps import PayrollConfig
from payroll.models import (
    PaymentPoint,
    Payroll,
    PayrollBenefitConsumption,
    BenefitConsumption,
    BenefitAttachment
)
from payroll.payments_registry import PaymentMethodStorage
from payroll.validation import PaymentPointValidation, PayrollValidation, BenefitConsumptionValidation
from payroll.strategies import StrategyOfPaymentInterface
from calculation.services import get_calculation_object
from core.services.utils import output_exception, check_authentication
from contribution_plan.models import PaymentPlan
from social_protection.models import Beneficiary, BeneficiaryStatus
from tasks_management.apps import TasksManagementConfig
from tasks_management.models import Task
from tasks_management.services import TaskService, _get_std_task_data_payload


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
                obj_data = self._adjust_create_payload(obj_data)
                payment_plan = self._get_payment_plan(obj_data)
                date_valid_from, date_valid_to = self._get_dates_parameter(obj_data)
                beneficiaries_queryset = self._select_beneficiary_based_on_criteria(obj_data, payment_plan)
                payroll, dict_representation = self._save_payroll(obj_data)
                self._generate_benefits(
                    payment_plan,
                    beneficiaries_queryset,
                    date_valid_from,
                    date_valid_to,
                    payroll
                )
                self.create_accept_payroll_task(payroll.id, obj_data)
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
                StrategyOfPaymentInterface.remove_benefits_from_rejected_payroll(payroll=obj_)
                return self.delete_instance(obj_)
        except Exception as exc:
            return output_exception(model_name=self.OBJECT_TYPE.__name__, method="delete", exception=exc)

    @check_authentication
    @register_service_signal('payroll_service.attach_benefit_to_payroll')
    def attach_benefit_to_payroll(self, payroll_id, benefit_id):
        payroll_benefit = PayrollBenefitConsumption(payroll_id=payroll_id, benefit_id=benefit_id)
        payroll_benefit.save(username=self.user.username)

    @register_service_signal('payroll_service.create_task')
    def create_accept_payroll_task(self, payroll_id, obj_data):
        payroll_to_accept = Payroll.objects.get(id=payroll_id)
        data = {**obj_data, 'id': payroll_id}
        TaskService(self.user).create({
            'source': 'payroll',
            'entity': payroll_to_accept,
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': PayrollConfig.payroll_accept_event,
            'data': _get_std_task_data_payload(data)
        })

    @register_service_signal('payroll_service.close_payroll')
    def close_payroll(self, obj_data):
        payroll_to_close = Payroll.objects.get(id=obj_data['id'])
        data = {'id': payroll_to_close.id}
        TaskService(self.user).create({
            'source': 'payroll_reconciliation',
            'entity': payroll_to_close,
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': PayrollConfig.payroll_reconciliation_event,
            'data': _get_std_task_data_payload(data)
        })

    @register_service_signal('payroll_service.reject_approve_payroll')
    def reject_approved_payroll(self, obj_data):
        payroll_to_reject = Payroll.objects.get(id=obj_data['id'])
        data = {'id': payroll_to_reject.id}
        TaskService(self.user).create({
            'source': 'payroll_reject',
            'entity': payroll_to_reject,
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': PayrollConfig.payroll_reject_event,
            'data': _get_std_task_data_payload(data)
        })

    def _save_payroll(self, obj_data):
        obj_ = self.OBJECT_TYPE(**obj_data)
        dict_representation = self.save_instance(obj_)
        payroll_id = dict_representation["data"]["id"]
        payroll = Payroll.objects.get(id=payroll_id)
        return payroll, dict_representation

    def _get_payment_plan(self, obj_data):
        payment_plan_id = obj_data.get("payment_plan_id")
        payment_plan = PaymentPlan.objects.get(id=payment_plan_id)
        return payment_plan

    def _get_dates_parameter(self, obj_data):
        date_valid_from = obj_data.get('date_valid_from', None)
        date_valid_to = obj_data.get('date_valid_to', None)
        return date_valid_from, date_valid_to

    def _select_beneficiary_based_on_criteria(self, obj_data, payment_plan):
        json_ext = obj_data.get("json_ext")
        custom_filters = [
            criterion["custom_filter_condition"]
            for criterion in json_ext.get("advanced_criteria", [])
        ] if json_ext else []

        beneficiaries_queryset = Beneficiary.objects.filter(
            benefit_plan__id=payment_plan.benefit_plan.id, status=BeneficiaryStatus.ACTIVE
        )

        if custom_filters:
            beneficiaries_queryset = CustomFilterWizardStorage.build_custom_filters_queryset(
                PayrollConfig.name,
                "BenefitPlan",
                custom_filters,
                beneficiaries_queryset,
            )

        return beneficiaries_queryset

    def _generate_benefits(self, payment_plan, beneficiaries_queryset, date_from, date_to, payroll):
        calculation = get_calculation_object(payment_plan.calculation)
        calculation.calculate_if_active_for_object(
            payment_plan,
            user_id=self.user.id,
            start_date=date_from, end_date=date_to,
            beneficiaries_queryset=beneficiaries_queryset,
            payroll=payroll
        )


class BenefitConsumptionService(BaseService):
    OBJECT_TYPE = BenefitConsumption

    def __init__(self, user, validation_class=BenefitConsumptionValidation):
        super().__init__(user, validation_class)

    @check_authentication
    @register_service_signal('benefit_consumption_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('benefit_consumption_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @check_authentication
    @register_service_signal('benefit_consumption_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)

    @check_authentication
    @register_service_signal('benefit_consumption_service.create_or_update_benefit_attachment')
    def create_or_update_benefit_attachment(self, bills_queryset, benefit_id):
        # remove first old attachments and save the new one
        BenefitAttachment.objects.filter(benefit_id=benefit_id).delete()
        # save new bill attachments
        for bill in bills_queryset:
            benefit_attachment = BenefitAttachment(bill_id=bill.id, benefit_id=benefit_id)
            benefit_attachment.save(username=self.user.username)

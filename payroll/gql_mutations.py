import graphene
from django.db import transaction
from django.contrib.auth.models import AnonymousUser
from pydantic.error_wrappers import ValidationError

from core.gql.gql_mutations.base_mutation import BaseHistoryModelCreateMutationMixin, BaseMutation, \
    BaseHistoryModelDeleteMutationMixin
from core.schema import OpenIMISMutation
from payroll.apps import PayrollConfig
from payroll.models import Payroll
from payroll.services import PayrollService


class CreatePayrollInput(OpenIMISMutation.Input):
    name = graphene.String(required=True, max_length=255)
    benefit_plan_id = graphene.UUID(required=True)
    payment_point_id = graphene.UUID(required=True)
    custom_filters = graphene.List(graphene.String(required=True), required=False)


class CreatePayrollMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "CreatePayrollMutation"
    _mutation_module = "payroll"
    _model = CreatePayrollInput

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.has_perms(
                PayrollConfig.gql_payroll_create_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        service = PayrollService(user)
        response = service.create(data)
        if not response['success']:
            return response
        return None

    class Input(CreatePayrollInput):
        pass


class DeletePayrollMutation(BaseHistoryModelDeleteMutationMixin, BaseMutation):
    _mutation_class = "DeletePayrollMutation"
    _mutation_module = "payroll"
    _model = Payroll

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.has_perms(
                PayrollConfig.gql_payroll_delete_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        service = PayrollService(user)
        ids = data.get('ids')
        if ids:
            with transaction.atomic():
                for id in ids:
                    service.delete({'id': id})

    class Input(OpenIMISMutation.Input):
        ids = graphene.List(graphene.UUID)

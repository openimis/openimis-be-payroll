import graphene
from gettext import gettext as _
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db import transaction

from core.gql.gql_mutations.base_mutation import BaseHistoryModelCreateMutationMixin, BaseMutation, \
    BaseHistoryModelUpdateMutationMixin, BaseHistoryModelDeleteMutationMixin
from core.schema import OpenIMISMutation
from payroll.apps import PayrollConfig
from payroll.models import PaymentPoint
from payroll.services import PaymentPointService


class CreatePaymentPointInputType(OpenIMISMutation.Input):
    name = graphene.String(required=True, max_length=255)
    location_id = graphene.Int(required=True)
    ppm_id = graphene.Int(required=True)


class UpdatePaymentPointInputType(CreatePaymentPointInputType):
    id = graphene.UUID(required=True)


class DeletePaymentPointInputType(OpenIMISMutation.Input):
    ids = graphene.List(graphene.UUID, required=True)


class CreatePaymentPointMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "CreatePaymentPointMutation"
    _mutation_module = PayrollConfig.name
    _model = PaymentPoint

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                PayrollConfig.gql_payment_point_create_perms):
            raise ValidationError(_("mutation.authentication_required"))

    @classmethod
    def _mutate(cls, user, **data):
        data.pop('client_mutation_id', None)
        data.pop('client_mutation_label', None)

        service = PaymentPointService(user)
        service.create(data)

    class Input(CreatePaymentPointInputType):
        pass


class UpdatePaymentPointMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    _mutation_class = "UpdatePaymentPointMutation"
    _mutation_module = PayrollConfig.name
    _model = PaymentPoint

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                PayrollConfig.gql_payment_point_update_perms):
            raise ValidationError(_("mutation.authentication_required"))

    @classmethod
    def _mutate(cls, user, **data):
        data.pop('client_mutation_id', None)
        data.pop('client_mutation_label', None)

        service = PaymentPointService(user)
        service.update(data)

    class Input(UpdatePaymentPointInputType):
        pass


class DeletePaymentPointMutation(BaseHistoryModelDeleteMutationMixin, BaseMutation):
    _mutation_class = "DeletePaymentPointMutation"
    _mutation_module = PayrollConfig.name
    _model = PaymentPoint

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                PayrollConfig.gql_payment_point_delete_perms):
            raise ValidationError(_("mutation.authentication_required"))

    @classmethod
    def _mutate(cls, user, **data):
        data.pop('client_mutation_id', None)
        data.pop('client_mutation_label', None)

        service = PaymentPointService(user)

        ids = data.get('ids')
        if ids:
            with transaction.atomic():
                for id in ids:
                    service.delete({'id': id})

    class Input(DeletePaymentPointInputType):
        pass

import graphene
import graphene_django_optimizer as gql_optimizer
from gettext import gettext as _
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q

from core.schema import OrderedDjangoFilterConnectionField
from core.utils import append_validity_filter
from invoice.gql.gql_types.bill_types import BillGQLType
from invoice.models import Bill
from location.services import get_ancestor_location_filter
from payroll.apps import PayrollConfig
from payroll.gql_mutations import CreatePaymentPointMutation, UpdatePaymentPointMutation, DeletePaymentPointMutation, \
    CreatePayrollMutation, DeletePayrollMutation
from payroll.gql_queries import PaymentPointGQLType, PayrollGQLType, PaymentMethodGQLType, PaymentMethodListGQLType
from payroll.models import PaymentPoint, Payroll
from payroll.payments_registry import PaymentMethodStorage


class Query(graphene.ObjectType):
    payment_point = OrderedDjangoFilterConnectionField(
        PaymentPointGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        client_mutation_id=graphene.String(),
        parent_location=graphene.String(),
        parent_location_level=graphene.Int(),
    )
    payroll = OrderedDjangoFilterConnectionField(
        PayrollGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        client_mutation_id=graphene.String(),
    )

    bill_by_payroll = OrderedDjangoFilterConnectionField(
        BillGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String(),
        payroll_uuid=graphene.UUID(required=True)
    )

    payment_methods = graphene.Field(
        PaymentMethodListGQLType,
    )

    def resolve_bill_by_payroll(self, info, **kwargs):
        Query._check_permissions(info.context.user, PayrollConfig.gql_payroll_search_perms)
        filters = [*append_validity_filter(**kwargs), Q(payrollbill__payroll_id=kwargs.get("payroll_uuid"),
                                                        is_deleted=False,
                                                        payrollbill__is_deleted=False,
                                                        payrollbill__payroll__is_deleted=False)]

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        subject_type = kwargs.get("subject_type", None)
        if subject_type:
            filters.append(Q(subject_type__model=subject_type))

        thirdparty_type = kwargs.get("thirdparty_type", None)
        if thirdparty_type:
            filters.append(Q(thirdparty_type__model=thirdparty_type))

        return gql_optimizer.query(Bill.objects.filter(*filters), info)

    def resolve_payment_point(self, info, **kwargs):
        Query._check_permissions(info.context.user, PayrollConfig.gql_payment_point_search_perms)
        filters = []

        client_mutation_id = kwargs.get("client_mutation_id")
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        parent_location = kwargs.get('parent_location')
        if parent_location:
            filters += [get_ancestor_location_filter(parent_location)]

        query = PaymentPoint.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    def resolve_payroll(self, info, **kwargs):
        Query._check_permissions(info.context.user, PayrollConfig.gql_payroll_search_perms)
        filters = append_validity_filter(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id")
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        query = Payroll.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    def resolve_payment_methods(self, info, **kwargs):
        user = info.context.user
        if type(user) is AnonymousUser or not user.id:
            raise PermissionError("Unauthorized")

        payment_methods = PaymentMethodStorage.get_all_available_payment_methods()
        gql_payment_methods = Query._build_payment_method_options(payment_methods)
        return PaymentMethodListGQLType(gql_payment_methods)

    @staticmethod
    def _build_payment_method_options(payment_methods):
        gql_payment_methods = []
        for payment_method in payment_methods:
            gql_payment_methods.append(
                PaymentMethodGQLType(
                    name=payment_method['name']
                )
            )
        return gql_payment_methods

    @staticmethod
    def _check_permissions(user, perms):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(perms):
            raise PermissionError(_("Unauthorized"))


class Mutation(graphene.ObjectType):
    create_payment_point = CreatePaymentPointMutation.Field()
    update_payment_point = UpdatePaymentPointMutation.Field()
    delete_payment_point = DeletePaymentPointMutation.Field()

    create_payroll = CreatePayrollMutation.Field()
    delete_payroll = DeletePayrollMutation.Field()

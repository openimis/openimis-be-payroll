import graphene
import graphene_django_optimizer as gql_optimizer
from gettext import gettext as _
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q

from core.schema import OrderedDjangoFilterConnectionField
from core.utils import append_validity_filter
from invoice.gql.bill import BillQueryMixin
from invoice.gql.gql_types.bill_types import BillGQLType
from invoice.models import Bill
from location.apps import LocationConfig
from payroll.apps import PayrollConfig
from payroll.gql_mutations import CreatePaymentPointMutation, UpdatePaymentPointMutation, DeletePaymentPointMutation, \
    CreatePayrollMutation, DeletePayrollMutation
from payroll.gql_queries import PaymentPointGQLType, PayrollGQLType
from payroll.models import PaymentPoint, Payroll


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

        # this code with parent_location and parent_location_level query args should be replaced with proper generic solution
        parent_location = kwargs.get('parent_location')
        if parent_location is not None:
            parent_location_level = kwargs.get('parent_location_level')
            if parent_location_level is None:
                raise NotImplementedError("Missing parentLocationLevel argument when filtering on parentLocation")
            f = "uuid"
            for i in range(len(LocationConfig.location_types) - parent_location_level - 1):
                f = "parent__" + f
            f = "location__" + f
            filters += [Q(**{f: parent_location})]

        query = PaymentPoint.objects.filter(*filters)
        gql_optimizer.query(query, info)

    def resolve_payroll(self, info, **kwargs):
        Query._check_permissions(info.context.user, PayrollConfig.gql_payroll_search_perms)
        filters = append_validity_filter(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id")
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        query = Payroll.objects.filter(*filters)
        return gql_optimizer.query(query, info)

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

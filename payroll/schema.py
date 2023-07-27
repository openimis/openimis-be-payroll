import graphene
import graphene_django_optimizer as gql_optimizer
from gettext import gettext as _
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q

from core.schema import OrderedDjangoFilterConnectionField
from payroll.apps import PayrollConfig
from payroll.gql_mutations import CreatePaymentPointMutation, UpdatePaymentPointMutation, DeletePaymentPointMutation
from payroll.gql_queries import PaymentPointGQLType
from payroll.models import PaymentPoint


class Query(graphene.ObjectType):
    payment_point = OrderedDjangoFilterConnectionField(
        PaymentPointGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        client_mutation_id=graphene.String(),
    )

    def resolve_payment_point(self, info, **kwargs):
        Query._check_permissions(info.context.user, PayrollConfig.gql_payment_point_search_perms)
        filters = []

        client_mutation_id = kwargs.get("client_mutation_id")
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        query = PaymentPoint.objects.filter(*filters)
        gql_optimizer.query(query, info)

    @staticmethod
    def _check_permissions(user, perms):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(perms):
            raise PermissionError(_("Unauthorized"))


class Mutation(graphene.ObjectType):
    create_payment_point = CreatePaymentPointMutation.Field()
    update_payment_point = UpdatePaymentPointMutation.Field()
    delete_payment_point = DeletePaymentPointMutation.Field()

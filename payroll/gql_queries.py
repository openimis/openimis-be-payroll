import graphene
from graphene_django import DjangoObjectType

from core import prefix_filterset, ExtendedConnection
from core.gql_queries import UserGQLType
from invoice.gql.gql_types.bill_types import BillGQLType
from invoice.models import Bill
from location.gql_queries import LocationGQLType
from payroll.models import PaymentPoint, Payroll
from social_protection.gql_queries import BenefitPlanGQLType


class PaymentPointGQLType(DjangoObjectType):
    uuid = graphene.String(source='uuid')

    class Meta:
        model = PaymentPoint
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "name": ["iexact", "istartswith", "icontains"],
            **prefix_filterset("location__", LocationGQLType._meta.filter_fields),
            **prefix_filterset("ppm__", UserGQLType._meta.filter_fields),

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }
        connection_class = ExtendedConnection


class PayrollGQLType(DjangoObjectType):
    uuid = graphene.String(source='uuid')
    bill = graphene.List(BillGQLType)

    class Meta:
        model = Payroll
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "name": ["iexact", "istartswith", "icontains"],
            "status": ["exact", "startswith", "contains"],
            "payment_method": ["exact", "startswith", "contains"],
            **prefix_filterset("payment_point__", PaymentPointGQLType._meta.filter_fields),
            **prefix_filterset("benefit_plan__", BenefitPlanGQLType._meta.filter_fields),

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_from": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_to": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }
        connection_class = ExtendedConnection

    def resolve_bill(self, info):
        return Bill.objects.filter(payrollbill__payroll__id=self.id,
                                   is_deleted=False,
                                   payrollbill__is_deleted=False)


class PaymentMethodGQLType(graphene.ObjectType):
    name = graphene.String()


class PaymentMethodListGQLType(graphene.ObjectType):
    payment_methods = graphene.List(PaymentMethodGQLType)

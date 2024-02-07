import graphene
from graphene_django import DjangoObjectType

from core import prefix_filterset, ExtendedConnection
from core.gql_queries import UserGQLType
from invoice.gql.gql_types.bill_types import BillGQLType
from invoice.models import Bill
from location.gql_queries import LocationGQLType
from individual.gql_queries import IndividualGQLType
from payroll.models import PaymentPoint, Payroll, BenefitConsumption, BenefitAttachment
from social_protection.gql_queries import BenefitPlanGQLType
from contribution_plan.gql import PaymentPlanGQLType
from payment_cycle.gql_queries import PaymentCycleGQLType


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


class BenefitAttachmentGQLType(DjangoObjectType):
    uuid = graphene.String(source='uuid')

    class Meta:
        model = BenefitAttachment
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            **prefix_filterset("bill__", BillGQLType._meta.filter_fields),

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_from": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_to": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }
        connection_class = ExtendedConnection


class BenefitConsumptionGQLType(DjangoObjectType):
    uuid = graphene.String(source='uuid')
    benefit_attachment = graphene.List(BenefitAttachmentGQLType)

    class Meta:
        model = BenefitConsumption
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "photo": ["iexact", "istartswith", "icontains"],
            "code": ["iexact", "istartswith", "icontains"],
            "status": ["exact", "startswith", "contains"],
            "receipt": ["exact", "startswith", "contains"],
            "date_due": ["exact", "lt", "lte", "gt", "gte"],
            **prefix_filterset("individual__", IndividualGQLType._meta.filter_fields),

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_from": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_to": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }
        connection_class = ExtendedConnection

    def resolve_benefit_attachment(self, info):
        return BenefitAttachment.objects.filter(
            benefit_id=self.id,
            is_deleted=False
        )


class PayrollGQLType(DjangoObjectType):
    uuid = graphene.String(source='uuid')
    benefit_consumption = graphene.List(BenefitConsumptionGQLType)

    class Meta:
        model = Payroll
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "name": ["iexact", "istartswith", "icontains"],
            "status": ["exact", "startswith", "contains"],
            "payment_method": ["exact", "startswith", "contains"],
            **prefix_filterset("payment_point__", PaymentPointGQLType._meta.filter_fields),
            **prefix_filterset("payment_plan__", PaymentPlanGQLType._meta.filter_fields),
            **prefix_filterset("payment_cycle__", PaymentCycleGQLType._meta.filter_fields),

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_from": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_to": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }
        connection_class = ExtendedConnection

    def resolve_benefit_consumption(self, info):
        return BenefitConsumption.objects.filter(payrollbenefitconsumption__payroll__id=self.id,
                                   is_deleted=False,
                                   payrollbenefitconsumption__is_deleted=False)


class PaymentMethodGQLType(graphene.ObjectType):
    name = graphene.String()


class PaymentMethodListGQLType(graphene.ObjectType):
    payment_methods = graphene.List(PaymentMethodGQLType)

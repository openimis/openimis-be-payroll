import json
from datetime import datetime, timedelta

from graphene import Schema
from graphene.test import Client
from django.test import TestCase

from location.models import Location
from payroll.models import Payroll, PaymentPoint
from payroll.tests.data import gql_payroll_create, gql_payroll_query, gql_payment_point_delete, gql_payroll_delete
from payroll.tests.helpers import LogInHelper, PaymentPointHelper
from payroll.schema import Query, Mutation
from social_protection.models import BenefitPlan
from social_protection.tests.data import service_add_payload


class PayrollGQLTestCase(TestCase):
    class GQLContext:
        def __init__(self, user):
            self.user = user

    user = None
    user_unauthorized = None
    gql_client = None
    gql_context = None
    gql_context_unauthorized = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = LogInHelper().get_or_create_user_api(username='username_authorized')
        cls.user_unauthorized = LogInHelper().get_or_create_user_api(username='username_unauthorized', roles=[1])
        gql_schema = Schema(
            query=Query,
            mutation=Mutation
        )
        cls.gql_client = Client(gql_schema)
        cls.gql_context = cls.GQLContext(cls.user)
        cls.gql_context_unauthorized = cls.GQLContext(cls.user_unauthorized)
        cls.name = "TestCreatePayroll"
        cls.date_valid_from, cls.date_valid_to = cls.__get_start_and_end_of_current_month()
        cls.payment_point = PaymentPointHelper().get_or_create_payment_point_api()
        cls.benefit_plan = cls.__create_benefit_plan()

    def test_query(self):
        output = self.gql_client.execute(gql_payroll_query, context=self.gql_context)
        result = output.get('data', {}).get('payroll', {})
        self.assertTrue(result)

    def test_query_unauthorized(self):
        output = self.gql_client.execute(gql_payroll_query, context=self.gql_context_unauthorized)
        error = next(iter(output.get('errors', [])), {}).get('message', None)
        self.assertTrue(error)

    def test_create(self):
        payload = gql_payroll_create % (
            self.name,
            self.benefit_plan.id,
            self.payment_point.id,
            self.date_valid_from,
            self.date_valid_to,
        )
        output = self.gql_client.execute(payload, context=self.gql_context)
        self.assertTrue(Payroll.objects.filter(
            name=self.name,
            benefit_plan_id=self.benefit_plan.id,
            payment_point_id=self.payment_point.id,
            date_valid_from=self.date_valid_from,
            date_valid_to=self.date_valid_to,
            is_deleted=False)
                        .exists())

    def test_create_unauthorized(self):
        payload = gql_payroll_create % (
            self.name,
            self.benefit_plan.id,
            self.payment_point.id,
            self.date_valid_from,
            self.date_valid_to,
        )
        output = self.gql_client.execute(payload, context=self.gql_context_unauthorized)
        self.assertTrue(Payroll.objects.filter(
            name=self.name,
            benefit_plan_id=self.benefit_plan.id,
            payment_point_id=self.payment_point.id,
            date_valid_from=self.date_valid_from,
            date_valid_to=self.date_valid_to,
            is_deleted=False)
                        .exists())

    def test_delete(self):
        payroll = Payroll(name=self.name,
                          benefit_plan_id=self.benefit_plan.id,
                          payment_point_id=self.payment_point.id,
                          date_valid_from=self.date_valid_from,
                          date_valid_to=self.date_valid_to,
                          )
        payroll.save(username=self.user.username)
        payload = gql_payroll_delete % json.dumps([str(payroll.id)])
        output = self.gql_client.execute(payload, context=self.gql_context)
        self.assertTrue(Payroll.objects.filter(id=payroll.id, is_deleted=True).exists())

    def test_delete_unauthorized(self):
        payroll = Payroll(name=self.name,
                          benefit_plan_id=self.benefit_plan.id,
                          payment_point_id=self.payment_point.id,
                          date_valid_from=self.date_valid_from,
                          date_valid_to=self.date_valid_to,
                          )
        payroll.save(username=self.user.username)
        payload = gql_payroll_delete % json.dumps([str(payroll.id)])
        output = self.gql_client.execute(payload, context=self.gql_context_unauthorized)
        self.assertTrue(Payroll.objects.filter(id=payroll.id, is_deleted=False).exists())

    @classmethod
    def __create_benefit_plan(cls):
        object_data = {
            **service_add_payload
        }

        benefit_plan = BenefitPlan(**object_data)
        benefit_plan.save(username=cls.user.username)

        return benefit_plan

    @classmethod
    def __get_start_and_end_of_current_month(cls):
        today = datetime.today()
        # Set date_valid_from to the beginning of the current month
        date_valid_from = today.replace(day=1).strftime("%Y-%m-%d")

        # Calculate the last day of the current month
        next_month = today.replace(day=28) + timedelta(days=4)  # Adding 4 days to ensure we move to the next month
        date_valid_to = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")

        return date_valid_from, date_valid_to

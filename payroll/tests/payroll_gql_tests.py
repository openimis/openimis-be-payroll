import json
from datetime import datetime, timedelta

from graphene import Schema
from graphene.test import Client
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from individual.models import Individual
from individual.tests.data import service_add_individual_payload
from invoice.models import Bill
from payroll.models import Payroll, PayrollBill
from payroll.tests.data import gql_payroll_create, gql_payroll_query, gql_payroll_delete, \
    gql_payroll_create_no_json_ext
from payroll.tests.helpers import LogInHelper, PaymentPointHelper
from payroll.schema import Query, Mutation
from social_protection.models import BenefitPlan, Beneficiary
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
        cls.status = "CREATED"
        cls.payment_method = "TestPaymentMethod"
        cls.date_valid_from, cls.date_valid_to = cls.__get_start_and_end_of_current_month()
        cls.payment_point = PaymentPointHelper().get_or_create_payment_point_api()
        cls.benefit_plan = cls.__create_benefit_plan()
        cls.individual = cls.__create_individual()
        cls.subject_type = ContentType.objects.get_for_model(Beneficiary)
        cls.beneficiary = cls.__create_beneficiary()
        cls.bill = cls.__create_bill()
        cls.json_ext_able_bodied_false = """{\\"advanced_criteria\\": [{\\"custom_filter_condition\\": \\"able_bodied__boolean=False\\"}]}"""
        cls.json_ext_able_bodied_true = """{\\"advanced_criteria\\": [{\\"custom_filter_condition\\": \\"able_bodied__boolean=True\\"}]}"""

    def test_query(self):
        output = self.gql_client.execute(gql_payroll_query, context=self.gql_context)
        result = output.get('data', {}).get('payroll', {})
        self.assertTrue(result)

    def test_query_unauthorized(self):
        output = self.gql_client.execute(gql_payroll_query, context=self.gql_context_unauthorized)
        error = next(iter(output.get('errors', [])), {}).get('message', None)
        self.assertTrue(error)

    def create_payroll(self, name, json_ext):
        payload = gql_payroll_create % (
            name,
            self.benefit_plan.id,
            self.payment_point.id,
            self.payment_method,
            self.status,
            self.date_valid_from,
            self.date_valid_to,
            json_ext,
        )
        output = self.gql_client.execute(payload, context=self.gql_context)
        payroll = Payroll.objects.filter(
            name=name,
            benefit_plan_id=self.benefit_plan.id,
            payment_point_id=self.payment_point.id,
            payment_method=self.payment_method,
            status=self.status,
            date_valid_from=self.date_valid_from,
            date_valid_to=self.date_valid_to,
            is_deleted=False,
        )
        return payroll

    def create_payroll_no_json_ext(self, name):
        payload = gql_payroll_create_no_json_ext % (
            name,
            self.benefit_plan.id,
            self.payment_point.id,
            self.payment_method,
            self.status,
            self.date_valid_from,
            self.date_valid_to,
        )
        output = self.gql_client.execute(payload, context=self.gql_context)
        payroll = Payroll.objects.filter(
            name=name,
            benefit_plan_id=self.benefit_plan.id,
            payment_point_id=self.payment_point.id,
            payment_method=self.payment_method,
            status=self.status,
            date_valid_from=self.date_valid_from,
            date_valid_to=self.date_valid_to,
            is_deleted=False,
        )
        return payroll

    def delete_payroll_and_check_bill(self, payroll):
        payroll_bill = PayrollBill.objects.filter(
            bill=self.bill, payroll=payroll.first())
        self.assertEqual(payroll_bill.count(), 1)
        payroll_bill.delete()
        payroll.delete()
        self.assertEqual(PayrollBill.objects.all().count(), 0)
        self.assertFalse(payroll.exists())

    def test_create_fail_due_to_lack_of_bills_for_given_criteria(self):
        payroll = self.create_payroll(self.name, self.json_ext_able_bodied_false)
        self.assertFalse(payroll.exists())

    def test_create_no_advanced_criteria(self):
        payroll = self.create_payroll_no_json_ext(self.name)
        self.assertTrue(payroll.exists())
        self.delete_payroll_and_check_bill(payroll)

    def test_create_full(self):
        payroll = self.create_payroll(self.name, self.json_ext_able_bodied_true)
        self.assertTrue(payroll.exists())
        self.delete_payroll_and_check_bill(payroll)

    def test_create_fail_due_to_empty_name(self):
        payroll = self.create_payroll("", self.json_ext_able_bodied_true)
        self.assertFalse(payroll.exists())

    def test_create_fail_due_to_one_bill_assigment(self):
        tmp_name = f"{self.name}-tmp"
        payroll_tmp = self.create_payroll(tmp_name, self.json_ext_able_bodied_true)
        self.assertTrue(payroll_tmp.exists())

        payroll = self.create_payroll(self.name, self.json_ext_able_bodied_true)
        self.assertFalse(payroll.exists())

        self.delete_payroll_and_check_bill(payroll_tmp)

    def test_create_unauthorized(self):
        payload = gql_payroll_create % (
            self.name,
            self.benefit_plan.id,
            self.payment_point.id,
            self.payment_method,
            self.status,
            self.date_valid_from,
            self.date_valid_to,
            self.json_ext_able_bodied_false,
        )
        output = self.gql_client.execute(payload, context=self.gql_context_unauthorized)
        self.assertFalse(
            Payroll.objects.filter(
                name=self.name,
                benefit_plan_id=self.benefit_plan.id,
                payment_point_id=self.payment_point.id,
                payment_method=self.payment_method,
                status=self.status,
                date_valid_from=self.date_valid_from,
                date_valid_to=self.date_valid_to,
                json_ext=self.json_ext_able_bodied_false,
                is_deleted=False,
            ).exists()
        )

    def test_delete(self):
        payroll = Payroll(name=self.name,
                          benefit_plan_id=self.benefit_plan.id,
                          payment_point_id=self.payment_point.id,
                          payment_method=self.payment_method,
                          status=self.status,
                          date_valid_from=self.date_valid_from,
                          date_valid_to=self.date_valid_to,
                          json_ext=self.json_ext_able_bodied_false,
                          )
        payroll.save(username=self.user.username)
        payroll_bill = PayrollBill(payroll=payroll, bill=self.bill)
        payroll_bill.save(username=self.user.username)
        payload = gql_payroll_delete % json.dumps([str(payroll.id)])
        output = self.gql_client.execute(payload, context=self.gql_context)
        self.assertTrue(Payroll.objects.filter(id=payroll.id, is_deleted=True).exists())
        self.assertEqual(PayrollBill.objects.filter(payroll=payroll, bill=self.bill).count(), 0)

    def test_delete_unauthorized(self):
        payroll = Payroll(name=self.name,
                          benefit_plan_id=self.benefit_plan.id,
                          payment_point_id=self.payment_point.id,
                          payment_method=self.payment_method,
                          status=self.status,
                          date_valid_from=self.date_valid_from,
                          date_valid_to=self.date_valid_to,
                          json_ext=self.json_ext_able_bodied_true,
                          )
        payroll.save(username=self.user.username)
        payroll_bill = PayrollBill(payroll=payroll, bill=self.bill)
        payroll_bill.save(username=self.user.username)
        payload = gql_payroll_delete % json.dumps([str(payroll.id)])
        output = self.gql_client.execute(payload, context=self.gql_context_unauthorized)
        self.assertTrue(Payroll.objects.filter(id=payroll.id, is_deleted=False).exists())
        self.assertEqual(PayrollBill.objects.filter(payroll=payroll, bill=self.bill).count(), 1)
        payroll_bill.delete(username=self.user.username)
        self.assertTrue(PayrollBill.objects.filter(payroll=payroll, bill=self.bill, is_deleted=True))

    def test_check_bill_included_unpaid(self):
        self.bill.json_ext = {"unpaid": True}
        self.bill.save(username=self.user.username)
        bills_queryset_not_paid = Bill.objects.filter(json_ext__unpaid=True)
        bills_queryset = Bill.objects.filter(
            Q(json_ext__unpaid=False) |
            Q(json_ext__unpaid__isnull=True)
        )
        self.assertGreaterEqual(bills_queryset_not_paid.count(), 1)
        self.assertEqual(bills_queryset.count(), 0)

    def test_check_bill_not_included_unpaid(self):
        bills_queryset_not_paid = Bill.objects.filter(json_ext__unpaid=True)
        bills_queryset = Bill.objects.filter(
            Q(json_ext__unpaid=False) |
            Q(json_ext__unpaid__isnull=True)
        )
        self.assertEqual(bills_queryset_not_paid.count(), 0)
        self.assertGreaterEqual(bills_queryset.count(), 1)

    @classmethod
    def __create_benefit_plan(cls):
        object_data = {
            **service_add_payload
        }

        benefit_plan = BenefitPlan(**object_data)
        benefit_plan.save(username=cls.user.username)

        return benefit_plan

    @classmethod
    def __create_individual(cls):
        object_data = {
            **service_add_individual_payload
        }

        individual = Individual(**object_data)
        individual.save(username=cls.user.username)

        return individual

    @classmethod
    def __create_beneficiary(cls):
        object_data = {
            "individual": cls.individual,
            "benefit_plan": cls.benefit_plan,
            "json_ext": {"able_bodied": True}
        }
        beneficiary = Beneficiary(**object_data)
        beneficiary.save(username=cls.user.username)
        return beneficiary

    @classmethod
    def __create_bill(cls):
        object_data = {
            "subject_type": cls.subject_type,
            "subject_id": cls.beneficiary.id,
            "status": Bill.Status.VALIDATED
        }
        bill = Bill(**object_data)
        bill.save(username=cls.user.username)
        return bill

    @classmethod
    def __get_start_and_end_of_current_month(cls):
        today = datetime.today()
        # Set date_valid_from to the beginning of the current month
        date_valid_from = today.replace(day=1).strftime("%Y-%m-%d")

        # Calculate the last day of the current month
        next_month = today.replace(day=28) + timedelta(days=4)  # Adding 4 days to ensure we move to the next month
        date_valid_to = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")

        return date_valid_from, date_valid_to

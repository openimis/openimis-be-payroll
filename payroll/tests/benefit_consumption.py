import copy

from django.test import TestCase

from individual.models import Individual
from payroll.models import BenefitConsumption, BenefitAttachment
from payroll.services import BenefitConsumptionService
from payroll.tests.data import benefit_consumption_data_test, benefit_consumption_data_update
from individual.tests.data import service_add_individual_payload
from core.test_helpers import LogInHelper
from invoice.models import Bill
from invoice.tests.helpers import create_test_bill


class BenefitConsumptionServiceTest(TestCase):
    user = None
    service = None
    query_all = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = LogInHelper().get_or_create_user_api()
        cls.service = BenefitConsumptionService(cls.user)
        cls.individual = cls.__create_test_individual()
        cls.bills_queryset = cls.__create_test_bill(cls.individual)

    def test_add_benefit_consumption(self):
        result = self.service.create(benefit_consumption_data_test)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid', None)
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().code, benefit_consumption_data_test.get('code'))

    def test_update_benefit_consumption(self):
        result = self.service.create(benefit_consumption_data_test)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        update_payload = copy.deepcopy(benefit_consumption_data_update)
        update_payload['id'] = uuid
        result = self.service.update(update_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().code, update_payload.get('code'))

    def test_delete_benefit_consumption(self):
        result = self.service.create(benefit_consumption_data_test)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        delete_payload = {'id': uuid}
        result = self.service.delete(delete_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 0)

    def test_add_attachment_to_benefit_consumption(self):
        result = self.service.create(benefit_consumption_data_test)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        benefit = BenefitConsumption.objects.get(id=uuid)
        self.service.create_or_update_benefit_attachment(self.bills_queryset, benefit)
        benefit_attachments = BenefitAttachment.objects.filter(benefit=benefit)
        self.assertEqual(benefit_attachments.count(), 2)

    @classmethod
    def __create_test_individual(cls):
        individual = Individual(**service_add_individual_payload)
        return individual.save(username=cls.user.username)

    @classmethod
    def __create_test_bill(cls, individual):
        bill_1 = create_test_bill(subject=individual, thirdparty=individual, user=cls.user, code="12345-a")
        bill_2 = create_test_bill(subject=individual, thirdparty=individual, user=cls.user, code="12345-a")
        bill_ids = [bill_1.id, bill_2.id]
        bill_queryset = Bill.objects.filter(id__in=bill_ids)
        return bill_queryset

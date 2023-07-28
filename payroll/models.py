from django.db import models
from django.contrib.postgres.fields import ArrayField

from core.models import HistoryModel
from invoice.models import Bill
from social_protection.models import BenefitPlan


class PaymentPoint(HistoryModel):
    pass


class Payroll(HistoryModel):
    name = models.CharField(max_length=255, blank=False, null=False)
    benefit_plan = models.ForeignKey(BenefitPlan, on_delete=models.DO_NOTHING)
    payment_point = models.ForeignKey(PaymentPoint, on_delete=models.DO_NOTHING)
    custom_filters = ArrayField(models.CharField(max_length=255, blank=False, null=False), null=True)


class PayrollBill(HistoryModel):
    # 1:n it is ensured by service
    payroll = models.ForeignKey(Payroll, on_delete=models.DO_NOTHING)
    bill = models.ForeignKey(Bill, on_delete=models.DO_NOTHING)

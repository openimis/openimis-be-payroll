from django.db import models

from core.fields import DateField
from core.models import HistoryModel, InteractiveUser, HistoryBusinessModel
from invoice.models import Bill
from location.models import Location
from social_protection.models import BenefitPlan


class PaymentPoint(HistoryModel):
    name = models.CharField(max_length=255)
    location = models.ForeignKey(Location, models.DO_NOTHING)
    ppm = models.ForeignKey(InteractiveUser, models.DO_NOTHING)


class Payroll(HistoryBusinessModel):
    name = models.CharField(max_length=255, blank=False, null=False)
    benefit_plan = models.ForeignKey(BenefitPlan, on_delete=models.DO_NOTHING)
    payment_point = models.ForeignKey(PaymentPoint, on_delete=models.DO_NOTHING)


class PayrollBill(HistoryModel):
    # 1:n it is ensured by the service
    payroll = models.ForeignKey(Payroll, on_delete=models.DO_NOTHING)
    bill = models.ForeignKey(Bill, on_delete=models.DO_NOTHING)

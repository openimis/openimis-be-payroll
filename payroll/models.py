from django.db import models
from django.utils.translation import gettext as _

from core.models import HistoryModel, HistoryBusinessModel, User
from invoice.models import Bill
from location.models import Location
from social_protection.models import BenefitPlan


class PayrollStatus(models.TextChoices):
    CREATED = "CREATED", _("CREATED")
    ONGOING = "ONGOING", _("ONGOING")
    AWAITING_FOR_RECONCILIATION = "AWAITING_FOR_RECONCILIATION", _("AWAITING_FOR_RECONCILIATION")
    RECONCILIATED = "RECONCILIATED", _("RECONCILIATED")


class PaymentPoint(HistoryModel):
    name = models.CharField(max_length=255)
    location = models.ForeignKey(Location, models.DO_NOTHING)
    ppm = models.ForeignKey(User, models.DO_NOTHING, null=True)


class Payroll(HistoryBusinessModel):
    name = models.CharField(max_length=255, blank=False, null=False)
    benefit_plan = models.ForeignKey(BenefitPlan, on_delete=models.DO_NOTHING)
    payment_point = models.ForeignKey(PaymentPoint, on_delete=models.DO_NOTHING, null=True)
    status = models.CharField(
        max_length=100, choices=PayrollStatus.choices, default=PayrollStatus.CREATED, null=False
    )
    payment_method = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Payroll {self.name} - {self.uuid}"


class PayrollBill(HistoryModel):
    # 1:n it is ensured by the service
    payroll = models.ForeignKey(Payroll, on_delete=models.DO_NOTHING)
    bill = models.ForeignKey(Bill, on_delete=models.DO_NOTHING)


class PaymentAdaptorHistory(HistoryModel):
    payroll = models.ForeignKey(Payroll, on_delete=models.DO_NOTHING)
    total_amount = models.CharField(max_length=255, blank=True, null=True)
    bills_ids = models.JSONField()

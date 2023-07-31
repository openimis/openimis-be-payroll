from django.db import models

from core.models import HistoryModel, InteractiveUser
from location.models import Location


class PaymentPoint(HistoryModel):
    name = models.CharField(max_length=255)
    location = models.ForeignKey(Location, models.DO_NOTHING)
    ppm = models.ForeignKey(InteractiveUser, models.DO_NOTHING)

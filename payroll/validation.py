from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from core.validation import BaseModelValidation
from payroll.models import Payroll, PayrollBill


class PayrollValidation(BaseModelValidation):
    OBJECT_TYPE = Payroll

    @classmethod
    def validate_create(cls, user, **data):
        errors = validate_payroll(data)
        if errors:
            raise ValidationError(errors)
        super().validate_create(user, **data)


def validate_payroll(data):
    return [
        *are_bills_in_data(data),
        *validate_one_payroll_per_bill(data)
    ]


def are_bills_in_data(data):
    bill_ids = data.get('bill_ids', None)
    if not bill_ids:
        return [{"message": _("payroll.validation.payroll.no_bills_in_data")}]
    return []


def validate_one_payroll_per_bill(data):
    bill_ids = data.get('bill_ids', [])
    query = PayrollBill.objects.filters(bill__in=bill_ids)
    if query.exists():
        payroll_bill_ids = list(query.values_list('id', flat=True))
        return [{"message": _("payroll.validation.payroll.bill_already_assigned") % {
            "bill_ids": payroll_bill_ids,
        }}]
    return []

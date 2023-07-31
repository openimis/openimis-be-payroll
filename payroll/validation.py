from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from core.validation import BaseModelValidation
from payroll.models import PaymentPoint, Payroll, PayrollBill


class PaymentPointValidation(BaseModelValidation):
    OBJECT_TYPE = PaymentPoint

    @classmethod
    def validate_create(cls, user, **data):
        super().validate_create(user, **data)

    @classmethod
    def validate_update(cls, user, **data):
        super().validate_update(user, **data)

    @classmethod
    def validate_delete(cls, user, **data):
        super().validate_delete(user, **data)


class PayrollValidation(BaseModelValidation):
    OBJECT_TYPE = Payroll

    @classmethod
    def validate_create(cls, user, **data):
        errors = validate_payroll(data)
        if errors:
            raise ValidationError(errors)
        super().validate_create(user, **data)


def validate_payroll(data):
    # return [
    #     *are_bills_in_data(data),
    #     *validate_one_payroll_per_bill(data)
    # ]
    return []


def are_bills_in_data(data):
    bills = data.get('bills', None)
    if not bills:
        return [{"message": _("payroll.validation.payroll.no_bills_in_date_range")}]
    return []


def validate_one_payroll_per_bill(data):
    bills = data.get('bills', [])
    query = PayrollBill.objects.filters(bill__in=bills)
    if query.exists():
        payroll_bill_ids = list(query.values_list('id', flat=True))
        return [{"message": _("payroll.validation.payroll.bill_already_assigned") % {
            "bill_ids": payroll_bill_ids,
        }}]
    return []

from core.validation import BaseModelValidation
from payroll.models import PaymentPoint


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

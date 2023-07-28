import logging

from core.services import BaseService
from payroll.models import Payroll
from payroll.validation import PayrollValidation

logger = logging.getLogger(__name__)


class PayrollService(BaseService):
    OBJECT_TYPE = Payroll

    def __init__(self, user, validation_class=PayrollValidation):
        super().__init__(user, validation_class)

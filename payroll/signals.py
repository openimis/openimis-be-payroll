import logging

from core.models import User
from core.service_signals import ServiceSignalBindType
from core.signals import bind_service_signal
from openIMIS.openimisapps import openimis_apps
from tasks_management.models import Task
from payroll.apps import PayrollConfig
from payroll.payments_registry import PaymentMethodStorage


logger = logging.getLogger(__name__)
imis_modules = openimis_apps()


def bind_service_signals():

    def on_task_complete_accept_payroll(**kwargs):
        def accept_payroll(payroll, user):
            strategy = PaymentMethodStorage.get_chosen_payment_method(payroll.payment_method)
            if strategy:
                strategy.accept_payroll(payroll, user)
        try:
            result = kwargs.get('result', None)
            task = result['data']['task']
            user = User.objects.get(id=result['data']['user']['id'])
            if result \
                    and result['success'] \
                    and task['business_event'] == PayrollConfig.payroll_business_event:
                task_status = task['status']
                if task_status == Task.Status.COMPLETED:
                    payroll = task['entity']
                    accept_payroll(payroll, user)
        except Exception as e:
            logger.error("Error while executing on_task_complete_accept_payroll", exc_info=e)

    bind_service_signal(
        'payroll_service.create_task',
        on_task_complete_accept_payroll,
        bind_type=ServiceSignalBindType.AFTER
    )
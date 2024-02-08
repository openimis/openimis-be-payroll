import logging
from io import BytesIO

import pandas as pd

from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework import views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from im_export.views import check_user_rights
from invoice.models import Bill
from payroll.apps import PayrollConfig
from payroll.models import Payroll, BenefitConsumption, BenefitConsumptionStatus, PayrollStatus
from payroll.payments_registry import PaymentMethodStorage
from payroll.services import CsvReconciliationService

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([check_user_rights(PayrollConfig.gql_payroll_create_perms, )])
def send_callback_to_openimis(request):
    try:
        user = request.user
        payroll_id, response_from_gateway, rejected_bills = \
            _resolve_send_callback_to_imis_args(request)
        payroll = Payroll.objects.get(id=payroll_id)
        strategy = PaymentMethodStorage.get_chosen_payment_method(payroll.payment_method)
        if strategy:
            # save the reponse from gateway in openIMIS
            strategy.acknowledge_of_reponse_view(
                payroll,
                response_from_gateway,
                user,
                rejected_bills
            )
        return Response({'success': True, 'error': None}, status=201)
    except ValueError as exc:
        logger.error("Error while sending callback to openIMIS", exc_info=exc)
        return Response({'success': False, 'error': str(exc)}, status=400)
    except Exception as exc:
        logger.error("Unexpected error while sending callback to openIMIS", exc_info=exc)
        return Response({'success': False, 'error': str(exc)}, status=500)


def _resolve_send_callback_to_imis_args(request):
    payroll_id = request.data.get('payroll_id')
    response_from_gateway = request.data.get('response_from_gateway')
    rejected_bills = request.data.get('rejected_bills')
    if not payroll_id:
        raise ValueError('Payroll Id not provided')
    if not response_from_gateway:
        raise ValueError('Response from gateway not provided')
    if rejected_bills is None:
        raise ValueError('Rejected Bills not provided')

    return payroll_id, response_from_gateway, rejected_bills


class CSVReconciliationAPIView(views.APIView):
    def get(self, request):
        try:
            payroll_id = request.GET.get('payroll_id')
            service = CsvReconciliationService(request.user)
            in_memory_file = service.download_reconciliation(payroll_id)
            response = Response(headers={'Content-Disposition': f'attachment; filename="reconciliation.csv"'},
                                content_type='text/csv')
            response.content = in_memory_file.getvalue()
            return response
        except ValueError as exc:
            logger.error("Error while generating CSV reconciliation", exc_info=exc)
            return Response({'success': False, 'error': str(exc)}, status=400)
        except Exception as exc:
            logger.error("Unexpected error while generating CSV reconciliation", exc_info=exc)
            return Response({'success': False, 'error': str(exc)}, status=500)

    def post(self, request):
        try:
            payroll_id = request.GET.get('payroll_id')
            file = request.FILES.get('file')
            target_file_path = f"csv_reconciliation/payroll_{payroll_id}/{file.name}"
            service = CsvReconciliationService(request.user)
            if default_storage.exists(target_file_path):
                raise ValueError("csv_reconciliation.validation.file_already_exists")
            service.upload_reconciliation(payroll_id, file)
            default_storage.save(target_file_path, file)
            return Response({'success': True, 'error': None}, status=201)
        except ValueError as exc:
            logger.error("Error while uploading CSV reconciliation", exc_info=exc)
            return Response({'success': False, 'error': str(exc)}, status=400)
        except Exception as exc:
            logger.error("Unexpected error while uploading CSV reconciliation", exc_info=exc)
            return Response({'success': False, 'error': str(exc)}, status=500)

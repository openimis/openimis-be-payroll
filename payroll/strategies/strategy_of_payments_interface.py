import abc


class StrategyOfPaymentInterface(object,  metaclass=abc.ABCMeta):

    @classmethod
    def accept_payroll(cls, payroll, user, **kwargs):
        pass

    @classmethod
    def reject_payroll(cls, payroll, user, **kwargs):
        from payroll.models import PayrollStatus
        cls.change_status_of_payroll(payroll, PayrollStatus.REJECTED, user)
        cls.remove_benefits_from_rejected_payroll(payroll)

    @classmethod
    def reject_approved_payroll(cls, payroll, user):
        from core.services.utils.serviceUtils import model_representation
        from payroll.models import (
            BenefitConsumption,
            BenefitConsumptionStatus,
            PayrollStatus
        )
        from invoice.models import (
            DetailPaymentInvoice,
            PaymentInvoice
        )
        from payroll.services import PayrollService

        benefit_data = BenefitConsumption.objects.filter(
            payrollbenefitconsumption__payroll=payroll,
            status=BenefitConsumptionStatus.RECONCILED,
            is_deleted=False
        )
        related_bills = benefit_data.values_list('id', 'benefitattachment__bill')

        for benefit in benefit_data:
            benefit.receipt = None
            benefit.status = BenefitConsumptionStatus.ACCEPTED
            benefit.save(username=user.username)
        cls.change_status_of_payroll(payroll, PayrollStatus.PENDING_APPROVAL, user)
        PayrollService(user).create_accept_payroll_task(payroll.id, model_representation(payroll))

    @classmethod
    def acknowledge_of_reponse_view(cls, payroll, response_from_gateway, user, rejected_bills):
        pass

    @classmethod
    def reconcile_payroll(cls, payroll, user):
        pass

    @classmethod
    def change_status_of_payroll(cls, payroll, status, user):
        payroll.status = status
        payroll.save(username=user.login_name)

    @classmethod
    def remove_benefits_from_rejected_payroll(cls, payroll):
        from payroll.models import (
            BenefitAttachment,
            BenefitConsumption,
            PayrollBenefitConsumption
        )
        from invoice.models import (
            Bill,
            BillItem
        )

        benefit_data = BenefitConsumption.objects.filter(
            payrollbenefitconsumption__payroll=payroll,
            is_deleted=False
        ).values_list('id', 'benefitattachment__bill')

        benefits, related_bills = zip(*benefit_data)

        BenefitAttachment.objects.filter(
            benefit_id__in=benefits
        ).delete()

        BillItem.objects.filter(
            bill__id__in=related_bills
        ).delete()

        Bill.objects.filter(
            id__in=related_bills
        ).delete()

        PayrollBenefitConsumption.objects.filter(payroll=payroll).delete()

        BenefitConsumption.objects.filter(
            id__in=benefits,
            is_deleted=False
        ).delete()

import abc


class StrategyOfPaymentInterface(object,  metaclass=abc.ABCMeta):

    @classmethod
    def accept_payroll(cls, payroll, user, **kwargs):
        pass

    @classmethod
    def reject_payroll(cls, payroll, user, **kwargs):
        from payroll.models import PayrollStatus
        cls.change_status_of_payroll(payroll, PayrollStatus.REJECTED, user)
        cls._remove_benefits_from_rejected_payroll(payroll)

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
    def _remove_benefits_from_rejected_payroll(cls, payroll):
        from payroll.models import BenefitAttachment, BenefitConsumption
        from invoice.models import Bill, BillItem
        benefits = BenefitConsumption.objects.filter(
            payrollbenefitconsumption__payroll__id=payroll.id,
            is_deleted=False
        )
        # remove from db all related fields to payroll, no business need to keep them in db
        BillItem.objects.filter(bill__benefitattachment__benefit_id__in=benefits)
        Bill.objects.filter(benefitattachment__benefit_id__in=benefits)
        BenefitAttachment.objects.filter(benefit_id__in=benefits).delete()
        benefits.delete()

from django.apps import apps

# Check if the 'opensearch_reports' app is in INSTALLED_APPS
if 'opensearch_reports' in apps.app_configs:
    from django_opensearch_dsl import Document, fields as opensearch_fields
    from django_opensearch_dsl.registries import registry
    from payroll.models import (
        Payroll,
        PayrollBenefitConsumption,
        BenefitConsumption,
        BenefitAttachment
    )
    from payment_cycle.models import PaymentCycle
    from contribution_plan.models import PaymentPlan
    from individual.models import Individual
    from invoice.models import Bill

    @registry.register_document
    class PayrollDocument(Document):
        name = opensearch_fields.KeywordField()
        status = opensearch_fields.KeywordField()
        payment_method = opensearch_fields.KeywordField()
        date_created = opensearch_fields.DateField()
        payment_plan = opensearch_fields.ObjectField(properties={
            'code': opensearch_fields.KeywordField(),
            'name': opensearch_fields.KeywordField(),
        })
        payment_cycle = opensearch_fields.ObjectField(properties={
            'code': opensearch_fields.KeywordField(),
            'status': opensearch_fields.KeywordField(),
            'start_date': opensearch_fields.DateField(),
            'end_date': opensearch_fields.DateField(),
        })

        class Index:
            name = 'payroll'
            settings = {
                'number_of_shards': 1,
                'number_of_replicas': 0
            }
            auto_refresh = True

        class Django:
            model = Payroll
            fields = [
                'id'
            ]
            related_models = [PaymentPlan, PaymentCycle]
            queryset_pagination = 5000

        def get_instances_from_related(self, related_instance):
            if isinstance(related_instance, PaymentPlan):
                return related_instance.payroll_set.all()
            elif isinstance(related_instance, PaymentCycle):
                return related_instance.payroll_set.all()


    @registry.register_document
    class BenefitConsumptionDocument(Document):
        photo = opensearch_fields.KeywordField()
        code = opensearch_fields.KeywordField()
        date_due = opensearch_fields.DateField()
        date_created = opensearch_fields.DateField()
        receipt = opensearch_fields.KeywordField()
        amount = opensearch_fields.KeywordField()
        type = opensearch_fields.KeywordField()
        status = opensearch_fields.KeywordField()
        json_ext = opensearch_fields.ObjectField()
        individual = opensearch_fields.ObjectField(properties={
            'first_name': opensearch_fields.KeywordField(),
            'last_name': opensearch_fields.KeywordField(),
            'dob': opensearch_fields.DateField(),
        })

        class Index:
            name = 'benefit_consumption'
            settings = {
                'number_of_shards': 1,
                'number_of_replicas': 0
            }
            auto_refresh = True

        class Django:
            model = BenefitConsumption
            related_models = [Individual]
            fields = [
                'id'
            ]
            queryset_pagination = 5000

        def get_instances_from_related(self, related_instance):
            if isinstance(related_instance, Individual):
                return related_instance.benefit_consumption_set.all()


    @registry.register_document
    class PayrollBenefitConsumptionDocument(Document):
        payroll = opensearch_fields.ObjectField(properties={
            'name': opensearch_fields.KeywordField(),
            'status': opensearch_fields.KeywordField(),
            'payment_method': opensearch_fields.KeywordField(),
            'date_created': opensearch_fields.DateField(),
            'payment_plan': opensearch_fields.ObjectField(properties={
                'code': opensearch_fields.KeywordField(),
                'name': opensearch_fields.KeywordField(),
            }),
            'payment_cycle': opensearch_fields.ObjectField(properties={
                'code': opensearch_fields.KeywordField(),
                'status': opensearch_fields.KeywordField(),
                'start_date': opensearch_fields.DateField(),
                'end_date': opensearch_fields.DateField(),
            })
        })
        benefit = opensearch_fields.ObjectField(properties={
            'code': opensearch_fields.KeywordField(),
            'status': opensearch_fields.KeywordField(),
            'type': opensearch_fields.KeywordField(),
            'receipt': opensearch_fields.KeywordField(),
            'amount': opensearch_fields.KeywordField(),
            'photo': opensearch_fields.KeywordField(),
            'date_due': opensearch_fields.DateField(),
            'individual': opensearch_fields.ObjectField(properties={
              'first_name': opensearch_fields.KeywordField(),
              'last_name': opensearch_fields.KeywordField(),
              'dob': opensearch_fields.DateField(),
            })
        })

        class Index:
            name = 'payroll_benefit_consumption'
            settings = {
                'number_of_shards': 1,
                'number_of_replicas': 0
            }
            auto_refresh = True

        class Django:
            model = PayrollBenefitConsumption
            related_models = [Payroll, BenefitConsumption]
            fields = [
                'id'
            ]
            queryset_pagination = 5000

        def get_instances_from_related(self, related_instance):
            if isinstance(related_instance, Payroll):
                return PayrollBenefitConsumption.objects.filter(payroll=related_instance)
            elif isinstance(related_instance, BenefitConsumption):
                return PayrollBenefitConsumption.objects.filter(benefit=related_instance)


    @registry.register_document
    class BenefitAttachmentDocument(Document):
        bill = opensearch_fields.ObjectField(properties={
            'code': opensearch_fields.KeywordField(),
            'code_ext': opensearch_fields.KeywordField(),
            'code_tp': opensearch_fields.KeywordField(),
            'status': opensearch_fields.KeywordField(),
            'currency_code': opensearch_fields.KeywordField(),
            'note': opensearch_fields.KeywordField(),
            'terms': opensearch_fields.KeywordField(),
            'date_created': opensearch_fields.DateField(),
            'date_due': opensearch_fields.DateField(),
            'date_payed': opensearch_fields.DateField(),
            'amount_total': opensearch_fields.KeywordField(),
        })
        benefit = opensearch_fields.ObjectField(properties={
            'code': opensearch_fields.KeywordField(),
            'status': opensearch_fields.KeywordField(),
            'type': opensearch_fields.KeywordField(),
            'receipt': opensearch_fields.KeywordField(),
            'amount': opensearch_fields.KeywordField(),
            'photo': opensearch_fields.KeywordField(),
            'date_due': opensearch_fields.DateField(),
            'individual': opensearch_fields.ObjectField(properties={
                'first_name': opensearch_fields.KeywordField(),
                'last_name': opensearch_fields.KeywordField(),
                'dob': opensearch_fields.DateField(),
            })
        })
        payroll = opensearch_fields.NestedField(properties={
            'name': opensearch_fields.KeywordField(),
            'status': opensearch_fields.KeywordField(),
            'payment_method': opensearch_fields.KeywordField(),
            'date_created': opensearch_fields.DateField(),
            'payment_plan': opensearch_fields.ObjectField(properties={
                'code': opensearch_fields.KeywordField(),
                'name': opensearch_fields.KeywordField(),
            }),
            'payment_cycle': opensearch_fields.ObjectField(properties={
                'code': opensearch_fields.KeywordField(),
                'status': opensearch_fields.KeywordField(),
                'start_date': opensearch_fields.DateField(),
                'end_date': opensearch_fields.DateField(),
            })
        })

        class Index:
            name = 'benefit_attachment'
            settings = {
                'number_of_shards': 1,
                'number_of_replicas': 0
            }
            auto_refresh = True

        class Django:
            model = BenefitAttachment
            related_models = [Payroll, Bill, BenefitConsumption]
            fields = [
                'id'
            ]
            queryset_pagination = 5000

        def get_instances_from_related(self, related_instance):
            if isinstance(related_instance, Payroll):
                return BenefitAttachment.objects.filter(
                    benefit__payrollbenefitconsumption__payroll=related_instance
                )
            elif isinstance(related_instance, Bill):
                return BenefitAttachment.objects.filter(bill=related_instance)
            elif isinstance(related_instance, BenefitConsumption):
                return BenefitAttachment.objects.filter(benefit=related_instance)

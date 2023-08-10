class StrategyOfPaymentInterface:

    @classmethod
    def accept_payroll(cls, **kwargs):
        pass

    @classmethod
    def send_data_to_adaptor(cls, **kwargs):
        pass

    def process_callback_from_adaptor(self):
        pass

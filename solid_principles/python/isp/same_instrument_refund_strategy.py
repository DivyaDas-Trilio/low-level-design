from solid_principles.python.isp.refund_compatible_creditcard import IRefundCompatibleCreditCard

class SameInstrumentRefundStrategy(IRefundCompatibleCreditCard):

    def process_refund(self, amount):
        print(f"Processing refund of {amount} using the same instrument")

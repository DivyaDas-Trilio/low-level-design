from solid_principles.python.isp.refund_compatible_creditcard import IRefundCompatibleCreditCard

class WalletRefundStrategy(IRefundCompatibleCreditCard):

    def process_refund(self, amount):
        print(f"Processing refund of {amount} to the wallet")
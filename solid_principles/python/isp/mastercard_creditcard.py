from sentry_sdk.client import I
class MastercardCreditCard(ICreditCard, IRefundCompatibleCreditCard):
    
    def __init__(self, *args, **kwargs):
        self.refund_strategy = SameInstrumentRefundStrategy()
    
    def swipe_and_pay(self, amount):
        print(f"Swiping Mastercard card for {amount}")

    def insert_and_pay(self, amount):
        print(f"Inserting Mastercard card for {amount}")

    def tap_and_pay(self, amount):
        print(f"Tapping Mastercard card for {amount}")

    def process_refund(self, amount):
        self.refund_strategy.process_refund(amount)

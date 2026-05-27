from sentry_sdk.client import I
class RupayCreditCard(ICreditCard, IUPICompatibleCreditCard, IRefundCompatibleCreditCard):
    def swipe_and_pay(self, amount):
        print(f"Swiping Rupay card for {amount}")

    def insert_and_pay(self, amount):
        print(f"Inserting Rupay card for {amount}")

    def tap_and_pay(self, amount):
        print(f"Tapping Rupay card for {amount}")

    def pay_via_upi(self, amount):
        print(f"Paying {amount} via UPI using Rupay card")
        
    def process_refund(self, amount):
        print(f"Processing refund of {amount} for Rupay card")

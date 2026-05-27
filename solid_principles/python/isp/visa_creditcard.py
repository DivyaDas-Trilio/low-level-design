from solid_principles.python.isp.credit_card import ICreditCard
from solid_principles.python.isp.refund_compatible_creditcard import IRefundCompatibleCreditCard
from solid_principles.python.isp.wallet_refund_strategy import WalletRefundStrategy

class VisaCreditCard(ICreditCard, IRefundCompatibleCreditCard):
    def __init__(self, refund_strategy=None):
        self.refund_strategy = refund_strategy
    def swipe_and_pay(self, amount):
        print(f"Swiping Visa card for {amount}")
    
    def insert_and_pay(self, amount):
        print(f"Inserting Visa card for {amount}")
    
    def tap_and_pay(self, amount):
        print(f"Tapping Visa card for {amount}")

    def process_refund(self, amount):
        self.refund_strategy.process_refund(amount)

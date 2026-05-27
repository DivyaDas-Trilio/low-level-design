class AmexCreditCard(ICreditCard, IRefundCompatibleCreditCard):
    def swipe_and_pay(self, amount):
        print(f"Swiping Amex card for {amount}")

    def insert_and_pay(self, amount):
        print(f"Inserting Amex card for {amount}")

    def tap_and_pay(self, amount):
        print(f"Tapping Amex card for {amount}")

    def process_refund(self, amount):
        print(f"Processing refund of {amount} for Amex card")
    
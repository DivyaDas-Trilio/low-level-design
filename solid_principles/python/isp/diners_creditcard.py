from solid_principles.python.isp.credit_card   import ICreditCard

class DinersCreditCard(ICreditCard):
    def swipe_and_pay(self, amount):
        print(f"Swiping Diners card for {amount}")

    def insert_and_pay(self, amount):
        print(f"Inserting Diners card for {amount}")

    def tap_and_pay(self, amount):
        print(f"Tapping Diners card for {amount}")
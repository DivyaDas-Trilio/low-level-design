from solid_principles.python.isp.diners_creditcard import DinersCreditCard
from solid_principles.python.isp.visa_creditcard import VisaCreditCard
from solid_principles.python.isp.wallet_refund_strategy import WalletRefundStrategy
from solid_principles.python.isp.same_instrument_refund_strategy import SameInstrumentRefundStrategy

if __name__ == "__main__":
    # driver code
    cc1 = DinersCreditCard()
    cc1.swipe_and_pay(100)
    
    cc2 = VisaCreditCard(WalletRefundStrategy())
    cc2.tap_and_pay(200)
    cc2.process_refund(50)

    cc3 = VisaCreditCard(SameInstrumentRefundStrategy())
    cc3.tap_and_pay(300)
    cc3.process_refund(100)
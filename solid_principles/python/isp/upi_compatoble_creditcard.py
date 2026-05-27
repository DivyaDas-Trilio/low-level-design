from abc import ABC, abstractmethod

class IUPICompatibleCreditCard(ABC):

    @abstractmethod
    def pay_via_upi(self, amount):
        pass

from abc import ABC, abstractmethod

class IRefundCompatibleCreditCard(ABC):

    @abstractmethod
    def process_refund(self, amount):
        pass
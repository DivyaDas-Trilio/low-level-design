from abc import ABC, abstractmethod

class ICreditCard(ABC):
    @abstractmethod
    def swipe_and_pay(self, amount):
        pass
    
    @abstractmethod
    def insert_and_pay(self, amount):
        pass
    
    @abstractmethod
    def tap_and_pay(self, amount):
        pass
    
    
from abc import ABC, ABCMeta, abstractmethod

class Notification(ABC):
    
    @abstractmethod
    def send_message(self):
        pass
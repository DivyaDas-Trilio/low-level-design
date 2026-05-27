from abc import ABC, abstractmethod
class Prototype(ABC):
    
    @abstractmethod
    def clone(self):
        pass

class Email(Prototype):
    def __init__(self, subject=None, body=None, sender=None, recipient=None, **kwargs):
        self._subject = subject
        self._body = body
        self._sender = sender
        self._recipient = recipient
        self._copy = kwargs.get("copy", None)
        if self._copy:
            self._subject = self._copy.subject
            self._body = self._copy.body
            self._sender = self._copy.sender
            self._recipient = self._copy.recipient

    def __str__(self):
        return f"Email from {self._sender} to {self._recipient}: {self._subject}"
    
    @property
    def subject(self):
        return self._subject
    
    @subject.setter
    def subject(self, subject):
        import pdb; pdb.set_trace()
        self._subject = subject
    
    @property
    def body(self):
        return self._body
    
    @body.setter
    def body(self, body):
        self._body = body
    
    @property
    def sender(self):
        return self._sender
    
    @sender.setter
    def sender(self, sender):
        self._sender = sender
    
    @property
    def recipient(self):
        return self._recipient
    
    @recipient.setter
    def recipient(self, recipient):
        self._recipient = recipient
        
    def clone(self):
        return Email(copy=self)
    
class PremiumEmail(Email, Prototype):
    def __init__(self, subject=None, body=None, sender=None, recipient=None, **kwargs):
        super().__init__(subject, body, sender, recipient, **kwargs)
        self._priority = kwargs.get("priority", "High")
        self._copy = kwargs.get("copy", None)
    
    @property
    def priority(self):
        return self._priority
    
    @priority.setter
    def priority(self, priority):
        self._priority = priority   
        
    def clone(self):
        return PremiumEmail(copy=self)
    
    def __str__(self):
        return f"PremiumEmail from {self._sender} to {self._recipient}: {self._subject} with priority {self._priority}"

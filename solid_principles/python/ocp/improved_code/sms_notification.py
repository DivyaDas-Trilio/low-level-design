from lld.solid_principles.python.ocp.improved_code.notification import Notification

class SMSNotification(Notification):
    def __init__(self):
        pass
    
    def send_message(self):
        print("sending SMS Notification...")
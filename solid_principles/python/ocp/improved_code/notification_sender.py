from lld.solid_principles.python.ocp.improved_code.email_notification import EmailNotification 
#from lld.solid_principles.python.ocp.better_code.push_notification import PushNotification
from lld.solid_principles.python.ocp.improved_code.push_notification import PushNotification
from lld.solid_principles.python.ocp.improved_code.sms_notification import SMSNotification


class NotificationSender:
    
    def __init__(self, notifications):
        self.notifications = notifications
        
    
    def send_notification(self, notifications=None):
        # for notification in notifications:
        #     if notification == 'SMS':
        #         SMSNotification().send_message("Hello SMS.")
        #     if notification == "EMAIL":
        #         EmailNotification().send_message("Hello Email.") 
        #     if notification == "PUSH":
        #         PushNotification().send_message("Hello Push.")
        
        for notification in self.notifications:
            notification.send_message()
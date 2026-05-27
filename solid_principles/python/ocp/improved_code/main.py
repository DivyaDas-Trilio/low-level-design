from lld.solid_principles.python.ocp.improved_code.email_notification import EmailNotification 
#from lld.solid_principles.python.ocp.improved_code.push_notification import PushNotification
from lld.solid_principles.python.ocp.improved_code.sms_notification import SMSNotification
from lld.solid_principles.python.ocp.improved_code.notification_sender import NotificationSender

if __name__ == "__main__":
    # message = ["SMS", "EMAIL"]
    NotificationSender([
        SMSNotification(),
        EmailNotification()]).send_notification()
    
    
    # for each in message:
    #     if each == 'SMS':
    #         SMSNotification().send_message("Hello SMS.")
    #     if each == "EMAIL":
    #         EmailNotification().send_message("Hello Email.") 
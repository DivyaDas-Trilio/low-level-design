from lld.solid_principles.python.ocp.better_code.email_notification import EmailNotification 
#from lld.solid_principles.python.ocp.better_code.push_notification import PushNotification
from lld.solid_principles.python.ocp.better_code.sms_notification import SMSNotification

if __name__ == "__main__":
    message = ["SMS", "EMAIL"]
    
    for each in message:
        if each == 'SMS':
            SMSNotification().send_message("Hello SMS.")
        if each == "EMAIL":
            EmailNotification().send_message("Hello Email.") 
from lld.solid_principles.python.ocp.improved_code.notification import Notification

class EmailNotification(Notification):
    def __init__(self):
        pass
    
    def send_message(self):
        # logic to send email notification
        print(f"Email Notification:")
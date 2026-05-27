class Notification:
    def __init__(self, message):
        self.message = message

    def send_email_notification(self):
        # logic to send email notification
        print(f"Email Notification: {self.message}")

    def send_sms_notification(self):
        # logic to send SMS notification
        print(f"SMS Notification: {self.message}")

    def send_push_notification(self):
        # logic to send push notification
        print(f"Push Notification: {self.message}")
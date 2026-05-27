from lld.solid_principles.python.ocp.improved_code.notification import Notification

class PushNotification(Notification):
    def __init__(self):
        pass

    def send_message(self, message):
        # logic to send push notification
        print(f"Push Notification: {message}")

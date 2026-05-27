from lld.solid_principles.python.ocp.notification import Notification

if __name__ == "__main__":
    message = "Your order has been shipped!"
    notification_type = "email"  # This can be "email", "sms", or "push"

    notification = Notification(message)

    if notification_type == "email":
        notification.send_email_notification()
    elif notification_type == "sms":
        notification.send_sms_notification()
    elif notification_type == "push":
        notification.send_push_notification()
    else:
        print("Invalid notification type.") 
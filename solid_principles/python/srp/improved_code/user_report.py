class UserReport:
    def __init__(self, user_db):
        self.user_db = user_db

    def generate_report(self, username):
        user = self.user_db.get_user(username)
        if user:
            return f"User Report for {username}: Email: {user.email}, Last Login: {user.last_login}"
        return "User not found"
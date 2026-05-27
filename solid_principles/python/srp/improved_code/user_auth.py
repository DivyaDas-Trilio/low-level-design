class UserAuth:
    def __init__(self, user_db):
        self.user_db = user_db

    def authenticate(self, username, password):
        user = self.user_db.get_user(username)
        if user and user.password == password:
            return True
        return False
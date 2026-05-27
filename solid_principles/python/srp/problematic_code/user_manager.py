class UserManager:
    def __init__(self):
        self.users = []

    def add_user(self, user):
        self.users.append(user)

    def remove_user(self, user):
        self.users.remove(user)

    def get_user(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def authenticate_user(self, username, password):
        user = self.get_user(username)
        if user and user.password == password:
            return True
        return False
    
    def save_user(self, user):
        # logic to save user data to a database or file
        print("User data saved.")
    
    def generate_report(self):
        # logic to generate a report of users
        print("User report generated.")
class Users:
    def __init__(self, name, email, id):
        self._users = []
        self._id = id
        self._name = name
        self._email = email
        
        
    # getters and setters for id, name, email
    @property
    def id(self):
        return self._id  

    @property
    def name(self):
        return self._name

    @property
    def email(self):
        return self._email

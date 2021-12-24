from User import User

class Admin(User):
    def __init__(self, username, email, password):
        super().__init__(username, email, password, "Admin", "Active")

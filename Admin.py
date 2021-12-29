from User import User

class Admin(User):
    def __init__(self, userID, username, email, password):
        super().__init__(userID, username, email, password, "Admin", "Active")

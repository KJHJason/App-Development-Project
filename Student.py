from Common import Common

class Student(Common):
    def __init__(self, user_id, username, email, password):
        super().__init__(user_id, username, email, password, "Student", "Good")
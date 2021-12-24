from User import User

class Student(User):
    def __init__(self, username, email, password):
        super().__init__(username, email, password, "Teacher", "Good")
        self.__earnings = 0
        
    def self_earnings(self, earnings):
        self.__earnings = earnings

    def get_earnings(self):
        return self.__earnings
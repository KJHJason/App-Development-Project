from User import User

class Teacher(User):
    def __init__(self, purchaseID, reviewID, viewed, joinDate):
        super().__init__(purchaseID, reviewID, viewed)
        self.__earnings = 0
        self.__joinDate = joinDate 

    def self_earnings(self, earnings):
        self.__earnings = earnings
    def self_joinDate(self, joinDate):
        self.__joinDate = joinDate

    def get_earnings(self):
        return self.__earnings
    def get_joinDate(self):
        return self.__joinDate

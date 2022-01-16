from StudentAndTeacher import StudentAndTeacher

class Student(StudentAndTeacher):
    def __init__(self, user_id, username, email, password):
        super().__init__(user_id, username, email, password, "Student", "Good")
        self.__purchaseIDs = []
        self.__reviewIDs = []

    def add_purchaseID(self, purchaseID):
        self.__purchaseIDs.append(purchaseID)
    def add_reviewID(self, reviewID):
        self.__reviewIDs.append(reviewID)
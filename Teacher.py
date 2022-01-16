from StudentAndTeacher import StudentAndTeacher
from Course import Course

class Teacher(StudentAndTeacher):
    def __init__(self, userID, username, email, password):
        super().__init__(userID, username, email, password, "Teacher", "Good")
        self.__earnings = 0
        self.__purchaseIDs = []
        self.__reviewIDs = []
        self.__viewed = ""
        self.__joinDate = ""

        self.__bio = ""

    # Added by Wei Ren for courses
        self.__coursesTeaching = [] # Course IDs here

    def add_purchaseID(self, purchaseID):
        self.__purchaseIDs.append(purchaseID)
    def add_reviewID(self, reviewID):
        self.__reviewIDs.append(reviewID)

    def set_joinDate(self, joinDate):
        self.__joinDate = joinDate
    def set_earnings(self, earnings):
        self.__earnings = earnings
    def set_bio(self, bio):
        self.__bio = bio
    
    def get_joinDate(self):
        return self.__joinDate
    def get_earnings(self):
        return self.__earnings
    def get_bio(self):
        return self.__bio

# Added by Wei Ren for courses
    def get_coursesTeaching(self):
        return self.__coursesTeaching
    def set_courseTeaching(self, courseID):
        self.__coursesTeaching.append(courseID)




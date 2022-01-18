from StudentAndTeacher import StudentAndTeacher
from Course import Course

class Teacher(StudentAndTeacher):
    def __init__(self, user_id, username, email, password):
        super().__init__(user_id, username, email, password, "Teacher", "Good")
        self.__earnings = 0
        self.__accumulated_earnings = 0
        self.__paypalID = ""    # PayPal Account ID
        self.__purchaseIDs = []
        self.__reviewIDs = []
        self.__bio = ""
    # Added by Wei Ren for courses
        self.__coursesTeaching = [] # Course IDs here

    def add_purchaseID(self, purchaseID):
        self.__purchaseIDs.append(purchaseID)
    def add_reviewID(self, reviewID):
        self.__reviewIDs.append(reviewID)

    def remove_purchaseID(self, purchaseID):
        if purchaseID in self.__purchaseIDs:
            self.__purchaseID.remove(purchaseID)
        else:
            return False
    def remove_reviewID(self, reviewID):
        if reviewID in self.__reviewIDs:
            self.__reviewIDs.remove(reviewID)
        else:
            return False

    def set_viewed(self, viewed):
        self.__viewed = viewed
    def set_earnings(self, earnings):
        self.__earnings = earnings
    def set_accumulated_earnings(self, earnings):
        self.__accumulated_earnings = earnings
    def set_bio(self, bio):
        self.__bio = bio
    
    def get_earnings(self):
        return self.__earnings
    def get_bio(self):
        return self.__bio
    def get_accumulated_earnings(self):
        return self.__accumulated_earnings

# Added by Wei Ren for courses
    def get_coursesTeaching(self):
        return self.__coursesTeaching
    def set_courseTeaching(self, courseID):
        self.__coursesTeaching.append(courseID)

    def set_paypalID(self, paypalID):
        self.__paypalID = paypalID
    def get_paypalID(self):
        return self.__paypalID

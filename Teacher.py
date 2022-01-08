from StudentAndTeacher import StudentAndTeacher
from Course import Course

class Teacher(StudentAndTeacher):
    def __init__(self, userID, username, email, password):
        super().__init__(userID, username, email, password, "Teacher", "Good")
        self.__earnings = 0
        self.__purchaseID = ""
        self.__reviewID = ""
        self.__viewed = ""
        self.__joinDate = ""
    # Added by Wei Ren for courses
        self.__coursesTeaching = [] # Course IDs here
        self.__shoppingCart = [] # Course IDs here
        self.__bio = ""
    
    def set_purchaseID(self, purchaseID):
        self.__purchaseID = purchaseID
    def set_reviewID(self, reviewID):
        self.__reviewID = reviewID
    def set_viewed(self, viewed):
        self.__viewed = viewed
    def set_joinDate(self, joinDate):
        self.__joinDate = joinDate
    def set_earnings(self, earnings):
        self.__earnings = earnings
    def set_bio(self, bio):
        self.__bio = bio
    
    def get_purchaseID(self):
        return self.__purchaseID
    def get_reviewID(self):
        return self.__reviewID
    def get_viewed(self):
        return self.__viewed
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

    #e.g. add_to_cart(0,"Zoom")
    def add_to_cart(self, courseID,type):
        self.__shoppingCart.append([str(courseID),type])
    def remove_from_cart(self,courseID,type):
        self.__shoppingCart.remove([str(courseID),type])

    def get_cartCourseType(self, courseID):
        for course in self.__shoppingCart:
            if course[0] == courseID:
                return course[1]

    def get_shoppingCart(self):
        return self.__shoppingCart

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
    # Added by Wei Ren for courses
        self.__coursesTeaching = [] # Course IDs here
        self.__shoppingCart = [] # Course IDs here
        self.__bio = ""
        self.__shoppingCart = [] # Course IDs & Type here
        self.__purchasedCourses = [] # Course IDs & Type here
    
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

    #e.g. add_to_cart(0,"Zoom")
    def add_to_cart(self, courseID,type):
        self.__shoppingCart.append([str(courseID),type])
    def remove_from_cart(self,courseID,type):
        self.__shoppingCart.remove([str(courseID),type])

    def get_cartCourseType(self, courseID):
        for course in self.__shoppingCart:
            if course[0] == courseID and course[1] == "Video":
                video = True
            elif course[0] == courseID and course[1] == "Zoom":
                zoom = True
        if video and zoom:
            return "Both"
        elif video:
            return "Video"
        elif zoom:
            return "Zoom"

    def get_purchasesCourseType(self,courseID):
        for course in self.__purchasedCourses:
            if course[0] == courseID and course[1] == "Video":
                video = True
            elif course[0] == courseID and course[1] == "Zoom":
                zoom = True
            if video and zoom:
                return "Both"
            elif video:
                return "Video"
            elif zoom:
                return "Zoom"
            else:
                return None

    def get_shoppingCart(self):
        return self.__shoppingCart

    def get_purchases(self):
        return self.__purchases

    def addCartToPurchases(self):
        for course in self.__shoppingCart:
            self.__purchasedCourses.append(course)
        self.__shoppingCart = []

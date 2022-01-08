from StudentAndTeacher import StudentAndTeacher

class Student(StudentAndTeacher):
    def __init__(self, userID, username, email, password):
        super().__init__(userID, username, email, password, "Student", "Good")
        self.__purchaseID = ""
        self.__reviewID = ""
        self.__viewed = ""
    # Added by Wei Ren for Courses
        self.__shoppingCart = []
        
    def set_purchaseID(self, purchaseID):
        self.__purchaseID = purchaseID
    def set_reviewID(self, reviewID):
        self.__reviewID = reviewID
    def set_viewed(self, viewed):
        self.__viewed = viewed

    def get_purchaseID(self):
        return self.__purchaseID
    def get_reviewID(self):
        return self.__reviewID
    def get_viewed(self):
        return self.__viewed

    # Added by Wei Ren for Courses
    #e.g. add_to_cart(0,"Zoom")
    def add_to_cart(self, courseID,type):
        self.__shoppingCart.append([str(courseID),type])        # [[courseID, courseType], [courseID, courseType], ...]
    def remove_from_cart(self,courseID,type):
        self.__shoppingCart.remove([str(courseID),type])

    def get_cartCourseType(self, courseID):
        for course in self.__shoppingCart:
            if course[0] == courseID:
                return course[1]

    def get_shoppingCart(self):
        return self.__shoppingCart

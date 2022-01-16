from User import User
from ViewsAndRecommendations import ViewsAndRecommendations

class StudentAndTeacher(User):
    def __init__(self, user_id, username, email, password, acc_type, status):
        super().__init__(user_id, username, email, password, acc_type, status)
        self.__card_name = ""
        self.__card_no = ""
        self.__card_expiry = ""
        self.__card_type = ""
        self.__email_verification = "Not Verified"
        self.__purchaseID = []
        self.__reviewID = []
        self.__viewed = ""
        self.__teacher_joined_date = ""
        # Added by Wei Ren for Courses
        self.__shoppingCart = [] # Course IDs & Type here
        self.__purchasedCourses = [] # Course IDs, Type, Timing, Cost here
        self.__viewedCourseObject = ViewsAndRecommendations()

    def set_card_name(self, card_name):
        self.__card_name = card_name
    def set_card_no(self, card_no):
        self.__card_no = card_no
    def set_card_expiry(self, card_expiry):
        self.__card_expiry = card_expiry
    def set_card_type(self, card_type):
        self.__card_type = card_type
    def set_email_verification(self, verify_email):
        self.__email_verification = verify_email
    def set_teacher_join_date(self, join_date):
        self.__teacher_joined_date = join_date

    def set_purchaseID(self, purchaseID):
        self.__purchaseID.append(purchaseID)
    def set_reviewID(self, reviewID):
        self.__reviewID.append(reviewID)

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

    def get_card_name(self):
        return self.__card_name
    def get_card_no(self):
        return self.__card_no
    def get_card_expiry(self):
        return self.__card_expiry
    def get_card_type(self):
        return self.__card_type
    def get_email_verification(self):
        return self.__email_verification
    def get_teacher_join_date(self):
        return self.__teacher_joined_date
    def get_views_recommendations_object(self):
        return self.__viewedCourseObject

    def get_purchaseID(self):
        return self.__purchaseID
    def get_reviewID(self):
        return self.__reviewID
    def get_viewed(self):
        return self.__viewed

    def display_card_info(self):
        print("Username:", self.get_username(), "Acc type:", self.get_acc_type(), "card name:", self.__card_name, "card number:", self.__card_no, "card expiry:", self.__card_expiry, "card type:", self.__card_type)


    # Added by Wei Ren for courses
    def add_to_cart(self, courseID,type):        #e.g. add_to_cart(0,"Zoom")
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
        for paymentID in self.__purchasedCourses.keys():
            course = paymentID.split("_")    # [ID, Type]
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
        return self.__purchasedCourses

    def addCartToPurchases(self, courseID, courseType, timing, cost, transactionID, accountID):
        if [courseID, courseType] in self.__shoppingCart:
            paymentID = courseID + "_" + courseType # ID_Type
            purchase = {paymentID:{'Timing' : timing,'Cost' : cost, "paypalTransactionID" : transactionID, "paypalAccountID" : accountID}}
            self.__purchasedCourses.append(purchase)
            self.__shoppingCart.remove([courseID, courseType])
        else:
            raise Exception("PayPal dislikes you.")

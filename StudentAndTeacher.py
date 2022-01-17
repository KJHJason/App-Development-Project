from User import User
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
        self.__purchasedCourses = {} # Course IDs, Type, Timing, Cost here
        self.__tags_viewed = {"Programming": 0, 
                              "Web Development": 0,
                              "Game Development": 0,
                              "Mobile App Development": 0,
                              "Software Development": 0,
                              "Other Development": 0,
                              "Entrepreneurship": 0,
                              "Project Management": 0,
                              "BI & Analytics": 0,
                              "Business Strategy": 0,
                              "Other Business": 0,
                              "3D Modelling": 0,
                              "Animation": 0,
                              "UX Design": 0,
                              "Design Tools": 0,
                              "Other Design": 0,
                              "Digital Photography": 0,
                              "Photography Tools": 0,
                              "Video Production": 0,
                              "Video Design Tools": 0,
                              "Other Photography/Videography": 0,
                              "Science": 0,
                              "Math": 0,
                              "Language": 0,
                              "Test Prep": 0,
                              "Other Academics": 0}
    
    def set_tags_viewed(self, tagsDict):
        self.__tags_viewed = tagsDict
    def get_tags_viewed(self):
        return self.__tags_viewed
    def change_no_of_view(self, seenTag):
        if seenTag in self.__tags_viewed:
            self.__tags_viewed[seenTag] += 1
        else:
            print("No such tag found.")
    # for scalability reasons but would not be used in this project
    def add_tag(self, newTag):
        self.__tags_viewed[newTag] = 0
    def remove_tag(self, tagToBeRemoved):
        self.__tags_viewed.pop(tagToBeRemoved)

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

    def addCartToPurchases(self, courseID, courseType, date, time, cost, orderID, payerID):
        if [courseID, courseType] in self.__shoppingCart:
            paymentID = courseID + "_" + courseType # ID_Type
            self.__purchasedCourses[paymentID] = {'Date' : date, 'Time' : time, 'Cost' : cost, "PayPalOrderID" : orderID, "PayPalAccountID" : payerID}
            self.__shoppingCart.remove([courseID, courseType])
        else:
            raise Exception("PayPal dislikes you.")

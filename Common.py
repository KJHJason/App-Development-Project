from User import User

class Common(User):
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
        self.__shoppingCart = {} # Course IDs & Type here
        self.__purchasedCourses = {} # Course IDs, Type, Timing, Cost here
        self.__tags_viewed = {"Programming": 0, 
                              "Web_Development": 0,
                              "Game_Development": 0,
                              "Mobile_App_Development": 0,
                              "Software_Development": 0,
                              "Other_Development": 0,
                              "Entrepreneurship": 0,
                              "Project_Management": 0,
                              "BI_Analytics": 0,
                              "Business_Strategy": 0,
                              "Other_Business": 0,
                              "3D_Modelling": 0,
                              "Animation": 0,
                              "UX_Design": 0,
                              "Design_Tools": 0,
                              "Other_Design": 0,
                              "Digital_Photography": 0,
                              "Photography_Tools": 0,
                              "Video_Production": 0,
                              "Video_Design_Tools": 0,
                              "Other_Photography_Videography": 0,
                              "Science": 0,
                              "Math": 0,
                              "Language": 0,
                              "Test_Prep": 0,
                              "Other_Academics": 0}
    
    def set_purchases(self, purchasesDict):
        self.__purchasedCourses = purchasesDict
    def get_purchases(self): # Get a dictionary of the user's purchased courses
        return self.__purchasedCourses

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
    def get_card_name(self):
            return self.__card_name

    def set_card_no(self, card_no):
        self.__card_no = card_no
    def get_card_no(self):
        return self.__card_no

    def set_card_expiry(self, card_expiry):
        self.__card_expiry = card_expiry
    def get_card_expiry(self):
        return self.__card_expiry

    def set_card_type(self, card_type):
        self.__card_type = card_type
    def get_card_type(self):
        return self.__card_type

    def set_email_verification(self, verify_email):
        self.__email_verification = verify_email
    def get_email_verification(self):
        return self.__email_verification

    def set_teacher_join_date(self, join_date):
        self.__teacher_joined_date = join_date
    def get_teacher_join_date(self):
        return self.__teacher_joined_date

    def set_purchaseID(self, purchaseID):
        self.__purchaseID.append(purchaseID)
    def remove_purchaseID(self, purchaseID):
        if purchaseID in self.__purchaseIDs:
            self.__purchaseID.remove(purchaseID)
        else:
            return False

    def set_reviewID(self, reviewID):
        self.__reviewID.append(reviewID)
    def remove_reviewID(self, reviewID):
        if reviewID in self.__reviewIDs:
            self.__reviewIDs.remove(reviewID)
        else:
            return False

    def add_purchaseID(self, purchaseID):
        self.__purchaseIDs.append(purchaseID)
    def get_purchaseID(self):
        return self.__purchaseID
    def remove_purchaseID(self, purchaseID):
        if purchaseID in self.__purchaseIDs:
            self.__purchaseID.remove(purchaseID)
        else:
            return False
    
    def add_reviewID(self, reviewID):
        self.__reviewIDs.append(reviewID)
    def get_reviewID(self):
        return self.__reviewID
    def remove_reviewID(self, reviewID):
        if reviewID in self.__reviewIDs:
            self.__reviewIDs.remove(reviewID)
        else:
            return False

    def set_viewed(self, viewed):
        self.__viewed = viewed
    def get_viewed(self):
        return self.__viewed

    # Added by Wei Ren for courses
    def add_to_cart(self, courseID,type):        #e.g. add_to_cart(0,"Zoom")
        if courseID in list(self.__shoppingCart.keys()):
            if self.__shoppingCart[courseID] != type:
                self.__shoppingCart[courseID] = "Both"
            else:
                print("Course ID", courseID, "Type", type, "already in shopping cart.")
        else:
            self.__shoppingCart[courseID] = type
    def remove_from_cart(self,courseID):
        try:
            self.__shoppingCart.pop(courseID)
        except KeyError:
            print("Course ID", courseID, "Type", type, "not in shopping cart.")
        except:
            print("Unexpected error.")

    def get_cartCourseType(self, courseID):
        try:
            return self.__shoppingCart[courseID]
        except KeyError:
            print("Course ID", courseID, "not in shopping cart.")
            return {}
        except:
            print("Unexpected error.")
            return {}

    def get_purchasesCourseType(self,courseID):
        try:
            return self.__purchasedCourses[courseID]["Course Type"]
        except KeyError:
            print("Course ID", courseID, "not in purchased courses.")
            return {}
        except:
            print("Unexpected error.")
            return {}

    def get_shoppingCart(self):
        return self.__shoppingCart
    def addCartToPurchases(self, courseID, courseType, date, time, cost, orderID, payerID):
        if courseID in list(self.__shoppingCart.keys()):
            self.__purchasedCourses[courseID] = {'Course ID' : courseID, "Course Type" : courseType,'Date' : date, 'Time' : time, 'Cost' : cost, "PayPalOrderID" : orderID, "PayPalAccountID" : payerID}
            self.__shoppingCart.pop(courseID)
        else:
            # raise Exception("PayPal dislikes you.")
            print("PayPal dislikes you.")
from User import User

class Student(User):
    def __init__(self, userID, username, email, password):
        super().__init__(userID, username, email, password, "Student", "Good")
        self.__card_name = ""
        self.__card_no = ""
        self.__card_expiry = ""
        self.__card_cvv = ""
        self.__card_type = ""
        self.__purchaseID = ""
        self.__reviewID = ""
        self.__viewed = ""
        
    def set_card_name(self, card_name):
        self.__card_name = card_name
    def set_card_no(self, card_no):
        self.__card_no = card_no
    def set_card_expiry(self, card_expiry):
        self.__card_expiry = card_expiry
    def set_card_cvv(self, card_cvv):
        self.__card_cvv = card_cvv
    def set_card_type(self, card_type):
        self.__card_type = card_type
    def set_purchaseID(self, purchaseID):
        self.__purchaseID = purchaseID
    def set_reviewID(self, reviewID):
        self.__reviewID = reviewID
    def set_viewed(self, viewed):
        self.__viewed = viewed

    def get_card_name(self):
        return self.__card_name
    def get_card_no(self):
        return self.__card_no
    def get_card_expiry(self):
        return self.__card_expiry
    def get_card_cvv(self):
        return self.__card_cvv
    def get_card_type(self):
        return self.__card_type
    def get_purchaseID(self):
        return self.__purchaseID
    def get_reviewID(self):
        return self.__reviewID
    def get_viewed(self):
        return self.__viewed

    def display_card_info(self):
        print("student's name:", self.get_username(), "card name:", self.__card_name, "card number:", self.__card_no, "card expiry:", self.__card_expiry, "card cvv:", self.__card_cvv, "card type:", self.__card_type)
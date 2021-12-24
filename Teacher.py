from User import User

class Student(User):
    def __init__(self, username, email, password, card_name, card_no, card_expiry, card_cvv, card_type):
        super().__init__(username, email, password, "Teacher", "Good")
        self.__earnings = 0
        self.__card_name = card_name
        self.__card_no = card_no
        self.__card_expiry = card_expiry
        self.__card_cvv = card_cvv
        self.__card_type = card_type

    def self_earnings(self, earnings):
        self.__earnings = earnings

    def get_earnings(self):
        return self.__earnings

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
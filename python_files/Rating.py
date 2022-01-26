# Done by Wei Ren

class Rating():
    def __init__(self, userID, title, comment, rating):
        self.__userID= userID
        self.__title = title
        self.__comment = comment
        self.__rating = rating

    def set_userID(self, userID):
        self.__userID = userID
    def get_userID(self):
        return self.__userID

    def set_title(self, title):
        self.__title = title
    def get_title(self):
        return self.__title

    def set_comment(self, comment):
        self.__comment = comment
    def get_comment(self):
        return self.__comment

    def set_rating(self, rating):
        self.__rating = rating
    def get_rating(self):
        return self.__rating
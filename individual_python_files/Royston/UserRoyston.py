class User:
    # id_count = 0

    def __init__(self, purchaseID, reviewID, viewed):
        # User.id_count += 1
        # self.__user_id = User.id_count
        self.__purchaseID = purchaseID
        self.__reviewID = reviewID
        self.__viewed = viewed


    # def set_user_id(self, user_id):
    #     self__user_id = user_id
    def set_purchaseID(self, purchaseID):
        self.__purchaseID = purchaseID
    def set_reviewID(self, reviewID):
        self.__reviewID = reviewID
    def set_viewed(self, viewed):
        self.__viewed = viewed

    # def get_user_id(self):
    #     return self.__user_id
    def get_purchaseID(self):
        return self.__purchaseID
    def get_reviewID(self):
        return self.__reviewID
    def get_viewed(self):
        return self.__viewed


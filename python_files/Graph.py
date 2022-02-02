from datetime import datetime, date

# Done by Jason

class userbaseGraph:
    def __init__(self, numberOfUsers):
        self.__noOfUser = numberOfUsers
        self.__collectedDate = date.today().strftime("%d-%m-%Y")
        self.__lastUpdated = str(datetime.now().strftime("%d/%m/%Y, %H:%M:%S (UTC +8)"))

    def set_noOfUser(self, numberOfUsers):
        self.__noOfUser = numberOfUsers
    def get_noOfUser(self):
        return self.__noOfUser
        
    def set_date(self, date):
        self.__collectedDate = date.strftime("%d-%m-%Y")
    def get_date(self):
        return self.__collectedDate

    def update_last_updated(self):
        self.__lastUpdated = str(datetime.now().strftime("%d/%m/%Y, %H:%M:%S (UTC +8)"))
    def get_lastUpdate(self):
        return self.__lastUpdated
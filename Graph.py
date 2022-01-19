from datetime import datetime, date

class Graph:
    def __init__(self, numberOfUsers):
        self.__noOfUser = numberOfUsers
        self.__collectedDate = date.today()
        self.__lastUpdated = str(datetime.now().strftime("%d-%m-%Y, %H:%M:%S")).replace("-", "/")

    def set_noOfUser(self, numberOfUsers):
        self.__noOfUser = numberOfUsers
    def get_noOfUser(self):
        return self.__noOfUser
        
    def get_date(self):
        return self.__collectedDate
    def get_lastUpdate(self):
        return self.__lastUpdated
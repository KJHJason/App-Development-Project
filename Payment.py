class Payment():
    paymentID = -1
    def __init__(self,userID, cardName, cardNumber, cardExpiry, firstName, lastName, billingAddress1, billingAddress2, billingAddress3, city, country, zipCode, countryCode, phoneNumber):
        self.__pending = True

        self.__userID = userID

        self.__class__.paymentID += 1
        self.__paymentID = self.__class__.paymentID

        self.__cardName = cardName
        self.__cardNumber = cardNumber
        self.__cardExpiry = cardExpiry
        
        self.firstName = firstName
        self.__lastName = lastName
        
        self.billingAddress1 = billingAddress1
        self.__billingAddress2 = billingAddress2
        self.__billingAddress3 = billingAddress3
        
        self.__city = city
        self.__country = country
        self.__zipCode = zipCode
        
        self.__countryCode = countryCode
        self.__phoneNumber = phoneNumber
        self.__fullNumber = countryCode + phoneNumber

    def get_pending(self):
        return self.__pending
    def set_pending(self, pending):
        self.__pending = pending

    def get_userID(self):
        return self.__userID
    def set_userID(self, userID):
        self.__userID = userID

    def get_paymentID(self):
        return self.__paymentID
    def set_paymentID(self, paymentID):
        self.__paymentID = paymentID

    def get_cardName(self):
        return self.__cardName
    def set_cardName(self,cardName):
        self.__cardName = cardName

    def get_cardNumber(self):
        return self.__cardNumber
    def set_cardNumber(self,cardNumber):
        self.__cardNumber = cardNumber

    def get_cardExpiry(self):
        return self.__cardExpiry
    def set_cardExpiry(self,cardExpiry):
        self.__cardExpiry = cardExpiry

    def get_firstName(self):
        return self.__firstName
    def set_firstName(self,firstName):
        self.__firstName = firstName

    def get_lastName(self):
        return self.__lastName
    def set_lastName(self,lastName):
        self.__lastName = lastName

    def get_billingAddress1(self):
        return self.__billingAddress1
    def set_billingAddress1(self,billingAddress1):
        self.__billingAddress1 = billingAddress1

    def get_billingAddress2(self):
        return self.__billingAddress2
    def set_billingAddress2(self,billingAddress2):
        self.__billingAddress2 = billingAddress2

    def get_billingAddress3(self):
        return self.__billingAddress3
    def set_billingAddress3(self,billingAddress3):
        self.__billingAddress3 = billingAddress3

    def get_city(self):
        return self.__city
    def set_city(self,city):
        self.__city = city

    def get_country(self):
        return self.__country
    def set_country(self,country):
        self.__country = country

    def get_zipCode(self):
        return self.__zipCode
    def set_zipCode(self,zipCode):
        self.__zipCode = zipCode

    def get_countryCode(self):
        return self.__countryCode
    def set_countryCode(self,countryCode):
        self.__countryCode = countryCode

    def get_phoneNumber(self):
        return self.__phoneNumber
    def set_phoneNumber(self,phoneNumber):
        self.__phoneNumber = phoneNumber

    def get_fullNumber(self,fullNumber):
        return(self.__countryCode + self.__phoneNumber)


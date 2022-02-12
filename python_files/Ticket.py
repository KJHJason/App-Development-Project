class Ticket():
    def __init__(self, ticketID, userID, accType, name, email, subject, enquiry):
        self.__ticketID = ticketID
        self.__userID = userID
        self.__accType = accType
        self.__name = name
        self.__email = email
        self.__subject = subject
        self.__enquiry = enquiry
        self.__status = "Open"
        
    def get_ticketID(self):
        return self.__ticketID
    def set_ticketID(self, ticketID):
        self.__ticketID = ticketID
    
    def get_userID(self):
        return self.__userID
    def set_userID(self, userID):
        self.__userID = userID
    
    def get_accType(self):
        return self.__accType
    def set_accType(self, accType):
        self.__accType = accType
    
    def get_name(self):
        return self.__name
    def set_name(self, name):
        self.__name = name
    
    def get_email(self):
        return self.__email
    def set_email(self, email):
        self.__email = email
    
    def get_subject(self):
        return self.__subject
    def set_subject(self, subject):
        self.__subject = subject
    
    def get_enquiry(self):
        return self.__enquiry
    def set_enquiry(self, enquiry):
        self.__enquiry = enquiry
    
    def get_status(self):
        return self.__status
    def set_status(self, status):
        self.__status = status

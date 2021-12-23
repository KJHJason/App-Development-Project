class User:
    id_count = 0

    def __init__(self, username, email, password, acc_type, status):
        User.id_count += 1
        self.__user_id = User.id_count
        self.__username = username
        self.__email = email
        self.__password = password
        self.__acc_type = acc_type
        self.__status = status

    def set_user_id(self, user_id):
        self__user_id = user_id
    def set_username(self, username):
        self.__username = username
    def set_email(self, email):
        self.__email = email
    def set_password(self, password):
        self.__password = password
    def set_acc_type(self, acc_type):
        self.__acc_type = acc_type
    def set_status(self, status):
        self.__status = status
    
    def get_user_id(self):
        return self.__user_id
    def get_username(self):
        return self.__username
    def get_email(self):
        return self.__email
    def get_password(self):
        return self.__password
    def get_acc_type(self):
        return self.__acc_type
    def get_status(self):
        return self.__status
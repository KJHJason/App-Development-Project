from argon2 import PasswordHasher

# Done by Jason

class User:
    def __init__(self, user_id, username, email, password, acc_type, status):
        self.__user_id = user_id
        self.__username = username
        self.__email = email
        self.__password = PasswordHasher().hash(password) # using argon2 to hash the password
        self.__acc_type = acc_type
        self.__status = status
        self.__profile_image = ""

    def set_user_id(self, user_id):
        self.__user_id = user_id
    def get_user_id(self):
        return self.__user_id

    def set_username(self, username):
        self.__username = username
    def get_username(self):
        return self.__username

    def set_email(self, email):
        self.__email = email
    def get_email(self):
        return self.__email

    def set_password(self, password):
        self.__password = password
    def get_password(self):
        return self.__password

    def set_acc_type(self, acc_type):
        self.__acc_type = acc_type
    def get_acc_type(self):
        return self.__acc_type

    def set_status(self, status):
        self.__status = status
    def get_status(self):
        return self.__status

    def set_profile_image(self, imagePath):
        self.__profile_image = imagePath
    def get_profile_image(self):
        return self.__profile_image
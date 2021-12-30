from argon2 import PasswordHasher
import html

"""Password hashing"""

# things to note, argon2 by default will use 65536KB of memory and time is 3 iterations, and 4 degrees of parallelism by default

# minimum requirement as of OWASP; Use Argon2id with a minimum configuration of 15 MiB of memory (15728KB), an iteration count of 2, and 1 degree of parallelism.
# OWASP website: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

class PasswordManager:
    def __init__(self):
        self.hasher = PasswordHasher()

    def salt_password(self, pwd):
        # salting the password for extra security, do not change the salt as all the users' password must have the same salt
        self.__salt = "9#ZcH%"
        self.__salted_pwd = pwd + self.__salt
        return self.__salted_pwd

    def hash_password(self, pwd):
        self.__pwd = self.salt_password(pwd)
        return self.hasher.hash(self.__pwd)

    def verify_password(self, hashed, pwd):
        # try and except as argon2 will raise an exception if the hashes are not matched
        try:
            self.__pwd = self.salt_password(pwd)
            return self.hasher.verify(hashed, self.__pwd)
        except:
            return False

    # different salt for the admin account for extra security as if the user's salt somehow got cracked, the attackers will still have to crack the admin's salt
    def admin_salt_password(self, pwd):
        # salting the password for extra security, do not change the salt as all the admins' password must have the same salt
        self.__admin_salt = "C%qf9D"
        self.__admin_salted_pwd = pwd + self.__admin_salt
        return self.__admin_salted_pwd

    def admin_hash_password(self, pwd):
        self.__admin_pwd = self.admin_salt_password(pwd)
        return self.hasher.hash(self.__admin_pwd)

    def admin_verify_password(self, hashed, pwd):
        # try and except as argon2 will raise an exception if the hashes are not matched
        try:
            self.__admin_pwd = self.admin_salt_password(pwd)
            return self.hasher.verify(hashed, self.__admin_pwd)
        except:
            return False

""" 
# for testing purposes
pwdManager = PasswordManager()
storing_hashed = pwdManager.hash_password("test123")
print(storing_hashed)

inputpwd = "test123"
pwdMatched = pwdManager.verify_password(storing_hashed, inputpwd)

if pwdMatched:
    print("matched")
else:
    print("incorrect hash") """

"""End of Password hashing"""

"""Input sanitisation"""

def Sanitise(userInput):
    userInput = html.escape(userInput, quote=True) # quote = True so that the characters (") and (') are escaped/translated
    userInput = userInput.strip()

    if len(userInput) != 0: # checking the length of the string if it's empty or not (Just in case as this should have been validated when using wtforms)
        return userInput
    else:
        return False

"""End of input sanitisation"""

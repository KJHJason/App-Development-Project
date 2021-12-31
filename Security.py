from argon2 import PasswordHasher
import html

# done by Jason

# helpful resources: 
# https://passlib.readthedocs.io/en/stable/lib/passlib.hash.argon2.html
# https://lindevs.com/generate-argon2id-password-hash-using-python/
# https://passlib.readthedocs.io/en/stable/lib/passlib.hash.argon2.html

"""Password hashing"""

# things to note, argon2 by default will generate a random salt and use 65536KB of memory and time is 3 iterations, and 4 degrees of parallelism when hashing

# minimum requirement as of OWASP; Use Argon2id with a minimum configuration of 15 MiB of memory (15728KB), an iteration count of 2, and 1 degree of parallelism.
# OWASP website: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

class PasswordManager:
    def __init__(self):
        self.hasher = PasswordHasher()

    def hash_password(self, pwd):
        return self.hasher.hash(pwd)

    def verify_password(self, hashed, pwd):
        # try and except as argon2 will raise an exception if the hashes are not matched
        try:
            return self.hasher.verify(hashed, pwd) # will return True if both the hash matches
        except:
            return False

""" # for testing purposes
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

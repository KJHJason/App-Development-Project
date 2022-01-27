from argon2 import PasswordHasher
import html, re # importing html for escaping inputs and re for compiling regular expression for validating email addresses
from shortuuid import ShortUUID # for ID generation using shortuuid as compared to uuid

# Done by Jason

# helpful resources: 
# https://passlib.readthedocs.io/en/stable/lib/passlib.hash.argon2.html
# https://lindevs.com/generate-argon2id-password-hash-using-python/
# https://passlib.readthedocs.io/en/stable/lib/passlib.hash.argon2.html
# https://stackoverflow.com/questions/58431973/argon2-library-that-hashes-passwords-without-a-secret-and-with-a-random-salt-tha

"""Password hashing"""

# things to note, argon2 by default will generate a random salt and use 65536KB of memory and time is 3 iterations, and 4 degrees of parallelism when hashing

# minimum requirement as of OWASP; Use Argon2id with a minimum configuration of 15 MiB of memory (15728KB), an iteration count of 2, and 1 degree of parallelism.
# OWASP website: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

# Password will be automatically hashed when an object is created in User.py.

# for verifying a hashed value with a plaintext to see if it matches
def verify_password(hashed, pwd):
    ph = PasswordHasher()
    # try and except as argon2 will raise an exception if the hashes are not matched
    try:
        return ph.verify(hashed, pwd) # will return True if both the hash matches
    except:
        return False

"""End of Password hashing"""

"""Input sanitisation"""

def sanitise(userInput):
    userInput = html.escape(userInput, quote=False) # quote = False so that the characters (") and (') are not escaped/translated
    userInput = userInput.strip()

    if len(userInput) != 0: # checking the length of the string if it's empty or not (Just in case as this should have been validated when using wtforms)
        return userInput
    else:
        return False

"""End of input sanitisation"""

"""Email Validation using regex/regular expression"""

# useful resources:
# https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/

def validate_email(email):
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+') # compile the regex so that it does not have to rewrite the regex

    if(re.fullmatch(regex, email)):
        return True
    else:
        return False

"""End of Email Validation using regex/regular expression"""

"""Start of Admin Console Functions"""

def validate_pwd_length(pwd, pwdMinimumLength):
    if len(pwd) < pwdMinimumLength:
        print("\nError: Please enter a password with at least {} characters!" .format(pwdMinimumLength))
        return False
    else:
        print("Verdict: Password length accepted, within {} characters minimum requirement." .format(pwdMinimumLength))
        return True

# using shortuuid to generate a 5 character id for the admins.
# out of 10 tests that generated one hundred thousand id(s), there was an average of 16 collisions which is feasible as the number of CourseFinity's support team will only be in the hundreds or thousands.
def generate_admin_id(adminDict):
    generatedID = str(ShortUUID().random(length=5))
    if generatedID in adminDict:
        generate_admin_id(adminDict) # using recursion if there is a collision to generate a new unique ID
    return generatedID

"""End of Admin Console Functions"""
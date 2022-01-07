from argon2 import PasswordHasher
import html, re # importing html for escaping inputs and re for compiling regular expression for validating email addresses

# done by Jason

# helpful resources: 
# https://passlib.readthedocs.io/en/stable/lib/passlib.hash.argon2.html
# https://lindevs.com/generate-argon2id-password-hash-using-python/
# https://passlib.readthedocs.io/en/stable/lib/passlib.hash.argon2.html
# https://stackoverflow.com/questions/58431973/argon2-library-that-hashes-passwords-without-a-secret-and-with-a-random-salt-tha

"""Password hashing"""

# things to note, argon2 by default will generate a random salt and use 65536KB of memory and time is 3 iterations, and 4 degrees of parallelism when hashing

# minimum requirement as of OWASP; Use Argon2id with a minimum configuration of 15 MiB of memory (15728KB), an iteration count of 2, and 1 degree of parallelism.
# OWASP website: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

def hash_password(pwd):
    ph = PasswordHasher()
    return ph.hasher.hash(pwd)

def verify_password(hashed, pwd):
    ph = PasswordHasher()
    # try and except as argon2 will raise an exception if the hashes are not matched
    try:
        return ph.hasher.verify(hashed, pwd) # will return True if both the hash matches
    except:
        return False

"""End of Password hashing"""

"""Input sanitisation"""

def sanitise(userInput):
    userInput = html.escape(userInput, quote=True) # quote = True so that the characters (") and (') are escaped/translated
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
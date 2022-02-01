import html # importing html for escaping inputs
from shortuuid import ShortUUID # for ID generation using shortuuid as compared to uuid

# Done by Jason

"""Input sanitisation"""

def sanitise(userInput):
    userInput = html.escape(userInput, quote=False) # quote = False so that the characters (") and (') are not escaped/translated
    userInput = userInput.strip()

    if len(userInput) != 0: # checking the length of the string if it's empty or not (Just in case as this should have been validated when using wtforms)
        return userInput
    else:
        return False
    
def sanitise_quote(userInput):
    userInput = html.escape(userInput, quote=True) # quote = True so that the characters (") and (') are escaped/translated
    userInput = userInput.strip()

    if len(userInput) != 0: # checking the length of the string if it's empty or not (Just in case as this should have been validated when using wtforms)
        return userInput
    else:
        return False

"""End of input sanitisation"""

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
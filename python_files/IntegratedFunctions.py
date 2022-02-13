from email.mime import image
from __init__ import app, mail
from PIL import Image
from itsdangerous import TimedJSONWebSignatureSerializer as jsonSerializer
from requests import get as pyGet, post as pyPost
from flask_mailman import EmailMessage
import shelve, uuid, string, random, shortuuid, re, json
from pathlib import Path
from flask import url_for
from dicebear import DAvatar, DStyle
from calendar import monthrange
from datetime import date
from os import environ
from .Graph import userbaseGraph

"""Done by Jason"""

# useful resources:
# https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/
# use this function to validate email addresses using regular expressions
def validate_email(email):
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+') # compile the regex so that it does not have to rewrite the regex
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False

# use this function if you want to validate, check if the user is banned, and get the userKey to manipulate the data in the user shelve files (provided you have already opened the user shelve files previously)
def get_key_and_validate(userSession, userDict):
    userKey = userDict.get(userSession)
    userFound = False
    print("ID in session:", userSession)
    if userKey != None:
        print("Verdict: User ID Matched.")
        userFound = True
        userAccStatus = userKey.get_status()
        if userAccStatus == "Good":
            accType = userKey.get_acc_type()
            return userKey, userFound, True, accType
        else:
            return userKey, userFound, False, ""
    else:
        return "", userFound, False, ""


# Use this function if you want to validate the session, check if the user is banned, and get the userKey but not manipulating the data in the user shelve files (usually this will be used for reading the user account data or other data relevant to the user)
def validate_session_get_userKey_open_file(userSession):
    userKey = ""
    userDict = {}
    # Retrieving data from shelve to check validity of the session and to check if the files has been deleted
    try:
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
        userDict = db['Users']
        print("File found.")
        db.close()
    except:
        print("File could not be found.")
        return userKey, False, False, ""

    userFound = False
    print("ID in session:", userSession)
    userKey = userDict.get(userSession)
    if userKey != None:
        print("Verdict: User ID Matched.")
        userFound = True
        userAccStatus = userKey.get_status()
        if userAccStatus == "Good":
            accType = userKey.get_acc_type()
            return userKey, userFound, True, accType
        else:
            return userKey, userFound, False, ""
    else:
        print("Verdict: User ID not found.")
        return userKey, userFound, False, ""

# generate a unique ID using UUID v4 as compared to UUID v1 due to security reasons since UUID v1 generate based on the time + Host MAC address + random component to generate the unique ID but have a 1 in 16384 to have a collision
# However, UUID v4 is completely random but has a very small chance for collision but it is very unlikely to happen
# useful resource: https://stackoverflow.com/questions/53096198/prevent-uuid-collision-in-python-same-process
def generate_ID(inputDict):
    generatedID = str(uuid.uuid4().hex)
    if generatedID in inputDict:
        generate_ID(inputDict) # using recursion if there is a collision to generate a new unique ID
    return generatedID

# ShortUUID with 10 test cases that generated a million ID, there was an average of 0 collisions which is ideal and feasible for now as CourseFinity is still a new business.
# If CourseFinity grows to be a successful hit, changing the length of the ID would not break the whole app
def generate_course_ID(inputDict):
    generatedID = str(shortuuid.ShortUUID().random(length=16)) # using shortuuid to generate a 16 character ID for the course ID which will be used in the url
    if generatedID in inputDict:
        generate_course_ID(inputDict) # using recursion if there is a collision to generate a new unique ID
    return generatedID

# for generating an ID based on a specified length
def generate_ID_to_length(inputDict, length):
    generatedID = str(shortuuid.ShortUUID().random(length=length)) # using shortuuid to generate a 16 character ID for the course ID which will be used in the url
    if generatedID in inputDict:
        generate_ID_to_length(inputDict, length) # using recursion if there is a collision to generate a new unique ID
    return generatedID

def generate_ID_to_length_no_dict(length):
    generatedID = str(shortuuid.ShortUUID().random(length=length)) # using shortuuid to generate a 16 character ID for the course ID which will be used in the url
    return generatedID

def general_page_open_file_with_userKey(userID):
    imagesrcPath = ""
    try:
        adminDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "r")
        adminDict = db['Admins']
        print("File found.")
        db.close()
        fileFound = True
    except:
        print("File could not be found.")
        fileFound = False

    if fileFound:
        adminKey = adminDict.get(userID)
        if adminKey != None:
            print("Verdict: Admin ID Matched.")
            adminImagesrcPath = "/static/images/user/default.png"
            userFound = True
            accStatus = adminKey.get_status()
            if accStatus == "Active":
                accType = adminKey.get_acc_type()
                return adminKey, userFound, True, accType, adminImagesrcPath
            else:
                return adminKey, userFound, False, "", adminImagesrcPath
    try:
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
        userDict = db['Users']
        print("File found.")
        db.close()
    except:
        print("File could not be found.")
        return False, False, False, "", ""

    userFound = False
    userKey = userDict.get(userID)
    if userKey != None:
        print("Verdict: User ID Matched.")
        userFound = True
        accStatus = userKey.get_status()
        if accStatus == "Good":
            imagesrcPath = retrieve_user_profile_pic(userKey)
            accType = userKey.get_acc_type()
            return userKey, userFound, True, accType, imagesrcPath
        else:
            return userKey, userFound, False, "", imagesrcPath
    return None, False, False, "", ""

# use on course page where the user db is already opened
def general_page_open_file_with_userKey_userDict(userID, userDict):
    imagesrcPath = ""
    try:
        adminDict = {}
        adminDB = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "r")
        adminDict = adminDB['Admins']
        print("File found.")
        adminDB.close()
        fileFound = True
    except:
        print("File could not be found.")
        fileFound = False

    if fileFound:
        adminKey = adminDict.get(userID)
        if adminKey != None:
            print("Verdict: Admin ID Matched.")
            adminImagesrcPath = "/static/images/user/default.png"
            userFound = True
            accStatus = adminKey.get_status()
            if accStatus == "Active":
                accType = adminKey.get_acc_type()
                return adminKey, userFound, True, accType, adminImagesrcPath
            else:
                return adminKey, userFound, False, "", adminImagesrcPath

    userFound = False
    userKey = userDict.get(userID)
    if userKey != None:
        print("Verdict: User ID Matched.")
        userFound = True
        accStatus = userKey.get_status()
        if accStatus == "Good":
            imagesrcPath = retrieve_user_profile_pic(userKey)
            accType = userKey.get_acc_type()
            return userKey, userFound, True, accType, imagesrcPath
        else:
            return userKey, userFound, False, "", imagesrcPath
    return None, False, False, "", ""

# use the function below if you just want to validate the session and check if the user is banned but there is no need to manipulate the data in the user shelve data files and also assuming that the user must be logged in, meaning the user shelve data must be present in the directory
def validate_session_open_file(userSession):
    # Retrieving data from shelve to check validity of the session and to check if the files has been deleted
    try:
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
        userDict = db['Users']
        print("File found.")
        db.close()
    except:
        print("File could not be found.")
        # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the guest homepage
        return False, False, ""

    userFound = False
    print("User ID in session:", userSession)
    userKey = userDict.get(userSession)
    if userKey != None:
        print("Verdict: User ID Matched.")
        userFound = True
        accStatus = userKey.get_status()
        if accStatus == "Good":
            accType = userKey.get_acc_type()
            return userFound, True, accType
        else:
            return userFound, False, ""
    else:
        return userFound, False, ""

# use this function to check for any duplicates data in the user shelve files
def check_duplicates(userInput, userDict, infoToCheck):
    if infoToCheck == "username":
        # checking duplicates for username
        print("Retrieving usernames from database.")
        for key in userDict:
            usernameShelveData = userDict[key].get_username()
            if userInput == usernameShelveData:
                print("Username in database:", usernameShelveData)
                print("Username input:", userInput)
                print("Verdict: Username already taken.")
                return True
        return False

    elif infoToCheck == "email":
        # Checking duplicates for email
        print("Retrieving emails from database.")
        for key in userDict:
            emailShelveData = userDict[key].get_email()
            if userInput == emailShelveData:
                print("Email in database:", emailShelveData)
                print("Email input:", userInput)
                print("Verdict: User email already exists.")
                return True
        return False

    else:
        raise Exception('Third argument for check_duplicates() can only take in "username" or "email"!')

# use this function to check for the allowed image extensions when uploading an image to the web app's server
# it will return True or False
# What it does is: converts the filename to a list of strings. For e.g. ["filename", "png"] and retrieve the first index which will be the file extension and lowercase it
def allowed_image_file(filename):
    # try and except as if the user submits a file that does not have any extensions, e.g. "this_is_my_file" which is missing the extension such as .png at the back, it will cause a runtime error
    try:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config["ALLOWED_IMAGE_EXTENSIONS"]
    except:
        return False

# use this function to to get the extension type of a file
# it will return the extension type (e.g. ".png")
def get_extension(filename):
    # try and except as if the user submits a file that does not have any extensions, e.g. "this_is_my_file" which is missing the extension such as .png at the back, it will cause a runtime error
    try:
        extension = filename.rsplit('.', 1)[1].lower() # converts the filename to a list of strings. For e.g. ["filename", "png"] and retrieve the first index which will be the file extension and lowercase it
        extension = "." + str(extension)
        return extension
    except:
        return False

# for overwriting existing files but must validate if the file already exists else it will cause a runtime error
def overwrite_file(file, oldFilePath, newFilePath):
    oldFilePath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)
    file.save(newFilePath)

# use this function to resize your image to the desired dimensions and also compresses it
# do note that the dimensions argument must be in a tuple, e.g. (500, 500)
def resize_image(imagePath, dimensions):
    # try and except as a user might have use a unsupported image file and manually change it to .png, .jpg, etc. in which the Pillow library will raise a runtime error as it is unable to open the image
    try:
        image = Image.open(imagePath).convert("RGB")
        resizedImage = image.resize(dimensions)
        imagePath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)
        newImagePath = imagePath.with_suffix(".webp") # changes the extension to .webp
        resizedImage.save(newImagePath, format="webp", optimize=True, quality=75)
        return True, newImagePath
    except:
        print("Error in resizing and compressing image...")
        return False, ""

# use this function to construct a path for storing files such as images in the web app directory
# pass in a relative path, e.g. "/static/images/users" and a filename, e.g. "test.png"
def construct_path(relativeUploadPath, filename):
    return Path(app.root_path).joinpath(relativeUploadPath, filename)

def dicebear_failsafe(username):
    return f"https://avatars.dicebear.com/api/initials/{username}.svg?size=250&"

# function for retrieving user's profile picture using dicebear library based on the user ID
# Condition: Only use this function when there is no shelve files opened previously
def get_user_profile_pic(userID):
    imagesrcPath = ""

    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
    try:
        if 'Users' in db:
            userDict = db['Users']
        else:
            db.close()
            print("User data in shelve is empty.")
            return imagesrcPath, False
    except:
        db.close()
        print("Error in retrieving Users from user.db")
        return imagesrcPath, False

    userKey = userDict.get(userID)
    profileFileName = userKey.get_profile_image()
    profileFileNameBool = bool(profileFileName)
    profileFilePath = construct_path(app.config["PROFILE_UPLOAD_PATH"], profileFileName)
    profileReset = False
    if profileFileNameBool != False and profileFilePath.is_file():
        imagesrcPath = "/static/images/user/" + profileFileName
    else:
        try:
            imagesrcPath = DAvatar(style=DStyle.initials, seed=userKey.get_username(), options=app.config["DICEBEAR_OPTIONS"]).url_svg
        except:
            # a failsafe if multiple connections are made to dicebear.com and causes a ConnectionResetError to occur
            imagesrcPath = dicebear_failsafe(userKey.get_username())

        if profileFileNameBool != False:
            print("Image file does not exist anymore, resetting user's profile image...")
            # if user profile pic does not exist but the user object has a filename in the profile image attribute, then set the attribute data to empty string
            userObject = userDict.get(userID)
            userObject.set_profile_image("")
            db["Users"] = userDict
            profileReset = True
            print("User's profile image reset successfully.")
            
    db.close()
    return imagesrcPath, profileReset

def get_user_profile_pic_only(userID):
    imagesrcPath = ""

    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
    try:
        if 'Users' in db:
            userDict = db['Users']
        else:
            db.close()
            print("User data in shelve is empty.")
            return imagesrcPath, False
    except:
        db.close()
        print("Error in retrieving Users from user.db")
        return imagesrcPath, False

    userKey = userDict.get(userID)
    profileFileName = userKey.get_profile_image()
    profileFileNameBool = bool(profileFileName)
    profileFilePath = construct_path(app.config["PROFILE_UPLOAD_PATH"], profileFileName)
    if profileFileNameBool != False and profileFilePath.is_file():
        imagesrcPath = "/static/images/user/" + profileFileName
    else:
        try:
            imagesrcPath = DAvatar(style=DStyle.initials, seed=userKey.get_username(), options=app.config["DICEBEAR_OPTIONS"]).url_svg
        except:
            # a failsafe if multiple connections are made to dicebear.com and causes a ConnectionResetError to occur
            imagesrcPath = dicebear_failsafe(userKey.get_username())

        if profileFileNameBool != False:
            print("Image file does not exist anymore, resetting user's profile image...")
            # if user profile pic does not exist but the user object has a filename in the profile image attribute, then set the attribute data to empty string
            userObject = userDict.get(userID)
            userObject.set_profile_image("")
            db["Users"] = userDict
            print("User's profile image reset successfully.")

    db.close()
    return imagesrcPath

# function for retrieving user's profile picture using dicebear library based on only the user's object given
def retrieve_user_profile_pic(userKey):
    profileFileName = userKey.get_profile_image()
    profileFileNameBool = bool(profileFileName)
    profileFilePath = construct_path(app.config["PROFILE_UPLOAD_PATH"], profileFileName)
    if profileFileNameBool != False and profileFilePath.is_file():
        imagesrcPath = "/static/images/user/" + profileFileName
    else:
        try:
            imagesrcPath = DAvatar(style=DStyle.initials, seed=userKey.get_username(), options=app.config["DICEBEAR_OPTIONS"]).url_svg
        except:
            # a failsafe if multiple connections are made to dicebear.com and causes a ConnectionResetError to occur
            imagesrcPath = dicebear_failsafe(userKey.get_username())

    return imagesrcPath

def delete_user_profile(userImageFileName):
    userImageFilePath = construct_path(app.config["PROFILE_UPLOAD_PATH"], userImageFileName)
    # delete the user's profile image file
    userImageFilePath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)

# use the function below if you just want to validate the session and check if the admin is active but there is no need to manipulate the data in the admin shelve data files and also assuming that the admin must be logged in, meaning the admin shelve data must be present in the directory
def admin_validate_session_open_file(adminSession):
    # Retrieving data from shelve to check validity of the session and to check if the files has been deleted
    try:
        adminDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "r")
        adminDict = db['Admins']
        print("File found.")
        db.close()
    except:
        print("File could not be found.")
        # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the guest homepage
        return False, False

    userFound = False
    print("Admin ID in session:", adminSession)
    adminKey = adminDict.get(adminSession)
    if adminKey != None:
        print("Verdict: Admin ID Matched.")
        userFound = True
        accStatus = adminKey.get_status()
        if accStatus == "Active":
            return userFound, True
        else:
            return userFound, False
    else:
        return userFound, False

# use this function if you want to validate, check if the admin is banned, and get the adminKey to manipulate the data in the admin shelve files (provided you have already opened the admin shelve files previously)
def admin_get_key_and_validate(adminSession, adminDict):
    adminKey = ""
    userFound = False
    print("ID in session:", adminSession)
    adminKey = adminDict.get(adminSession)
    if adminKey != None:
        print("Verdict: Admin ID Matched.")
        userFound = True
        accStatus = adminKey.get_status()
        if accStatus == "Active":
            return adminKey, userFound, True
        else:
            return adminKey, userFound, False
    else:
        return adminKey, userFound, False

# Use this function if you want to validate the session, check if the admin is active, and get the adminKey but not manipulating the data in the admin shelve files (usually this will be used for reading the admin account data or other data relevant to the admin)
def admin_get_key_and_validate_open_file(adminSession):
    adminKey = ""
    try:
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "r")
        adminDict = db["Admins"]
        print("File found.")
        db.close()
    except:
        print("No files found.")
        return adminKey, False, False

    userFound = False
    print("Admin ID in session:", adminSession)
    adminKey = adminDict.get(adminSession)
    if adminKey != None:
        print("Verdict: Admin ID Matched.")
        userFound = True
        accStatus = adminKey.get_status()
        if accStatus == "Active":
            return adminKey, userFound, True
        else:
            return adminKey, userFound, False
    else:
        return adminKey, userFound, False

# page number given here must start from 0
# resources that helped me in the pagination algorithm, https://www.tutorialspoint.com/book-pagination-in-python
def paginate(contentList, pageNumber, itemPerPage):
    # mainly using list slicing manipulation
    numOfItemsSeen = pageNumber * itemPerPage # calculating how many items are alrd seen based on the page number given
    return contentList[numOfItemsSeen:numOfItemsSeen+itemPerPage] # then return the sliced list starting from the items already seen and adding the next few items to be seen.

# getting the numbers of pagination buttons to display
def get_pagination_button_list(pageNum, maxPages):
    paginationList = []
    if maxPages <= 5:
        for pageCount in range(maxPages):
            pageCount += 1
            paginationList.append(pageCount)
    else:
        currentFromMax = maxPages - pageNum # calculating the difference from the user's current page to max number of pages
        if pageNum < 4: # if the user's current page number is 3 or less,
            paginationList.append(1)
            paginationList.append(2)
            paginationList.append(3)
            paginationList.append(4)
            paginationList.append(5)
        elif currentFromMax <= 2: # if the difference is 2 or less
            paginationList.append(maxPages - 4)
            paginationList.append(maxPages - 3)
            paginationList.append(maxPages - 2)
            paginationList.append(maxPages - 1)
            paginationList.append(maxPages )
        else:
            paginationList.append(pageNum - 2)
            paginationList.append(pageNum - 1 )
            paginationList.append(pageNum)
            paginationList.append(pageNum + 1)
            paginationList.append(pageNum + 2)

    return paginationList

def check_last_day_of_month(inputDate):
    lastDayOfMonth = monthrange(inputDate.year, inputDate.month)[1] # retrieves the last date of the return tuple value from monthrange, e.g. (5, 31). The value in index 0 is the days of the week on the first day of the month, for e.g. 0 for monday.
    if inputDate == date(inputDate.year, inputDate.month, lastDayOfMonth):
        return True
    else:
        return False

def check_first_day_of_month(inputDate):
    if inputDate == date(inputDate.year, inputDate.month, 1):
        return True
    else:
        return False

# functions for reset password process via email
# helpful resources: https://stackoverflow.com/questions/56699115/timedjsonwebsignatureserializer-vs-urlsafetimedserializer-when-should-i-use-wha
# TimedJsonWebSignatureSerializer uses SHA512 by default
def get_reset_token(emailKey, expires_sec=600): # 10 mins
    s = jsonSerializer(app.config["SECRET_KEY"], expires_sec)
    return s.dumps({"user_id": emailKey.get_user_id()}).decode("utf-8")

def verify_reset_token(token):
    s = jsonSerializer(app.config["SECRET_KEY"])
    # try and except as if the token is invalid, it will raise an exception
    try:
        userID = s.loads(token)["user_id"] # get the token but if the token is invalid or expired, it will raise an exception
        return userID
    except:
        return None

def send_reset_email(email, emailKey):
    token = get_reset_token(emailKey)
    subject, from_email = "[CourseFinity] Password Reset Request", app.config["MAIL_USERNAME"]
    html_content = f"""<p>Hello,</p>

<p>To reset your password, visit the following link:<br>
<a href="{url_for("resetPassword", token=token, _external=True)}" target="_blank">{url_for("resetPassword", token=token, _external=True)}</a></p>

<p>Do note that this link will expire in 10 minutes.<br>
If you did not make this request, please disregard this email.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    message = EmailMessage(subject, html_content, from_email, [email])
    message.content_subtype = "html"
    message.send()

def send_email_change_notification(oldEmail, newEmail):
    subject, from_email = "[CourseFinity] Email Changed", app.config["MAIL_USERNAME"]
    html_content = f"""<p>Hello,</p>

<p>You have recently changed your email from {oldEmail} to {newEmail}</p>

<p>If you did not make this change, your account may have been compromised.<br>
Please contact us if you require assistance with account recovery by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    message = EmailMessage(subject, html_content, from_email, [oldEmail])
    message.content_subtype = "html"
    message.send()

def send_password_change_notification(email):
    subject, from_email = "[CourseFinity] Password Changed", app.config["MAIL_USERNAME"]
    html_content = f"""<p>Hello,</p>

<p>You have recently changed your password.</p>

<p>If you did not make this change, your account may have been compromised.<br>
Please contact us if you require assistance with account recovery by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    message = EmailMessage(subject, html_content, from_email, [email])
    message.content_subtype = "html"
    message.send()

# useful notes for verifying emails: https://www.chargebee.com/blog/avoid-friction-trial-sign-process/
# URLSafeTimedSerializer uses SHA1 by default
def generate_verify_email_token(userID, expires_sec=86400): # 1 day
    s = jsonSerializer(app.config["SECRET_KEY"], expires_sec)
    return s.dumps({"user_id": userID}).decode("utf-8")

def verify_email_token(token):
    s = jsonSerializer(app.config["SECRET_KEY"])
    try:
        userID = s.loads(token)["user_id"] # get the token but if the token is invalid or expired, it will raise an exception
        return userID
    except:
        return None

def send_verify_email(email, userID):
    token = generate_verify_email_token(userID)
    subject, from_email = "[CourseFinity] Welcome to CourseFinity!", app.config["MAIL_USERNAME"]
    html_content = f"""<p>Hello,</p>

<p>Welcome to CourseFinity!<br>
We would like you to verify your email for verifications purposes.</p>

<p>Please click on this link to verify your email:<br>
<a href="{url_for("verifyEmailToken", token=token, _external=True)}" target="_blank">{url_for("verifyEmailToken", token=token, _external=True)}</a></p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Thank you.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    message = EmailMessage(subject, html_content, from_email, [email])
    message.content_subtype = "html"
    message.send()

def send_verify_changed_email(email, oldEmail, userID):
    token = generate_verify_email_token(userID)
    subject, from_email = "[CourseFinity] Verify Updated Email", app.config["MAIL_USERNAME"]
    html_content = f"""<p>Hello,</p>

<p>You have recently updated your email from {oldEmail} to {email}<br>
We would like you to verify your email for verifications purposes.</p>

<p>Please click on this link to verify your email:<br>
<a href="{url_for("verifyEmailToken", token=token, _external=True)}" target="_blank">{url_for("verifyEmailToken", token=token, _external=True)}</a></p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Thank you.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    message = EmailMessage(subject, html_content, from_email, [email])
    message.content_subtype = "html"
    message.send()

def send_another_verify_email(email, userID):
    token = generate_verify_email_token(userID)
    subject, from_email = "[CourseFinity] Verify Email", app.config["MAIL_USERNAME"]
    html_content = f"""<p>Hello,</p>

<p>We would like you to verify your email for verifications purposes.</p>

<p>Please click on this link to verify your email:<br>
<a href="{url_for("verifyEmailToken", token=token, _external=True)}" target="_blank">{url_for("verifyEmailToken", token=token, _external=True)}</a></p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Thank you.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    message = EmailMessage(subject, html_content, from_email, [email])
    message.content_subtype = "html"
    message.send()

def send_admin_reset_email(email, password):
    subject, from_email = "[CourseFinity] Account Recovery Request Accepted", app.config["MAIL_USERNAME"]
    html_content = f"""<p>Hello,</p>

<p>As per requested, we have helped you reset your email and password to the following,<br>
Updated email: {email}<br>
Updated password: {password}</p>

<p>Please use your email and the updated password to login and immediately change the password due to security reasons.<br>
You can login using the following link:<br>
{url_for("userLogin", _external=True)}</p>

<p>Thank you and enjoy learning or teaching at CourseFinity!</p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    message = EmailMessage(subject, html_content, from_email, [email])
    message.content_subtype = "html"
    message.send()

# Sending a follow up email if user has submitted a ban appeal and is accepted.
# However, I am not sending a ban email notification as users who have followed the rules should not be worried about getting banned.
# Hence, upon logging in, if the user is mistakenly banned, he/she will receive a "You have banned" alert from the login and will proceed to contact CourseFinity support email instead.
# If the user knows that they have violated the rules and receives a ban email, they may go on other platform or create another account immediately after the knowledge of their ban. (In a way, without sending a ban email notification, it is delaying their time for actions)
def send_admin_unban_email(email):
    subject, from_email = "[CouseFinity] Ban Appeal Successful", app.config["MAIL_USERNAME"]
    html_content = f"""<p>Hello,</p>

<p>We have looked at your ban appeal application and we have unbanned your account.<br>
We are really sorry for the inconvenience caused and will do our part to investigate the mistake on our end.</p>

<p>Thank you and enjoy learning or teaching at CourseFinity!</p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    message = EmailMessage(subject, html_content, from_email, [email])
    message.content_subtype = "html"
    message.send()

# For generating a 6 character ID using shortuuid library for the support ticket ID.
# Out of 10 test cases that generated one million id(s), there were an average of 206 collisions which is feasible as CourseFinity should not expect a million support tickets to be generated everyday unless the system is intentionally attacked which can be prevented to a certain extent using the flask-limiter.
def generate_6_char_id(ticketDict):
    ticketID = str(shortuuid.ShortUUID().random(length=6)) # generates a 6 characters ID using shortuuid library
    if ticketID in ticketDict: # the ticketDict must use the generated ticketID as the keys for all objects
        generate_6_char_id(ticketDict) # using recursion to generate a new ID if there is a collision
    return ticketID

# use this to send the creation of support ticket notification email to be sent to the user
# for Wei Ren
def send_contact_us_email(ticketID, issueTitle, name, email):
    subject = "[CourseFinity] Support Request - " + issueTitle + " #" + ticketID
    from_email = app.config["MAIL_USERNAME"]
    html_content = f"""<p>Hello {name},</p>

<p>Thanks for contacting CourseFinity support! We have received your request (#{ticketID}) and will respond back as soon as we are able to.</p>

<p>For the fastest resolution to your inquiry, please provide the Support Team with as much information as possible and keep it contained to a single ticket instead of creating a new one.</p>

<p>While you are waiting, you can check out our FAQ page at <a href="{url_for("faq", _external=True)}" target="_blank">{url_for("faq", _external=True)}</a> for solutions to common problems.</p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)}" target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Thank you.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    message = EmailMessage(subject, html_content, from_email, [email])
    message.content_subtype = "html"
    message.send()

def generate_password():
    combinations = string.digits + "!@#$%^&*()" + string.ascii_lowercase + string.ascii_uppercase
    lengthOfPass = 15

    # using random.sample to pick a unique k from the combinations, aka the population, until it meets the lengthOfPass. Hence, if the lengthOfPass exceeds the number of combinations, it will raise a ValueError exception.
    generatedPassword = "".join(random.sample(combinations, lengthOfPass)) # join the generated list for the password
    return generatedPassword

def get_random_courses(courseDict):
    print("Retreiving random courses...")
    userDict = {}
    try:
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
        userDict = db['Users']
        db.close()
        print("File found.")
    except:
        print("File could not be found.")
        # since the shelve files could not be found, it will create a placeholder/empty shelve files
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        db["Users"] = userDict
        db.close()

    recommendCourseList = []
    if len(courseDict) > 3:
        while len(recommendCourseList) != 3:
            try:
                randomisedCourse = random.choice(list(courseDict.values()))
            except:
                break
            if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                if randomisedCourse not in recommendCourseList:
                    recommendCourseList.append(randomisedCourse)
                else:
                    # if course has been recommended already
                    courseDict.pop(randomisedCourse.get_courseID())
            else:
                # if the teacher of the course has been banned
                courseDict.pop(randomisedCourse.get_courseID())
    else:
        for value in courseDict.values():
            if userDict.get(value.get_userID()).get_status() == "Good":
                recommendCourseList.append(value)

    # retrieving course teacher's username
    recommedationDict = {}
    for courses in recommendCourseList:
        teacherObject = userDict.get(courses.get_userID())
        teacherUsername = teacherObject.get_username()
        recommedationDict[courses] = teacherUsername

    return recommedationDict

def saveNoOfUserPerDay():
    graphList = []
    graphDateList = []
    userDict = {}
    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
    currentDate = date.today().strftime("%d-%m-%Y")
    try:
        if 'userGraphData' in db and "Users" in db:
            graphList = db['userGraphData']
            userDict = db['Users']
        else:
            print("No data in user shelve files")
            db["userGraphData"] = graphList
            db['Users'] = userDict
    except:
        print("Error in retrieving Users/userGraphData from user.db")

    for dates in graphList:
        graphDateList.append(dates.get_date())
    if currentDate in graphDateList:
        print("Data already exists, updating old data.")
        graphListValue = graphList[graphDateList.index(currentDate)]
        graphListValue.set_noOfUser(len(userDict))
        graphListValue.update_last_updated()
        db["userGraphData"] = graphList
    else:
        print("Data does not exist, creating new data.")
        graphData = userbaseGraph(len(userDict))
        graphList.append(graphData)
        db["userGraphData"] = graphList
    db.close()

# useful resources: https://stackoverflow.com/questions/185936/how-to-delete-the-contents-of-a-folder
# Function for deleting any QR code due to security reasons
def delete_QR_code_images():
    print("Deleting any 2FA QR code images...")
    folderPath = Path(app.root_path).joinpath("static/images/qrcode")
    for qrCodeImage in folderPath.glob("*"): # .glob("*") yield all the files in folderPath
        if qrCodeImage.is_file():
            qrCodeImage.unlink()

"""End of Done by Jason"""

"""Done by Wei Ren"""

# Adds ellipsis to text to prevent overflow, feel free to add your own limits
def ellipsis(text, textType, wordLimit = None):
    length = 0
    count = 0
    weight = {'a': 60,
              'b': 60,
              'c': 52,
              'd': 60,
              'e': 60,
              'f': 30,
              'g': 60,
              'h': 60,
              'i': 25,
              'j': 25,
              'k': 52,
              'l': 25,
              'm': 87,
              'n': 60,
              'o': 60,
              'p': 60,
              'q': 60,
              'r': 35,
              's': 52,
              't': 30,
              'u': 60,
              'v': 52,
              'w': 77,
              'x': 52,
              'y': 52,
              'z': 52,
              'A': 70,
              'B': 70,
              'C': 77,
              'D': 77,
              'E': 70,
              'F': 65,
              'G': 82,
              'H': 77,
              'I': 30,
              'J': 55,
              'K': 70,
              'L': 60,
              'M': 87,
              'N': 77,
              'O': 82,
              'P': 70,
              'Q': 82,
              'R': 77,
              'S': 70,
              'T': 65,
              'U': 77,
              'V': 70,
              'W': 100,
              'X': 70,
              'Y': 70,
              'Z': 65,
              ' ': 27}
    if wordLimit != None and textType == "Custom":
        wordLimit *= weight['A']
    elif textType == "Title":
        wordLimit = 35*weight['A']
    elif textType == "Description":
        wordLimit = 70*weight['A']
    else:
        return None # You never know.

    for character in list(text):
        currentLength = length
        if character in weight:
            length += weight[character]
        else:
            length += 61 # Average value
        if currentLength < wordLimit and length > wordLimit:
            text = text[:count] + "..."
            break
        else:
            count += 1

    return text
# Weights taken here: https://gist.github.com/imaurer/d330e68e70180c985b380f25e195b90c

def send_ticket_closed_email(ticketID, issueTitle, name, email):
    subject = "[CourseFinity] Support Request - " + issueTitle + " #" + ticketID + " Closed"
    from_email = app.config["MAIL_USERNAME"]
    html_content = f"""<p>Hello {name},</p>

<p>Your ticket #{ticketID} has been closed as the issue has been dealt with by our staff.</p>

<p>If you believe this was an error, please contact our staff as soon as possible to resolve this issue.</p>

<p>Thank you.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    message = EmailMessage(subject, html_content, from_email, [email])
    message.content_subtype = "html"
    message.send()

# Use this to initialise statistics dictionary
"""
{'Courses Created':{'2021':{'January':{{'1st':{'1:00':<value>,
                                               '2:00':<value>,
                                               '3:00':<value>,
                                                ... ...
                                       {'2nd':{}},
                                        ... ...
                                      },
                            'February':{},
                            'March':{},
                             ... ...
                           },
                    '2022':{'January':{}},
                     ... ...
                   },
 'Courses Purchased':{},
  ... ...
}
"""
def create_statistic_dict(*args):

    # Initialised up to 5 years from now
    years = [(date.today().year+count) for count in range(5)]

    statisticDict = {}
    timeDict = {'1:00': 0,'2:00': 0,'3:00': 0,'4:00': 0,'5:00': 0,'6:00': 0,'7:00': 0,'8:00': 0,'9:00': 0,'10:00': 0,'11:00': 0,'12:00': 0,'13:00': 0,'14:00': 0,'15:00': 0,'16:00': 0,'17:00': 0,'18:00': 0,'19:00': 0,'20:00': 0,'21:00': 0,'22:00': 0,'23:00': 0,'24:00': 0}
    months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    dates = ['1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th','11th','12th','13th','14th','15th','16th','17th','18th','19th','20th','21st','22nd','23rd','24th','25th','26th','27th','28th','29th','30th','31st']

    for statisticType in args:
        yearDict = {}
        for year in years:
            monthDict = {}
            for month in months:
                dateDict = {}
                if month in ['January','March','May','July','August','November']:
                    length = 30
                elif month in ['April','June','September','October','December']:
                    length = 31
                elif month == "February" and year % 4 == 0 and not (year % 100 == 0 and year % 400 != 0):
                    length = 29
                else:
                    length = 28

                for dateIndex in range(length):
                    dateDict[dates[dateIndex]] = timeDict

                monthDict[month] = dateDict
            yearDict[str(year)] = monthDict
        statisticDict[statisticType] = yearDict
    return statisticDict


def add_next_statistic_year(statisticDict):
    timeDict = {'1:00': 0,'2:00': 0,'3:00': 0,'4:00': 0,'5:00': 0,'6:00': 0,'7:00': 0,'8:00': 0,'9:00': 0,'10:00': 0,'11:00': 0,'12:00': 0,'13:00': 0,'14:00': 0,'15:00': 0,'16:00': 0,'17:00': 0,'18:00': 0,'19:00': 0,'20:00': 0,'21:00': 0,'22:00': 0,'23:00': 0,'24:00': 0}
    months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    dates = ['1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th','11th','12th','13th','14th','15th','16th','17th','18th','19th','20th','21st','22nd','23rd','24th','25th','26th','27th','28th','29th','30th','31st']

    latestYear = int(list(statisticDict[list(statisticDict.keys())[0]].keys())[-1])
    year = latestYear + 1

    monthDict = {}
    for month in months:
        dateDict = {}
        if month in ['January','March','May','July','August','November']:
            length = 30
        elif month in ['April','June','September','October','December']:
            length = 31
        elif month == "February" and year % 4 == 0 and not (year % 100 == 0 and year % 400 != 0):
            length = 29
        else:
            length = 28

        for dateIndex in range(length):
            dateDict[dates[dateIndex]] = timeDict

        monthDict[month] = dateDict

    for statisticType in list(statisticDict.keys()):
        statisticDict[statisticType][str(year)] = monthDict

    return statisticDict


def add_statistic_type(statisticDict, type):
    timeDict = {'1:00': 0,'2:00': 0,'3:00': 0,'4:00': 0,'5:00': 0,'6:00': 0,'7:00': 0,'8:00': 0,'9:00': 0,'10:00': 0,'11:00': 0,'12:00': 0,'13:00': 0,'14:00': 0,'15:00': 0,'16:00': 0,'17:00': 0,'18:00': 0,'19:00': 0,'20:00': 0,'21:00': 0,'22:00': 0,'23:00': 0,'24:00': 0}
    months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    dates = ['1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th','11th','12th','13th','14th','15th','16th','17th','18th','19th','20th','21st','22nd','23rd','24th','25th','26th','27th','28th','29th','30th','31st']

    years = list(statisticDict[list(statisticDict.keys())[0]].keys())

    yearDict = {}
    for year in years:
        monthDict = {}
        for month in months:
            dateDict = {}
            if month in ['January','March','May','July','August','November']:
                length = 30
            elif month in ['April','June','September','October','December']:
                length = 31
            elif month == "February" and year % 4 == 0 and not (year % 100 == 0 and year % 400 != 0):
                length = 29
            else:
                length = 28

            for dateIndex in range(length):
                dateDict[dates[dateIndex]] = timeDict

            monthDict[month] = dateDict
        yearDict[str(year)] = monthDict
    statisticDict[type] = yearDict

    return statisticDict

# Using client and secret ID to acquire an access token.
# Access token is needed for PayPal payout (but not checkout)
def get_paypal_access_token():
    response = pyPost('https://api-m.sandbox.paypal.com/v1/oauth2/token',
                         headers={'Accept': 'application/json',
                                  'Accept-Language': 'en_US',},
                         data={'grant_type': 'client_credentials'},
                         auth=('AUTh83JMz8mLNGNzpzJRJSbSLUAEp7oe1ieGGqYCmVXpq427DeSVElkHnc0tt70b8gHlWg4yETnLLu1s', environ.get("PAYPAL_SECRET")))

    responseInfo = json.loads(response.text)

    return responseInfo["access_token"]

"""PayPal Payout Info"""
"""
Standard Payouts: How it works
https://developer.paypal.com/docs/payouts/standard/

Getting an Access Token
https://developer.paypal.com/docs/multiparty/get-started/#exchange-your-api-credentials-for-an-access-token

Standard Payout Integrate API
https://developer.paypal.com/docs/payouts/standard/integrate-api/

Customising Payout Intergrate
https://developer.paypal.com/docs/payouts/standard/integrate-api/customize/

PayPal Payouts Live Test
https://www.paypal.com/apex/product-profile/payouts/getAccessToken

Payouts Rest API
https://developer.paypal.com/api/payments.payouts-batch/v1/

Error Messages
https://developer.paypal.com/api/payments.payouts-batch/v1/#errors
"""

"""End of Done by Wei Ren"""

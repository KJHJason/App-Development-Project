from __init__ import app, mail
from PIL import Image
from itsdangerous import TimedJSONWebSignatureSerializer as jsonSerializer
from flask_mail import Message
import shelve, os, uuid, string, random, shortuuid
from pathlib import Path
from flask import url_for
from src import Avatar
from calendar import monthrange
from datetime import date

"""Done by Jason"""

# for uploading images of the user's profile picture to the web app's server configurations
PROFILE_UPLOAD_PATH = 'static/images/user'
THUMBNAIL_UPLOAD_PATH = 'static/images/courses/thumbnails'
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}

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
        db = shelve.open("user", "r")
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
            db.close()
            return userKey, userFound, True, accType
        else:
            db.close()
            return userKey, userFound, False, ""
    else:
        db.close()
        print("Verdict: User ID not found.")
        return userKey, userFound, False, ""

# generate a unique ID using UUID v4 as compared to UUID v1 due to security reasons since UUID v1 generate based on the time + Host MAC address + random component to generate the unique ID but have a 1 in 16384 to have a collision
# However, UUID v4 is completely random but has a very small chance for collision but it is very unlikely to happen
# useful resource: https://stackoverflow.com/questions/53096198/prevent-uuid-collision-in-python-same-process
def generate_ID(inputDict):
    generatedID = str(uuid.uuid4())
    if generatedID in inputDict:
        generate_ID(inputDict) # using recursion if there is a collision to generate a new unique ID
    return generatedID

# ShortUUID with 10 test cases that generated a million ID, there was an average of 0 collisions which is ideal and feasible for now as CourseFinity is still a new business.
# If CourseFinity grows to be a successful hit, changing the length of the ID would not break the whole app
def generate_course_ID(inputDict):
    generatedID = str(shortuuid.ShortUUID().random(length=16)) # using shortuuid to generate a 16 character ID for the course ID which will be used in the url
    if generatedID in inputDict:
        generate_ID(inputDict) # using recursion if there is a collision to generate a new unique ID
    return generatedID

# function to retrieve the acc type and validate the session which will mainly be used on general pages
def general_page_open_file(userID):
    imagesrcPath = ""
    adminImagesrcPath = "/static/images/user/default.png"
    try:
        adminDict = {}
        db = shelve.open("admin", "r")
        adminDict = db['Admins']
        print("File found.")
        db.close()
        fileFound = True
    except:
        print("File could not be found.")
        fileFound = False

    if fileFound:
        print("Admin ID in session:", userID)
        adminKey = adminDict.get(userID)
        if adminKey != None:
            print("Verdict: Admin ID Matched.")
            userFound = True
            accStatus = adminKey.get_status()
            if accStatus == "Active":
                accType = adminKey.get_acc_type()
                return userFound, True, accType, adminImagesrcPath
            else:
                return userFound, False, "", adminImagesrcPath
    try:
        userDict = {}
        db = shelve.open("user", "r")
        userDict = db['Users']
        print("File found.")
        db.close()
    except:
        print("File could not be found.")
        return False, False, "", imagesrcPath

    userFound = False
    print("User ID in session:", userID)
    userKey = userDict.get(userID)
    if userKey != None:
        print("Verdict: User ID Matched.")
        userFound = True
        accStatus = userKey.get_status()
        if accStatus == "Good":
            imagesrcPath = retrieve_user_profile_pic(userKey)
            accType = userKey.get_acc_type()
            return userFound, True, accType, imagesrcPath
        else:
            return userFound, False, "", imagesrcPath
    return None, False, False, ""

def general_page_open_file_with_userKey(userID):
    imagesrcPath = ""
    adminImagesrcPath = "/static/images/user/default.png"
    try:
        adminDict = {}
        db = shelve.open("admin", "r")
        adminDict = db['Admins']
        print("File found.")
        db.close()
        fileFound = True
    except:
        print("File could not be found.")
        fileFound = False

    if fileFound:
        print("Admin ID in session:", userID)
        adminKey = adminDict.get(userID)
        if adminKey != None:
            print("Verdict: Admin ID Matched.")
            userFound = True
            accStatus = adminKey.get_status()
            if accStatus == "Active":
                accType = adminKey.get_acc_type()
                return adminKey, userFound, True, accType, adminImagesrcPath
            else:
                return adminKey, userFound, False, "", adminImagesrcPath
    try:
        userDict = {}
        db = shelve.open("user", "r")
        userDict = db['Users']
        print("File found.")
        db.close()
    except:
        print("File could not be found.")
        return False, False, "", imagesrcPath

    userFound = False
    print("User ID in session:", userID)
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
        db = shelve.open("user", "r")
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
        for key in userDict:
            print("retrieving")
            usernameShelveData = userDict[key].get_username()
            if userInput == usernameShelveData:
                print("Username in database:", usernameShelveData)
                print("Username input:", userInput)
                print("Verdict: Username already taken.")
                return True
            else:
                print("Username in database:", usernameShelveData)
                print("Username input:", userInput)
                print("Verdict: Username is unique.")
        return False

    elif infoToCheck == "email":
        # Checking duplicates for email
        for key in userDict:
            print("retrieving")
            emailShelveData = userDict[key].get_email()
            if userInput == emailShelveData:
                print("Email in database:", emailShelveData)
                print("Email input:", userInput)
                print("Verdict: User email already exists.")
                return True
            else:
                print("Email in database:", emailShelveData)
                print("Email input:", userInput)
                print("Verdict: User email is unique.")
        return False

    else:
        raise Exception('Third argument for get_key() can only take in "username" or "email"!')

# use this function to check for the allowed image extensions when uploading an image to the web app's server
# it will return True or False
# What it does is: converts the filename to a list of strings. For e.g. ["filename", "png"] and retrieve the first index which will be the file extension and lowercase it
def allowed_image_file(filename):
    # try and except as if the user submits a file that does not have any extensions, e.g. "this_is_my_file" which is missing the extension such as .png at the back, it will cause a runtime error
    try:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
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
    os.remove(oldFilePath)
    file.save(newFilePath)

# use this function to resize your image to the desired dimensions
# do note that the dimensions argument must be in a tuple, e.g. (500, 500)
def resize_image(imagePath, dimensions):
    # try and except as a user might have use a unsupported image file and manually change it to .png, .jpg, etc. in which the Pillow library will raise a runtime error as it is unable to open the image
    try:
        image = Image.open(imagePath)
        resizedImage = image.resize(dimensions)
        os.remove(imagePath)
        resizedImage.save(imagePath)
        return True
    except:
        print("Error in resizing user's profile image...")
        return False

# use this function to construct a path for storing files such as images in the web app directory
# pass in a relative path, e.g. "/static/images/users" and a filename, e.g. "test.png"
def construct_path(relativeUploadPath, filename):
    return os.path.join(app.root_path, relativeUploadPath, filename)

# to check if the uploaded file size is within the maximum file size specified by you below in the web app configurations.
# do note that the 2nd argument, maximumFileSize, must be in bytes (e.g. 3 * 1024 * 1024 which is 3145728 bytes or 3MiB)
# also, in order to get the file size before saving onto the server directory, you need javascript to set a cookie that contain the file size in bytes as when I was reading the Flask documentation, I could not find any methods to get the file size when the user submits the form to upload a file
def allow_file_size(fileSize, maximumFileSize):
    if int(fileSize) <= maximumFileSize:
        return True
    else:
        return False

# function for retrieving user's profile picture using dicebear library
def get_user_profile_pic(username, profileFileName, profileFilePath):
    if profileFileName != "" and Path(profileFilePath).is_file():
        imagesrcPath = "/static/images/user/" + profileFileName
    else:
        imagesrcPath = Avatar(type="initials", seed=username)
    return imagesrcPath

# function for retrieving user's profile picture using dicebear library based on only the user's object given
def retrieve_user_profile_pic(userKey):
    profileFileName = userKey.get_profile_image()
    profileFilePath = construct_path(PROFILE_UPLOAD_PATH, profileFileName)
    if profileFileName != "" and Path(profileFilePath).is_file():
        imagesrcPath = "/static/images/user/" + profileFileName
    else:
        imagesrcPath = Avatar(type="initials", seed=userKey.get_username())
    return imagesrcPath

def delete_user_profile(userImageFileName):
    userImageFilePath = construct_path(PROFILE_UPLOAD_PATH, userImageFileName)
    # delete the user's profile image and adding validation to check if the image file path exists just in case as if the file does not exists, it will cause a runtime error/internal server error
    if Path(userImageFilePath).is_file():
        os.remove(userImageFilePath)

# use the function below if you just want to validate the session and check if the admin is active but there is no need to manipulate the data in the admin shelve data files and also assuming that the admin must be logged in, meaning the admin shelve data must be present in the directory
def admin_validate_session_open_file(adminSession):
    # Retrieving data from shelve to check validity of the session and to check if the files has been deleted
    try:
        adminDict = {}
        db = shelve.open("admin", "r")
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
        db = shelve.open("admin", "r")
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
        pageCount = 0
        for i in range(maxPages):
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

def get_two_decimal_pt(numberInput):
    return f"{numberInput:.2f}"

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
    message = Message("[CourseFinity] Password Reset Request", sender="CourseFinity123@gmail.com", recipients=[email])
    message.html = f"""<p>Hello,</p>
    
<p>To reset your password, visit the following link:<br>
<a href="{url_for("resetPassword", token=token, _external=True)}" target="_blank">{url_for("resetPassword", token=token, _external=True)}</a></p>

<p>Do note that this link will expire in 10 minutes.<br>
If you did not make this request, please disregard this email.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    mail.send(message)

def send_email_change_notification(oldEmail, newEmail):
    message = Message("[CourseFinity] Email Changed", sender="CourseFinity123@gmail.com", recipients=[oldEmail])
    message.html = f"""<p>Hello,</p>
    
<p>You have recently changed your email from {oldEmail} to {newEmail}</p>

<p>If you did not make this change, your account may have been compromised.<br>
Please contact us if you require assistance with account recovery by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    mail.send(message)

def send_password_change_notification(email):
    message = Message("[CourseFinity] Password Changed", sender="CourseFinity123@gmail.com", recipients=[email])
    message.html = f"""<p>Hello,</p>
    
<p>You have recently changed your password.</p>

<p>If you did not make this change, your account may have been compromised.<br>
Please contact us if you require assistance with account recovery by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    mail.send(message)

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
    message = Message("[CourseFinity] Welcome to CourseFinity!", sender="CourseFinity123@gmail.com", recipients=[email])
    message.html = f"""<p>Hello,</p>

<p>Welcome to CourseFinity!<br>
We would like you to verify your email for verifications purposes.</p>

<p>Please click on this link to verify your email:<br>
<a href="{url_for("verifyEmailToken", token=token, _external=True)}" target="_blank">{url_for("verifyEmailToken", token=token, _external=True)}</a></p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Thank you.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    mail.send(message)

def send_verify_changed_email(email, oldEmail, userID):
    token = generate_verify_email_token(userID)
    message = Message("[CourseFinity] Verify Updated Email", sender="CourseFinity123@gmail.com", recipients=[email])
    message.html = f"""<p>Hello,</p>

<p>You have recently updated your email from {oldEmail} to {email}<br>
We would like you to verify your email for verifications purposes.</p>

<p>Please click on this link to verify your email:<br>
<a href="{url_for("verifyEmailToken", token=token, _external=True)}" target="_blank">{url_for("verifyEmailToken", token=token, _external=True)}</a></p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Thank you.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    mail.send(message)

def send_another_verify_email(email, userID):
    token = generate_verify_email_token(userID)
    message = Message("[CourseFinity] Verify Email", sender="CourseFinity123@gmail.com", recipients=[email])
    message.html = f"""<p>Hello,</p>

<p>We would like you to verify your email for verifications purposes.</p>

<p>Please click on this link to verify your email:<br>
<a href="{url_for("verifyEmailToken", token=token, _external=True)}" target="_blank">{url_for("verifyEmailToken", token=token, _external=True)}</a></p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Thank you.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    mail.send(message)

def send_admin_reset_email(email, password):
    message = Message("[CourseFinity] Account Recovery Request Accepted", sender="CourseFinity123@gmail.com", recipients=[email])
    message.html = f"""<p>Hello,</p>

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
    mail.send(message)

# Sending a follow up email if user has submitted a ban appeal and is accepted.
# However, I am not sending a ban email notification as users who have followed the rules should not be worried about getting banned.
# Hence, upon logging in, if the user is mistakenly banned, he/she will receive a "You have banned" alert from the login and will proceed to contact CourseFinity support email instead.
# If the user knows that they have violated the rules and receives a ban email, they may go on other platform or create another account immediately after the knowledge of their ban. (In a way, without sending a ban email notification, it is delaying their time for actions)
def send_admin_unban_email(email):
    message = Message("[CouseFinity] Ban Appeal Successful", sender="CourseFinity123@gmail.com", recipients=[email])
    message.html = f"""<p>Hello,</p>

<p>We have looked at your ban appeal application and we have unbanned your account.<br>
We are really sorry for the inconvenience caused and will do our part to investigate the mistake on our end.</p>

<p>Thank you and enjoy learning or teaching at CourseFinity!</p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    mail.send(message)

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
    title = "[CourseFinity] Support Request - " + issueTitle + " #" + ticketID
    message = Message(title, sender="CourseFinity123@gmail.com", recipients=[email])
    message.html = f"""<p>Hello {name},</p>

<p>Thanks for contacting CourseFinity support! We have received your request (#{ticketID}) and will respond back as soon as we are able to.</p>

<p>For the fastest resolution to your inquiry, please provide the Support Team with as much information as possible and keep it contained to a single ticket instead of creating a new one.</p>

<p>While you are waiting, you can check out our FAQ page at <a href="{url_for("home", _external=True)}" target="_blank">{url_for("faq", _external=True)}</a> for solutions to common problems.</p>

<p>Please contact us if you have any questions or concerns. Our customer support can be reached by making a support ticket in the <a href="{url_for("contactUs", _external=True)} target="_blank">contact us page</a>, or contacting support@coursefinity.com</p>

<p>Thank you.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    mail.send(message)

def generate_password():
    combinations = string.digits + "!@#$%^&*()" + string.ascii_lowercase + string.ascii_uppercase
    lengthOfPass = 15

    # using random.sample to pick a unique k from the combinations, aka the population, until it meets the lengthOfPass. Hence, if the lengthOfPass exceeds the number of combinations, it will raise a ValueError exception.
    generatedPassword = "".join(random.sample(combinations, lengthOfPass)) # join the generated list for the password
    return generatedPassword

# to check for unique values in a list or dictionary
def checkUniqueElements(inputToCheck):
    listOf = []
    if isinstance(inputToCheck, dict):
        for values in inputToCheck.values():
            listOf.append(values)
        uniqueNumbersOfViews = len(set(listOf)) # get numbers of unique values in dictionary
    elif isinstance(inputToCheck, list):
        for value in inputToCheck:
            listOf.append(value)
        uniqueNumbersOfViews = len(set(listOf)) # get numbers of unique values in the list
    else:
        raise Exception("Function checkUniqueElements can only accept dictionary or lists!")
    return uniqueNumbersOfViews

def get_random_courses(courseDict):
    recommendCourseList = []
    if len(courseDict) > 3:
        while len(recommendCourseList) != 3:
            randomisedCourse = random.choice(list(courseDict.values()))
            if randomisedCourse not in recommendCourseList:
                recommendCourseList.append(randomisedCourse)
    else:
        for value in courseDict.values():
            recommendCourseList.append(value)
    return recommendCourseList

"""Done by Jason"""

"""Done by Wei Ren"""

# Adds ellipsis to text to prevent overflow, feel free to add your own limits
def ellipsis(text, textType):
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
    if textType == "Title":
        wordLimit = 30*weight['A']

    elif textType == "Description":
        wordLimit = 130*weight['A']
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

"""Done by Wei Ren"""

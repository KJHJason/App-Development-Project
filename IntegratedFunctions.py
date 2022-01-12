from __init__ import app, mail
from PIL import Image
from itsdangerous import TimedJSONWebSignatureSerializer as jsonSerializer
from flask_mail import Message
import shelve, os, uuid, string, random
from flask import url_for

"""Done by Jason"""

# for uploading images of the user's profile picture to the web app's server configurations
PROFILE_UPLOAD_PATH = 'static/images/user'
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
    generatedID = str(uuid.uuid4())
    if generatedID in inputDict:
        generate_ID(inputDict) # using recursion if there is a collision to generate a new unique ID
    return generatedID

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
def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# use this function to to get the extension type of a file
# it will return the extension type (e.g. ".png")
def get_extension(filename):
    extension = filename.rsplit('.', 1)[1].lower()
    extension = "." + str(extension)
    return extension

# for overwriting existing files but must validate if the file already exists else it will cause a runtime error
def overwrite_file(file, oldFilePath, newFilePath):
    os.remove(oldFilePath)
    file.save(newFilePath)

# use this function to resize your image to the desired dimensions
# do note that the dimensions argument must be in a tuple, e.g. (500, 500)
def resize_image(imagePath, dimensions):
    image = Image.open(imagePath)
    resizedImage = image.resize(dimensions)
    os.remove(imagePath)
    resizedImage.save(imagePath)

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
    message.body = f"""Hello,
    
To reset your password, visit the following link:
{url_for("resetPassword", token=token, _external=True)}

Do note that this link will expire in 10 minutes.
If you did not make this request, please disregard this email.

Sincerely,
CourseFinity Team
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
    message.body = f"""Hello,

Welcome to CourseFinity!
We would like you to verify your email for verifications purposes.

Please click on this link to verify your email:
{url_for("verifyEmailToken", token=token, _external=True)}

Please contact us if you have any questions or concerns. Our customer support can be reached by replying to this email, or contacting support@coursefinity.com

Thank you.

Sincerely,
CourseFinity Team
"""
    mail.send(message)

def send_verify_changed_email(email, oldEmail, userID):
    token = generate_verify_email_token(userID)
    message = Message("[CourseFinity] Email Changed", sender="CourseFinity123@gmail.com", recipients=[email])
    message.body = f"""Hello,

You have recently updated your email from {oldEmail} to {email}.
We would like you to verify your email for verifications purposes.

Please click on this link to verify your email:
{url_for("verifyEmailToken", token=token, _external=True)}

Please contact us if you have any questions or concerns. Our customer support can be reached by replying to this email, or contacting support@coursefinity.com

Thank you.

Sincerely,
CourseFinity Team
"""
    mail.send(message)

def send_another_verify_email(email, userID):
    token = generate_verify_email_token(userID)
    message = Message("[CourseFinity] Verify Email", sender="CourseFinity123@gmail.com", recipients=[email])
    message.body = f"""Hello,

We would like you to verify your email for verifications purposes.

Please click on this link to verify your email:
{url_for("verifyEmailToken", token=token, _external=True)}

Please contact us if you have any questions or concerns. Our customer support can be reached by replying to this email, or contacting support@coursefinity.com

Thank you.

Sincerely,
CourseFinity Team
"""
    mail.send(message)

def send_admin_reset_email(email, password):
    message = Message("[CourseFinity] Account Recovery Request Accepted", sender="CourseFinity123@gmail.com", recipients=[email])
    message.body = f"""Hello,

As per requested, we have helped you reset your email and password to the following,
Updated email: {email}
Updated password: {password}

Please use your email and the updated password to login and immediately change the password due to security reasons.
You can login using the following link:
{url_for("userLogin", _external=True)}

Thank you and enjoy learning or teaching at CourseFinity!

Please contact us if you have any questions or concerns. Our customer support can be reached by replying to this email, or contacting support@coursefinity.com

Sincerely,
CourseFinity Team
"""
    mail.send(message)

# Sending a follow up email if user has submitted a ban appeal and is accepted.
# However, I am not sending a ban email notification as users who have followed the rules should not be worried about getting banned.
# Hence, upon logging in, if the user is mistakenly banned, he/she will receive a "You have banned" alert from the login and will proceed to contact CourseFinity support email instead.
# If the user knows that they have violated the rules and receives a ban email, they may go on other platform or create another account immediately after the knowledge of their ban. (In a way, without sending a ban email notification, it is delaying their time for actions)
def send_admin_unban_email(email):
    message = Message("You have been unbanned from CourseFinity", sender="CourseFinity123@gmail.com", recipients=[email])
    message.body = f"""Hello,

We have looked at your ban appeal application and we have unbanned your account.
We are really sorry for the inconvenience caused and will do our part to investigate the mistake on our end.

Thank you and enjoy learning or teaching at CourseFinity!

Please contact us if you have any questions or concerns. Our customer support can be reached by replying to this email, or contacting support@coursefinity.com

Sincerely,
CourseFinity Team
"""
    mail.send(message)

# use this function for the contact us page
# for this to work, please feed in the title of the user's issue, the user ID of the user, the name of the user, the email of the user, and the main message/body content obtained from the body form
# please also check for cross site scripting and potential security risk by testing the form inputs
# note: gmail is safe from cross site scripting and it is currently using the home url as placeholder as the FAQ page is not done yet.
def send_contact_us_email(issueTitle, userID, name, email, bodyContent):
    id = str(uuid.uuid4())
    title = "[CourseFinity] Support Request - " + issueTitle + " #" + id
    message = Message(title, sender="CourseFinity123@gmail.com", recipients=[email])
    message.html = f"""<p>Hello {name},</p>

<p>Thanks for contacting CourseFinity support! We have received your request (#{id}) and will respond back as soon as we are able to.</p>

<p>For the fastest resolution to your inquiry, please provide the Support Team with as much information as possible and keep it contained to a single ticket instead of creating a new one.</p>

<p>While you are waiting, you can check out our FAQ page at <a href="{url_for("home", _external=True)}" target="_blank">{url_for("home", _external=True)}</a> for solutions to common problems.</p>

<p>Please reply to this email if you have any further questions or concerns.</p>

<p>Thank you.</p>

<p>Sincerely,<br>
<b>CourseFinity Team</b></p>
"""
    mail.send(message)

    # sending another email for a copy of the user's problem to the admin to refer
    title = "[CourseFinity] Support Ticket - " + issueTitle + " #" + id
    message = Message(title, sender="CourseFinity123@gmail.com", recipients=["CourseFinity123@gmail.com"])
    message.body = f"""Hello,

Please refer to the user's problem below:
(Warning: Please do NOT click on suspicious looking links that were sent by the user!)
{bodyContent}

User's info:
User ID: {userID}
Name: {name}
Email: {email}

Afterwards, please reply to the email with the ticket #{id} in the sent emails folder.

Thank you and have a nice day.
This email was auto-generated by the system. Please do not reply to this email.
"""
    mail.send(message)

def generate_password():
    combinations = string.digits + "!@#$%^&*()" + string.ascii_lowercase + string.ascii_uppercase
    lengthOfPass = 15

    # using random.sample to pick a unique k from the combinations, aka the population, until it meets the lengthOfPass. Hence, if the lengthOfPass exceeds the number of combinations, it will raise a ValueError exception.
    generatedPassword = "".join(random.sample(combinations, lengthOfPass)) # join the generated list for the password
    return generatedPassword

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

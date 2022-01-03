from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import shelve, Forms, os, math
import Student, Teacher, Admin
from Security import password_manager, sanitise, validate_email
from CardValidation import validate_card_number, get_card_type, validate_cvv, validate_formatted_expiry_date, validate_expiry_date
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
from PIL import Image
from itsdangerous import TimedJSONWebSignatureSerializer as serializer
from flask_mail import Mail, Message

"""Web app configurations"""

# general Flask configurations
app = Flask(__name__)
app.config["SECRET_KEY"] = "a secret key" # for demonstration purposes, if deployed, change it to something more secure

# for uploading images of the user's profile picture to the web app's server configurations
PROFILE_UPLOAD_PATH = 'static/images/user'
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}

# Maximum file size for uploading anything to the web app's server
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024 # 15MiB
app.config['MAX_PROFILE_IMAGE_FILESIZE'] = 1 * 1024 * 1024 # 1MiB

# configuration for email
app.config["MAIL_SERVER"] = "smtp.googlemail.com" # using gmail
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "CourseFinity123@gmail.com" # using gmail
app.config["MAIL_PASSWORD"] = "W8SX696Tz3"
mail = Mail(app)

# Flask limiter configuration
limiter = Limiter(app, key_func=get_remote_address)

"""End of Web app configurations"""

"""Useful Functions by Jason"""

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
            return userKey, userFound, True
        else:
            return userKey, userFound, False
    else:
        return "", userFound, False
    

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
        return userKey, False, False
        
    userFound = False
    print("ID in session:", userSession)
    userKey = userDict.get(userSession)
    if userKey != None:
        print("Verdict: User ID Matched.")
        userFound = True
        userAccStatus = userKey.get_status()
        if userAccStatus == "Good":
            return userKey, userFound, True
        else:
            return userKey, userFound, False
    else:
        print("Verdict: User ID not found.")
        return userKey, userFound, False
    

# use this function if you just want to get the next possible userID based on the user shelve files
# (provided you have already opened the user shelve files previously)
def get_userID(userDict):
    userIDShelveData = 0 # initialise to 0 as the shelve files can be missing or new which will have no data
    for key in userDict:
        print("retrieving")
        userIDShelveData = int(userDict[key].get_user_id())
        print("ID in database:", userIDShelveData)
        userIDShelveData += 1 # add 1 to get the next possible user ID if there is/are user data in the user shelve files
    return userIDShelveData

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
        return False, False
        
    userFound = False
    print("User ID in session:", userSession)
    userKey = userDict.get(userSession)
    if userKey != None:
        print("Verdict: User ID Matched.")
        userFound = True
        accStatus = userKey.get_status()
        if accStatus == "Good":
            return userFound, True
        else:
            return userFound, False
    else:
        return userFound, False

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
def get_reset_token(userKey, expires_sec=600): # 10 mins
    s = serializer(app.config["SECRET_KEY"], expires_sec)
    return s.dumps({"user_id": userKey.get_user_id()}).decode("utf-8")

def verify_reset_token(token):
    s = serializer(app.config["SECRET_KEY"])
    try:
        userID = s.loads(token)["user_id"] # get the token but if the token is invalid or expired, it will raise an exception
        return userID
    except:
        return None

def send_reset_email(email, email_key):
    token = get_reset_token(email_key)
    message = Message("Password Reset Request", sender="CourseFinity123@gmail.com", recipients=[email])
    message.body = f"""To reset your password, visit the following link
{url_for("resetPassword", token=token, _external=True)}

If you did not make this request, please ignore this email.
"""
    mail.send(message)

"""End of Useful Functions by Jason"""

"""General pages by INSERT_YOUR_NAME"""

@app.route('/', methods=["GET","POST"])
def home():
    # checking sessions if the had recently logged out
    if "recentlyLoggedOut" in session:
        recentlyLoggedOut = True
        session.pop("recentlyLoggedOut", None)
        print("User recently logged out?:", recentlyLoggedOut)
    else:
        recentlyLoggedOut = False
        print("User recently logged out?:", recentlyLoggedOut)

    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)
        
        if userFound and accActive:
            return render_template('users/admin/admin_home.html')
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return render_template('users/guest/guest_home.html')
    else:
        if "userSession" in session:
            userSession = session["userSession"]
            print(userSession)

            # checking if the teacher recently added their payment method when signing up
            if "teacherPaymentAdded" in session:
                teacherPaymentAdded = True
                session.pop("teacherPaymentAdded", None)
            else:
                teacherPaymentAdded = False

            userFound, accGoodStatus = validate_session_open_file(userSession)

            if userFound and accGoodStatus:
                return render_template('users/loggedin/user_home.html', teacherPaymentAdded=teacherPaymentAdded)
            else:
                print("User not found or is banned.")
                # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return render_template('users/guest/guest_home.html')
        else:
            return render_template('users/guest/guest_home.html', recentlyLoggedOut=recentlyLoggedOut)

"""End of General pages by INSERT_YOUR_NAME"""

"""User login and logout by Jason"""

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("2/second") # to prevent attackers from trying to crack passwords by sending too many automated requests from their ip address
def userLogin():
    if "userSession" not in session and "adminSession" not in session:
        create_login_form = Forms.CreateLoginForm(request.form)
        if "passwordUpdated" in session:
            passwordUpdated = True
            session.pop("passwordUpdated", None)
        else:
            passwordUpdated = False

        if request.method == "POST" and create_login_form.validate():
            emailInput = sanitise(create_login_form.email.data.lower())
            passwordInput = create_login_form.password.data
            try:
                userDict = {}
                db = shelve.open("user", "r")
                userDict = db['Users']
                db.close()
                print("File found.")
            except:
                print("File could not be found.")
                # since the shelve files could not be found, it will create a placeholder/empty shelve files so that user can submit the login form but will still be unable to login
                userDict = {}
                db = shelve.open("user", "c")
                db["Users"] = userDict
                db.close()

            # Declaring the 4 variables below to prevent UnboundLocalError
            email_found = False
            password_matched = False
            passwordShelveData = ""
            emailShelveData = ""

            # Checking the email input and see if it matches with any in the database
            for key in userDict:
                emailShelveData = userDict[key].get_email()
                if emailInput == emailShelveData:
                    email_key = userDict[key]
                    email_found = True
                    print("Email in database:", emailShelveData)
                    print("Email Input:", emailInput)
                    break
                else:
                    print("User email not found.")
                    
            # if the email is found in the shelve database, it will then validate the password input and see if it matches with the one in the database
            if email_found:
                passwordShelveData = email_key.get_password()
                print("Password in database:", passwordShelveData)
                print("Password Input:", passwordInput)

                password_matched = password_manager().verify_password(passwordShelveData, passwordInput)
                
                # printing for debugging purposes
                if password_matched:
                    print("Correct password!")
                else:
                    print("Password incorrect.")
                    
            if email_found and password_matched:
                print("User validated...")
                print("Email in database:", emailShelveData)
                print("Email Input:", emailInput)
                print("Password in database:", passwordShelveData)
                print("Password Input:", passwordInput)
                print("Account type:", email_key.get_acc_type())

                # checking if the user is banned
                accGoodStatus = email_key.get_status()
                if accGoodStatus == "Good":
                    # setting the user session based on the user's user ID
                    userID = email_key.get_user_id()
                    session["userSession"] = userID
                    print("User account not banned, login successful.")
                    return redirect(url_for("home"))
                else:
                    print("User account banned.")
                    return render_template('users/guest/login.html', form=create_login_form, banned=True)
            else:
                print("Email in database:", emailShelveData)
                print("Email Input:", emailInput)
                print("Password in database:", passwordShelveData)
                print("Password Input:", passwordInput)
                return render_template('users/guest/login.html', form=create_login_form, failedAttempt=True)
        else:
            return render_template('users/guest/login.html', form=create_login_form, passwordUpdated=passwordUpdated)
    else:
        return redirect(url_for("home"))

@app.route('/logout')
def logout():
    if "userSession" in session:
        session.pop("userSession", None)
    elif "adminSession" in session:
        session.pop("adminSession", None)
    else:
        return redirect(url_for("home"))
    
    # sending a session data so that when it redirects the user to the homepage, jinja2 will render out a logout alert
    session["recentlyLoggedOut"] = True
    return redirect(url_for("home"))

"""End of User login and logout by Jason"""

"""Reset Password by Jason"""

@app.route('/reset_password', methods=['GET', 'POST'])
def requestPasswordReset():
    if "userSession" not in session and "adminSession" not in session:
        create_request_form = Forms.RequestResetPasswordForm(request.form)
        if "invalidToken" in session:
            invalidToken = True
            session.pop("invalidToken", None)
        else:
            invalidToken = False

        if request.method == "POST" and create_request_form.validate():
            emailInput = sanitise(create_request_form.email.data.lower())
            try:
                userDict = {}
                db = shelve.open("user", "r")
                userDict = db['Users']
                db.close()
                print("File found.")
            except:
                print("File could not be found.")
                # since the shelve files could not be found, it will create a placeholder/empty shelve files so that user can submit the login form but will still be unable to login
                userDict = {}
                db = shelve.open("user", "c")
                db["Users"] = userDict
                db.close()

            # Declaring the 4 variables below to prevent UnboundLocalError
            email_found = False
            emailShelveData = ""

            # Checking the email input and see if it matches with any in the database
            for key in userDict:
                emailShelveData = userDict[key].get_email()
                if emailInput == emailShelveData:
                    email_key = userDict[key]
                    email_found = True
                    print("Email in database:", emailShelveData)
                    print("Email Input:", emailInput)
                    break
                else:
                    print("User email not found.")
                
            if email_found:
                print("User email found...")
                print("Email in database:", emailShelveData)
                print("Email Input:", emailInput)

                # checking if the user is banned
                accGoodStatus = email_key.get_status()
                if accGoodStatus == "Good":
                    send_reset_email(emailInput, email_key)
                    print("Email sent")
                    print("User account not banned, login successful.")
                    return render_template('users/guest/request_password_reset.html', form=create_request_form, emailSent=True)
                else:
                    print("User account banned.")
                    return render_template('users/guest/request_password_reset.html', form=create_request_form, banned=True)
            else:
                print("Email in database:", emailShelveData)
                print("Email Input:", emailInput)
                return render_template('users/guest/request_password_reset.html', form=create_request_form, invalidEmail=True)
        else:
            return render_template('users/guest/request_password_reset.html', form=create_request_form, invalidToken=invalidToken)
    else:
        return redirect(url_for("home"))

@app.route("/reset_password_form/<token>", methods=['GET', 'POST'])
def resetPassword(token):
    if "userSession" not in session and "adminSession" not in session:
        validateToken = verify_reset_token(token)
        if validateToken != None:
            create_reset_password_form = Forms.CreateResetPasswordForm(request.form)
            if request.method == "POST" and create_reset_password_form.validate():
                password = create_reset_password_form.resetPassword.data
                confirmPassword = create_reset_password_form.confirmPassword.data

                if password == confirmPassword:
                    userDict = {}
                    db = shelve.open("user", "c")  # "c" flag as to create the files if there were no files to retrieve from and also to create the user if the validation conditions are met
                    try:
                        if 'Users' in db:
                            userDict = db['Users']
                        else:
                            print("No user data in user shelve files.")
                            db["Users"] = userDict
                    except:
                        db.close()
                        print("Error in retrieving Users from user.db")
                        return redirect(url_for("home"))

                    userKey = userDict.get(validateToken)
                    # checking if the user is banned
                    accGoodStatus = userKey.get_status()
                    if accGoodStatus == "Good":
                        hashedPassword = password_manager().hash_password(password)
                        userKey.set_password(hashedPassword)
                        db["Users"] = userDict
                        db.close()
                        print("Password Reset Successful.")
                        session["passwordUpdated"] = True
                        return redirect(url_for("userLogin"))
                    else:
                        print("User account banned.")
                        return render_template('users/guest/reset_password.html', form=create_reset_password_form, banned=True)
                else:
                    return render_template('users/guest/reset_password.html', form=create_reset_password_form, pwd_were_not_matched=True)
            else:
                return render_template('users/guest/reset_password.html', form=create_reset_password_form)
        else:
            session["invalidToken"] = True
            return redirect(url_for("requestPasswordReset"))
    else:
        return redirect(url_for("home"))

"""End of Reset Password by Jason"""

"""Student signup process by Jason"""
@app.route('/signup', methods=['GET', 'POST'])
def userSignUp():
    if "userSession" not in session and "adminSession" not in session:
        create_signup_form = Forms.CreateSignUpForm(request.form)
        if request.method == 'POST' and create_signup_form.validate():
            
            # Declaring the 2 variables below to prevent UnboundLocalError
            email_duplicates = False
            username_duplicates = False

            cfmPassword = create_signup_form.cfm_password.data
            passwordInput = create_signup_form.password.data

            # Checking if the password and confirm passwords inputs were the same
            if cfmPassword == passwordInput:
                pwd_were_not_matched = False
                print("Password matched")
            else:
                pwd_were_not_matched = True
                print("Password not matched")

            emailInput = sanitise(create_signup_form.email.data.lower())
            emailValid = validate_email(emailInput)
            if emailValid:

                usernameInput = sanitise(create_signup_form.username.data)

                # Retrieving data from shelve for duplicate data checking
                userDict = {}
                db = shelve.open("user", "c")  # "c" flag as to create the files if there were no files to retrieve from and also to create the user if the validation conditions are met
                try:
                    if 'Users' in db:
                        userDict = db['Users']
                    else:
                        print("No user data in user shelve files.")
                        db["Users"] = userDict
                except:
                    db.close()
                    print("Error in retrieving Users from user.db")
                    return redirect(url_for("home"))

                # Checking duplicates for email and username
                email_duplicates = check_duplicates(emailInput, userDict, "email")
                username_duplicates = check_duplicates(usernameInput, userDict, "username")
                
                # If there were no duplicates and passwords entered were the same, create a new user
                if (pwd_were_not_matched == False) and (email_duplicates == False) and (username_duplicates == False):
                    hashedPwd = password_manager().hash_password(passwordInput)
                    print("Hashed password:", hashedPwd)

                    # setting user ID for the user
                    userID = get_userID(userDict)
                    print("User ID setted: ", userID)

                    user = Student.Student(userID, usernameInput, emailInput, hashedPwd)
                    print(user)

                    userDict[userID] = user
                    db["Users"] = userDict
                    
                    print(userDict)

                    db.close()
                    print("User added.")
                    session["userSession"] = userID
                    return redirect(url_for("home"))
                else:
                    # if there were still duplicates or passwords entered were not the same, used Jinja to show the error messages
                    db.close()
                    print("Validation conditions were not met.")
                    return render_template('users/guest/signup.html', form=create_signup_form, email_duplicates=email_duplicates, username_duplicates=username_duplicates, pwd_were_not_matched=pwd_were_not_matched) 
            else:
                return render_template('users/guest/signup.html', form=create_signup_form, emailInvalid=True)
        else:
            return render_template('users/guest/signup.html', form=create_signup_form)    
    else:
        return redirect(url_for("home"))

"""End of Student signup process by Jason"""

"""Teacher's signup process by Jason"""

@app.route('/teacher_signup', methods=['GET', 'POST'])
def teacherSignUp():
    if "userSession" not in session and "adminSession" not in session:
        create_teacher_sign_up_form = Forms.CreateTeacherSignUpForm(request.form)
    
        if request.method == 'POST' and create_teacher_sign_up_form.validate():
            # Declaring the 2 variables below to prevent UnboundLocalError
            email_duplicates = False
            username_duplicates = False

            cfmPassword = create_teacher_sign_up_form.cfm_password.data
            passwordInput = create_teacher_sign_up_form.password.data

            # Checking if the password and confirm passwords inputs were the same
            if cfmPassword == passwordInput:
                pwd_were_not_matched = False
                print("Password matched")
            else:
                pwd_were_not_matched = True
                print("Password not matched")

            emailInput = sanitise(create_teacher_sign_up_form.email.data.lower())
            emailValid = validate_email(emailInput)

            if emailValid:
                usernameInput = sanitise(create_teacher_sign_up_form.username.data)

                # Retrieving data from shelve for duplicate data checking
                userDict = {}
                db = shelve.open("user", "c")  # "c" flag as to create the files if there were no files to retrieve from and also to create the user if the validation conditions are met
                try:
                    if 'Users' in db:
                        userDict = db['Users']
                    else:
                        print("No user data in user shelve files")
                        db["Users"] = userDict
                except:
                    db.close()
                    print("Error in retrieving Users from user.db")
                    return redirect(url_for("home"))

                # Checking duplicates for email and username
                email_duplicates = check_duplicates(emailInput, userDict, "email")
                username_duplicates = check_duplicates(usernameInput, userDict, "username")

                if (pwd_were_not_matched == False) and (email_duplicates == False) and (username_duplicates == False):
                    print("User info validated.")
                    hashedPwd = password_manager().hash_password(passwordInput)
                    print("Hashed password:", hashedPwd)

                    # setting user ID for the teacher
                    userID = get_userID(userDict)
                    print("User ID setted: ", userID)

                    user = Teacher.Teacher(userID, usernameInput, emailInput, hashedPwd)
                    print(user)

                    userDict[userID] = user
                    db["Users"] = userDict
                    
                    session["teacher"] = userID # to send the user ID under the teacher session for user verification in the sign up payment process

                    print(userDict)
                    print("Teacher added.")

                    db.close()
                    
                    session["userSession"] = userID

                    return redirect(url_for("signUpPayment"))
                else:
                    # if there were still duplicates or passwords entered were not the same, used Jinja to show the error messages
                    db.close()
                    print("Validation conditions were not met.")
                    return render_template('users/guest/teacher_signup.html', form=create_teacher_sign_up_form, email_duplicates=email_duplicates, username_duplicates=username_duplicates, pwd_were_not_matched=pwd_were_not_matched) 
            else:
                return render_template('users/guest/teacher_signup.html', form=create_teacher_sign_up_form, invalidEmail=True) 
        else:
            return render_template('users/guest/teacher_signup.html', form=create_teacher_sign_up_form) 
    else:
        if "userSession" in session:
            return redirect(url_for("changeAccountType"))
        else:
            return redirect(url_for("home"))

@app.route('/sign_up_payment', methods=['GET', 'POST'])
def signUpPayment():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]
        if "teacher" in session:
            teacherID = session["teacher"]
            if teacherID == userSession:
                
                create_teacher_payment_form = Forms.CreateAddPaymentForm(request.form)
                if request.method == 'POST' and create_teacher_payment_form.validate():

                    # Retrieving data from shelve and to set the teacher's payment method info data
                    userDict = {}
                    db = shelve.open("user", "c")
                    try:
                        if 'Users' in db:
                            # there must be user data in the user shelve files as this is the 2nd part of the teacher signup process which would have created the teacher acc and store in the user shelve files previously
                            userDict = db['Users']
                        else:
                            db.close()
                            print("No user data in user shelve files.")
                            # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                            session.clear()
                            return redirect(url_for("home"))
                    except:
                        db.close()
                        print("Error in retrieving Users from user.db")
                        return redirect(url_for("home"))
                        

                    # retrieving the object from the shelve based on the user's email
                    teacherKey, userFound, accGoodStatus = get_key_and_validate(teacherID, userDict)
                    
                    if userFound and accGoodStatus:
                        # further checking to see if the user ID in the session is equal to the teacher ID session from the teacher sign up process

                        cardName = sanitise(create_teacher_payment_form.cardName.data)

                        cardNo = sanitise(create_teacher_payment_form.cardNo.data)
                        cardValid = validate_card_number(cardNo)
                        
                        cardCVV = sanitise(create_teacher_payment_form.cardCVV.data)
                        cardType = get_card_type(cardNo)
                        cardCVVValid = validate_cvv(cardCVV, cardType)

                        cardExpiry = create_teacher_payment_form.cardExpiry.data
                        cardExpiryValid = validate_expiry_date(cardExpiry)

                        if cardValid and cardExpiryValid and cardCVVValid:
                            if cardType != False: # checking if the card type is supported
                                cardExpiry = str(cardExpiry) # converting the card's expiry date datetime.date object to a string for string slicing
                                # string slicing for the cardExpiry as to make it in MM/DD format as compared to YYYY-MM-DD
                                cardYear = cardExpiry[:4] # to get the year from the date format "YYYY-MM-DD"
                                cardMonth = cardExpiry[5:7] # to get the month from the date format "YYYY-MM-DD"
                                cardExpiry = cardMonth + "/" + cardYear

                                # setting the teacher's payment method which in a way editing the teacher's object
                                teacherKey.set_card_name(cardName)
                                teacherKey.set_card_no(cardNo)
                                teacherKey.set_card_expiry(cardExpiry)
                                teacherKey.set_card_cvv(cardCVV)
                                teacherKey.set_card_type(cardType)
                                teacherKey.display_card_info()
                                db['Users'] = userDict
                                print("Payment added")

                                db.close()

                                session.pop("teacher", None) # deleting data from the session after registering the payment method
                                session["teacherPaymentAdded"] = True
                                return redirect(url_for("home"))
                            else:
                                return render_template('users/guest/teacher_signup_payment.html', form=create_teacher_payment_form, invalidCardType=True)
                        else:
                            return render_template('users/guest/teacher_signup_payment.html', form=create_teacher_payment_form, cardValid=cardValid, cardExpiryValid=cardExpiryValid, cardCVVValid=cardCVVValid)
                    else:
                        db.close()
                        print("User not found or is banned.")
                        # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                        session.clear()
                        return redirect(url_for("home"))
                else:
                    return render_template('users/guest/teacher_signup_payment.html', form=create_teacher_payment_form)
            else:
                # clear the teacher session if the logged in user somehow have a teacher session, it will then redirect them to the home page
                session.pop("teacher", None)
                return redirect(url_for("home"))
        else:
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))

"""End of Teacher's login/signup process by Jason"""

"""Admin login by Jason"""

@app.route('/admin_login', methods=['GET', 'POST'])
@limiter.limit("1/second") # to prevent attackers from trying to crack passwords by sending too many automated requests from their ip address
def adminLogin():
    if "adminSession" not in session and "userSession" not in session:
        create_login_form = Forms.CreateLoginForm(request.form)
        if request.method == "POST" and create_login_form.validate():
            emailInput = sanitise(create_login_form.email.data.lower())
            passwordInput = create_login_form.password.data
            try:
                adminDict = {}
                db = shelve.open("admin", "r")
                adminDict = db['Admins']
                db.close()
                print("File found.")
            except:
                print("File could not be found.")
                # since the shelve files could not be found, it will create a placeholder/empty shelve files so that user can submit the login form but will still be unable to login
                adminDict = {}
                db = shelve.open("admin", "c")
                db["Admins"] = adminDict
                db.close()

            # Declaring the 4 variables below to prevent UnboundLocalError
            email_found = False
            password_matched = False
            passwordShelveData = ""
            emailShelveData = ""

            # Checking the email input and see if it matches with any in the database
            for key in adminDict:
                emailShelveData = adminDict[key].get_email()
                if emailInput == emailShelveData:
                    email_key = adminDict[key]
                    email_found = True
                    print("Email in database:", emailShelveData)
                    print("Email Input:", emailInput)
                    break
                else:
                    print("User email not found.")
                    
            # if the email is found in the shelve database, it will then validate the password input and see if it matches with the one in the database
            if email_found:
                passwordShelveData = email_key.get_password()
                print("Password in database:", passwordShelveData)
                print("Password Input:", passwordInput)

                password_matched = password_manager().verify_password(passwordShelveData, passwordInput)

                if password_matched:
                    print("Correct password!")
                else:
                    print("Password incorrect.")
                    
            if email_found and password_matched:
                print("Admin account validated...")
                print("Email in database:", emailShelveData)
                print("Email Input:", emailInput)
                print("Password in database:", passwordShelveData)
                print("Password Input:", passwordInput)
                print("Account type:", email_key.get_acc_type())

                # checking if the admin account is active
                accActiveStatus = email_key.get_status()
                if accActiveStatus == "Active":
                    # setting the user session based on the user's user ID
                    userID = email_key.get_user_id()
                    session["adminSession"] = userID
                    print(userID)
                    print("Admin account active, login successful.")
                    return redirect(url_for("home"))
                else:
                    print("Admin account inactive.")
                    return render_template('users/guest/admin_login.html', form=create_login_form, notActive=True)
            else:
                print("Email in database:", emailShelveData)
                print("Email Input:", emailInput)
                print("Password in database:", passwordShelveData)
                print("Password Input:", passwordInput)
                print("Failed to login.")
                return render_template('users/guest/admin_login.html', form=create_login_form, failedAttempt=True)
        else:
            return render_template('users/guest/admin_login.html', form=create_login_form)
    else:
        return redirect(url_for("home"))

"""End of Admin login by Jason"""

"""User Management for Admins by Jason"""

@app.route("/user_management/<string:pageNum>/")
def userManagement(pageNum):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)
        
        if userFound and accActive:
            # add in your code here
            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                    print("Users found")
                else:
                    db["Users"] = userDict
                    print("No user data in user shelve files.")
            except:
                print("Error in retrieving Users from user.db")

            userList = []
            for users in userDict:
                user = userDict.get(users)
                userList.append(user)
            
            maxItemsPerPage = 10 # declare the number of items that can be seen per pages
            userListLen = len(userList) # get the length of the userList
            maxPages = math.ceil(userListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
            pageNum = int(pageNum)
            # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
            if pageNum < 0:
                return redirect("/user_management/0")
            elif userListLen > 0 and pageNum == 0:
                return redirect("/user_management/1")
            elif pageNum > maxPages:
                redirectRoute = "/user_management/" + str(maxPages)
                return redirect(redirectRoute)
            else:
                # pagination algorithm starts here
                pageNumForPagination = pageNum - 1 # minus for the paginate function
                paginatedUserList = paginate(userList, pageNumForPagination, maxItemsPerPage)
                paginationList = get_pagination_button_list(pageNum, maxPages)

                return render_template('users/admin/user_management.html', userList=paginatedUserList, count=userListLen, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""End of User Management for Admins by Jason"""

"""User Profile Settings by Jason"""

@app.route('/user_profile', methods=["GET","POST"])
def userProfile():
    if "userSession" in session and "adminSession" not in session:
        session.pop("teacher", None) # deleting data from the session if the user chooses to skip adding a payment method from the teacher signup process

        userSession = session["userSession"]

        # Retrieving data from shelve and to set the teacher's payment method info data
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                # there must be user data in the user shelve files as this is the 2nd part of the teacher signup process which would have created the teacher acc and store in the user shelve files previously
                userDict = db['Users']
            else:
                db.close()
                print("No user data in user shelve files.")
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            if request.method == "POST":
                if "profileImage" not in request.files:
                    print("No file sent.")
                    return redirect(url_for("userProfile"))

                file = request.files["profileImage"]
                filename = file.filename

                uploadedFileSize = request.cookies.get("filesize") # getting the uploaded file size value from the cookie made in the javascript when uploading the user profile image
                print("Uploaded file size:", uploadedFileSize, "bytes")

                withinFileLimit = allow_file_size(uploadedFileSize, app.config['MAX_PROFILE_IMAGE_FILESIZE'])

                if filename != "":
                    if file and allowed_image_file(filename) and withinFileLimit:
                        # will only accept .png, .jpg, .jpeg
                        print("File extension accepted and is within size limit.")

                        #  “never trust user input” principle, all submitted form data can be forged, and filenames can be dangerous.
                        # hence, secure_filename() is used because it will return a secure version of the filepath so that when constructing a file path to store the image, the server OS will be able to safely store the image 
                        filename = secure_filename(filename) 
                        
                        # constructing the file path so that the it will know where to store the image
                        filePath = construct_path(PROFILE_UPLOAD_PATH, filename)

                        # to construct a file path for userID.extension (e.g. 0.jpg) for renaming the file
                        extensionType = get_extension(filename)
                        userImageFileName = str(userSession) + extensionType
                        newFilePath = construct_path(PROFILE_UPLOAD_PATH, userImageFileName)

                        # constructing a file path to see if the user has already uploaded an image and if the file exists
                        userOldImageFilePath = construct_path(PROFILE_UPLOAD_PATH, userKey.get_profile_image())

                        # using Path from pathlib to check if the file path of userID.png (e.g. 0.png) already exist.
                        # if file already exist, it will remove and save the image and rename it to userID.png (e.g. 0.png) which in a way is overwriting the existing image
                        # else it will just save normally and rename it to userID.png (e.g. 0.png)
                        if Path(userOldImageFilePath).is_file():
                            print("Removing existing image.")
                            overwrite_file(file, userOldImageFilePath, filePath)
                            os.rename(filePath, newFilePath) # afterwards, it will rename the image that the user uploaded to userID.png
                            print("File renamed to", newFilePath, "and has been overwrited.")
                        else:
                            print("Saving image file.")
                            file.save(filePath)
                            os.rename(filePath, newFilePath) # rename the image that the user uploaded to userID.png
                            print("File renamed to", newFilePath, "and has been saved.")

                        # resizing the image to a 1:1 ratio that was recently uploaded and stored in the server directory
                        resize_image(newFilePath, (500, 500))

                        userKey.set_profile_image(userImageFileName)
                        db['Users'] = userDict
                        db.close()

                        session["imageChanged"] = True
                        return redirect(url_for("userProfile"))
                    else:
                        db.close()
                        print("Image extension not allowed or exceeded maximum image size of {} bytes" .format(app.config['MAX_PROFILE_IMAGE_FILESIZE']))
                        session["imageFailed"] = True
                        return redirect(url_for("userProfile"))
                else:
                    db.close()
                    print("No selected file/the user sent a empty file without a filename")
                    return redirect(url_for("userProfile"))
            else:
                db.close()
                userUsername = userKey.get_username()
                userEmail = userKey.get_email()
                userAccType = userKey.get_acc_type()

                userProfileImage = userKey.get_profile_image() # will return a filename, e.g. "0.png"
                userProfileImagePath = construct_path(PROFILE_UPLOAD_PATH, userProfileImage)

                # checking if the user have uploaded a profile image before and if the image file exists
                if userProfileImage != "" and Path(userProfileImagePath).is_file():
                    imagesrcPath = "/static/images/user/" + userProfileImage
                else:
                    imagesrcPath = "/static/images/user/default.png"

                # checking sessions if any of the user's acc info has changed
                if "username_changed" in session:
                    usernameChanged = True
                    session.pop("username_changed", None)
                    print("Username recently changed?:", usernameChanged)
                else:
                    usernameChanged = False
                    print("Username recently changed?:", usernameChanged)

                if "email_updated" in session:
                    emailChanged = True
                    session.pop("email_updated", None)
                    print("Email recently changed?:", emailChanged)
                else:
                    emailChanged = False
                    print("Email recently changed?:", emailChanged)

                if "password_changed" in session:
                    passwordChanged = True
                    session.pop("password_changed", None)
                    print("Password recently changed?:", passwordChanged)
                else:
                    passwordChanged = False
                    print("Password recently changed?:", passwordChanged)

                if "imageFailed" in session:
                    imageFailed = True
                    session.pop("imageFailed", None)
                    print("Fail to upload image because of wrong extension?:", imageFailed)
                else:
                    imageFailed = False
                    print("Fail to upload image because of wrong extension?:", imageFailed)

                if "imageChanged" in session:
                    imageChanged = True
                    session.pop("imageChanged", None)
                    print("Profile icon recently changed?:", imageChanged)
                else:
                    imageChanged = False
                    print("Profile icon recently changed?:", imageChanged)

                if "recentChangeAccType" in session:
                    recentChangeAccType = True
                    session.pop("recentChangeAccType", None)
                    print("Recently changed account type to teacher?:", recentChangeAccType)
                else:
                    recentChangeAccType = False
                    print("Recently changed account type to teacher?:", recentChangeAccType)
                
                return render_template('users/loggedin/user_profile.html', username=userUsername, email=userEmail, accType = userAccType, emailChanged=emailChanged, usernameChanged=usernameChanged, passwordChanged=passwordChanged, imageFailed=imageFailed, imageChanged=imageChanged, imagesrcPath=imagesrcPath, recentChangeAccType=recentChangeAccType)
        else:
            db.close()
            print("User not found or is banned.")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route("/change_username", methods=["GET","POST"])
def updateUsername():
    if "userSession" in session and "adminSession" not in session:
        create_update_username_form = Forms.CreateChangeUsername(request.form)
        if request.method == "POST" and create_update_username_form.validate():
            userSession = session["userSession"]
            
            # Retrieving data from shelve and to write the data into it later
            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("User data in shelve is empty.")
                    session.clear() 
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("home"))

            # retrieving the object from the shelve based on the user's user ID
            userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
            
            if userFound and accGoodStatus:
                updatedUsername = sanitise(create_update_username_form.updateUsername.data)
                currentUsername = userKey.get_username()
                    
                if updatedUsername != currentUsername:
                    # checking duplicates for username
                    for key in userDict:
                        print("retrieving")
                        usernameShelveData = userDict[key].get_username()
                        if updatedUsername == usernameShelveData:
                            print("Username in database:", usernameShelveData)
                            print("Username input:", updatedUsername)
                            print("Verdict: Username already taken.")
                            username_duplicates = True
                            break
                        else:
                            print("Username in database:", usernameShelveData)
                            print("Username input:", updatedUsername)
                            print("Verdict: Username is unique.")
                            username_duplicates = False

                    if username_duplicates == False:

                        # updating username of the user
                        userKey.set_username(updatedUsername)
                        db['Users'] = userDict
                        print("Username updated")

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of password
                        session["username_changed"] = True

                        db.close()
                        return redirect(url_for("userProfile"))
                    else:
                        return render_template('users/loggedin/change_username.html', form=create_update_username_form, username_duplicates=True)
                else:
                    print("Update username input same as user's current username")
                    return render_template('users/loggedin/change_username.html', form=create_update_username_form, sameUsername=True)
            else:
                print("User not found or is banned.")
                # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
        else:
            return render_template('users/loggedin/change_username.html', form=create_update_username_form)
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route("/change_email", methods=["GET","POST"])
def updateEmail():
    if "userSession" in session and "adminSession" not in session:
        create_update_email_form = Forms.CreateChangeEmail(request.form)
        if request.method == "POST" and create_update_email_form.validate():
            userSession = session["userSession"]

            # Retrieving data from shelve and to write the data into it later
            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("User data in shelve is empty.")
                    session.clear() 
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("home"))

            # retrieving the object based on the shelve files using the user's user ID
            userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
            
            if userFound and accGoodStatus:
                updatedEmail = sanitise(create_update_email_form.updateEmail.data.lower())
                currentEmail = userKey.get_email()
                    
                # Checking duplicates for email
                if updatedEmail != currentEmail:
                    for key in userDict:
                        print("retrieving")
                        emailShelveData = userDict[key].get_email()
                        if updatedEmail == emailShelveData:
                            print("Email in database:", emailShelveData)
                            print("Email input:", updatedEmail)
                            print("Verdict: User email already exists.")
                            email_duplicates = True
                            break
                        else:
                            print("Email in database:", emailShelveData)
                            print("Email input:", updatedEmail)
                            print("Verdict: User email is unique.")
                            email_duplicates = False

                    if email_duplicates == False:
                        # updating email of the user
                        userKey.set_email(updatedEmail)
                        db['Users'] = userDict
                        print("Email updated")
                        
                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of email
                        session["email_updated"] = True

                        db.close()
                        return redirect(url_for("userProfile"))
                    else:
                        db.close()
                        return render_template('users/loggedin/change_email.html', form=create_update_email_form, email_duplicates=True)
                else:
                    db.close()
                    print("User updated email input is the same as their current email")
                    return render_template('users/loggedin/change_email.html', form=create_update_email_form, sameEmail=True)
            else:
                print("User not found or is banned.")
                # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
        else:
            return render_template('users/loggedin/change_email.html', form=create_update_email_form)
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route("/change_password", methods=["GET","POST"])
def updatePassword():
    if "userSession" in session and "adminSession" not in session:
        create_update_password_form = Forms.CreateChangePasswordForm(request.form)
        if request.method == "POST" and create_update_password_form.validate():
            userSession = session["userSession"]

            # declaring password_not_matched, and errorMessage variable to prevent unboundLocalError
            password_not_matched = True
            password_verification = False

            # for jinja2
            errorMessage = False 

            # Retrieving data from shelve and to write the data into it later
            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("User data in shelve is empty.")
                    session.clear() 
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("home"))

            # retrieving the object based on the shelve files using the user's user ID
            userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
            
            if userFound and accGoodStatus:
                currentPassword = create_update_password_form.currentPassword.data
                updatedPassword = create_update_password_form.updatePassword.data
                confirmPassword = create_update_password_form.confirmPassword.data

                # Retrieving current password of the user
                currentStoredPassword = userKey.get_password()

                # validation starts
                print("Updated password input:", updatedPassword)
                print("Confirm password input", confirmPassword)
                if updatedPassword == confirmPassword:
                    password_not_matched = False
                    print("New and confirm password inputs matched")
                else:
                    print("New and confirm password inputs did not match")

                print("Current password:", currentStoredPassword)
                print("Current password input:", currentPassword)

                password_verification = password_manager().verify_password(currentStoredPassword, currentPassword)
                
                # printing message for debugging purposes
                if password_verification:
                    print("User identity verified")
                else:
                    print("Current password input hash did not match with the one in the shelve database")

                # if there any validation error, errorMessage will become True for jinja2 to render the error message
                if password_verification == False or password_not_matched:
                    errorMessage = True
                    db.close()
                    return render_template('users/loggedin/change_password.html', form=create_update_password_form, errorMessage=errorMessage)
                else:
                    # updating password of the user once validated
                    hashedPwd = password_manager().hash_password(updatedPassword)
                    userKey.set_password(hashedPwd)
                    db['Users'] = userDict
                    print("Password updated")
                    db.close()

                    # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of password
                    session["password_changed"] = True
                    return redirect(url_for("userProfile"))
            else:
                print("User not found is banned.")
                # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
        else:
            return render_template('users/loggedin/change_password.html', form=create_update_password_form)
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route('/change_account_type', methods=["GET","POST"])
def changeAccountType():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
        accType = userKey.get_acc_type()
        print("Account type:", accType)

        if userFound and accGoodStatus:
            if accType == "Student":
                if request.method == "POST":
                    # updating the user's account type to teacher if the user pressed on the "Become a teacher" button and confirmed his/her intention by clicking on confirm on the bootstrap 5 modal
                    userKey.set_acc_type("Teacher")
                    db["Users"] = userDict
                    db.close()
                    print("Account type updated to teacher.")
                    session["recentChangeAccType"] = True # making a session so that jinja2 can render a notification of the account type change
                    return redirect(url_for("userProfile"))
                else:    
                    db.close()
                    return render_template("users/student/change_account_type.html")
            else:
                db.close()
                print("User is not a student.")
                # if the user is not a student but visits this webpage, it will redirect the user to the user profile page
                return redirect(url_for("userProfile"))
        else:
            db.close()
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

"""End of User Profile Settings by Jason"""

"""User payment method settings by Jason"""

@app.route('/payment_method', methods=["GET","POST"])
def userPayment():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                session.clear() 
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
        
        if userFound and accGoodStatus:
            cardExist = bool(userKey.get_card_name())
            print("Card exist?:", cardExist)
            accType = userKey.get_acc_type()

            if cardExist == False:
                create_add_payment_form = Forms.CreateAddPaymentForm(request.form)
                if request.method == "POST" and create_add_payment_form.validate():
                    print("POST request sent and form entries validated")
                    cardName = sanitise(create_add_payment_form.cardName.data)

                    cardNo = sanitise(create_add_payment_form.cardNo.data)
                    cardValid = validate_card_number(cardNo)

                    cardCVV = sanitise(create_add_payment_form.cardCVV.data)
                    cardType = get_card_type(cardNo) # get type of the credit card for specific warning so that the user would know that only Mastercard and Visa cards are only accepted
                    cardCVVValid = validate_cvv(cardCVV, cardType)

                    cardExpiry = create_add_payment_form.cardExpiry.data
                    cardExpiryValid = validate_expiry_date(cardExpiry)

                    if cardValid and cardExpiryValid and cardCVVValid:
                        if cardType != False:
                            cardExpiry = str(cardExpiry) # converting the card's expiry date datetime.date object to a string for string slicing
                            # string slicing for the cardExpiry as to make it in MM/DD format as compared to YYYY-MM-DD
                            cardYear = cardExpiry[:4] # to get the year from the date format "YYYY-MM-DD"
                            cardMonth = cardExpiry[5:7] # to get the month from the date format "YYYY-MM-DD"
                            cardExpiry = cardMonth + "/" + cardYear

                            # setting the user's payment method
                            userKey.set_card_name(cardName)
                            userKey.set_card_no(cardNo)
                            userKey.set_card_expiry(cardExpiry)
                            userKey.set_card_cvv(cardCVV)
                            userKey.set_card_type(cardType)
                            userKey.display_card_info()
                            db['Users'] = userDict
                            print("Payment added")

                            # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of adding the payment method
                            session["payment_added"] = True

                            db.close()
                            return redirect(url_for("userPayment"))
                        else:
                            return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form, invalidCardType=True)
                    else:
                        return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form, cardValid=cardValid, cardExpiryValid=cardExpiryValid, cardCVVValid=cardCVVValid)
                else:
                    print("POST request sent but form not validated")
                    db.close()

                    # checking sessions if any of the user's payment method has been deleted
                    if "card_deleted" in session:
                        cardDeleted = True
                        session.pop("card_deleted", None)
                        print("Card recently added?:", cardDeleted)
                    else:
                        cardDeleted = False
                        print("Card recently added?:", cardDeleted)

                    return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form, cardDeleted=cardDeleted, accType=accType)
            else:
                db.close()
                cardName = userKey.get_card_name()
                cardNo = str(userKey.get_card_no())
                print("Original card number:", cardNo)
                cardNo = cardNo[-5:-1] # string slicing to get the last 4 digits of the credit card number
                print("Sliced card number:", cardNo)
                cardExpiry = userKey.get_card_expiry()
                print("Card expiry date:", cardExpiry)
                cardType = userKey.get_card_type()

                # checking sessions if any of the user's payment method details has changed
                if "card_updated" in session:
                    cardUpdated = True
                    session.pop("card_updated", None)
                    print("Card recently updated?:", cardUpdated)
                else:
                    cardUpdated = False
                    print("Card recently updated?:", cardUpdated)
                
                if "payment_added" in session:
                    cardAdded = True
                    session.pop("payment_added", None)
                    print("Card recently added?:", cardAdded)
                else:
                    cardAdded = False
                    print("Card recently added?:", cardAdded)

                return render_template('users/loggedin/user_existing_payment.html', cardName=cardName, cardNo=cardNo, cardExpiry=cardExpiry, cardType=cardType, cardUpdated=cardUpdated, cardAdded=cardAdded, accType=accType)
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route('/edit_payment', methods=["GET","POST"])
def userEditPayment():
    if "userSession" in session and "adminSession" not in session:
        # checking if the user has a credit card in the shelve database to prevent directory traversal which may break the web app

        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() 
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
        
        if userFound and accGoodStatus:
            accType = userKey.get_acc_type()

            cardExist = bool(userKey.get_card_name())
            print("Card exist?:", cardExist)
            cardName = userKey.get_card_name()

            cardNo = str(userKey.get_card_no())
            print("Original card number:", cardNo)
            cardNo = cardNo[-5:-1] # string slicing to get the last 4 digits of the credit card number
            print("Sliced card number:", cardNo)

            cardType = userKey.get_card_type().capitalize()
            if cardExist:
                create_edit_payment_form = Forms.CreateEditPaymentForm(request.form)
                if request.method == "POST" and create_edit_payment_form.validate():
                    cardCVV = sanitise(create_edit_payment_form.cardCVV.data)
                    cardCVVValid = validate_cvv(cardCVV, cardType.lower())

                    cardExpiry = create_edit_payment_form.cardExpiry.data
                    cardExpiryValid = validate_expiry_date(cardExpiry)
                    if cardCVVValid and cardExpiryValid:

                        cardExpiry = str(cardExpiry) # converting the card's expiry date datetime.date object to a string for string slicing
                        # string slicing for the cardExpiry as to make it in MM/DD format as compared to YYYY-MM-DD
                        cardYear = cardExpiry[:4] # to get the year from the date format "YYYY-MM-DD"
                        cardMonth = cardExpiry[5:7] # to get the month from the date format "YYYY-MM-DD"
                        cardExpiry = cardMonth + "/" + cardYear

                        # changing the user's payment info
                        userKey.set_card_cvv(cardCVV)
                        userKey.set_card_expiry(cardExpiry)
                        db['Users'] = userDict
                        print("Changed CVV:", cardCVV)
                        print("Payment edited")
                        db.close()

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of the card details
                        session["card_updated"] = True

                        return redirect(url_for("userPayment"))
                    else:
                        return render_template('users/loggedin/user_edit_payment.html', form=create_edit_payment_form, cardName=cardName, cardNo=cardNo, cardType=cardType, accType=accType, cardCVVValid=cardCVVValid, cardExpiryValid=cardExpiryValid)
                else:
                    db.close()
                    return render_template('users/loggedin/user_edit_payment.html', form=create_edit_payment_form, cardName=cardName, cardNo=cardNo, cardType=cardType, accType=accType)
            else:
                db.close()
                return redirect(url_for("userProfile"))
        else:
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route('/delete_card', methods=['POST'])
def deleteCard():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
        
        if userFound and accGoodStatus:
            # checking if the user has a credit card in the shelve database to prevent directory traversal if the logged in attackers send a POST request to the web app server
            cardExist = bool(userKey.get_card_name())
            print("Card exist?:", cardExist)

            if cardExist:
                # deleting user's payment info, specifically changing their payment info to empty strings
                userKey.set_card_name("")
                userKey.set_card_no("")
                userKey.set_card_expiry("")
                userKey.set_card_cvv("")
                userKey.set_card_type("")
                userKey.display_card_info()

                db['Users'] = userDict
                print("Payment added")
                db.close()
                
                # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of the card details
                session["card_deleted"] = True
                return redirect(url_for("userPayment"))
                
            else:
                db.close()
                return redirect(url_for("userProfile"))
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

"""End of User payment method settings by Jason"""

"""Search Function by Royston"""

@app.route("/search")
def search():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
        
        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            
            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

""""End of Search Function by Royston"""

"""Purchase History by Royston"""

@app.route("/purchasehistory")
def purchaseHistory():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
        
        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            purchaseID = userKey.get_purchaseID()
            print("PurchaseID exists?: ", purchaseID)

            userDict = {}
            db = shelve.open("user", "r")
            #try:
                #if purchaseID:

                #else:

            #except:
            #    db.close()
            #    print("Error in displaying Purchase History")
            #    return redirect(url_for("home"))

            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Purchase History by Royston"""

"""Purchase Review by Royston"""

@app.route("/purchasereview")
def purchaseReview():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
        
        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            
            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Purchase Review by Royston"""

"""Purchase View by Royston"""

@app.route("/purchaseview")
def purchaseView():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
        
        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            
            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Purchase View by Royston"""

"""Teacher Cashout System by Royston"""

@app.route("/teacher_cashout")
def teacherCashOut():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
        
        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            
            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Teacher Cashout System by Royston"""


# 7 template app.route("") for you guys :prayge:
# Please REMEMBER to CHANGE the def function() function name to something relevant and unique (will have runtime error if the function name is not unique)
'''
# Template for your app.route("") if
  - User session validity check needed (Logged in?)
  - User banned?
  
  - Using user shelve files --> shelve.open("user", "C") ONLY
  - Webpage will not have admin view
  - Use case: User features such as change_password.html, etc.
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
def function():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus = get_key_and_validate(userSession, userDict)
        
        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            
            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - User session validity check needed (Logged in?)
  - User banned?
  
  - Using CUSTOM shelve files --> shelve.open("<name of shelve here>", "C") ONLY
  - If your feature might need to retrieve the user's account details
  - Webpage will not have admin view
  - Use case: User features/pages that deals with other shelve files
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
def function():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        userFound, accGoodStatus = validate_session_open_file(userSession) 
        # if there's a need to retrieve the userKey for reading the user's account details, use the function below instead of the one above
        # userKey, userFound, accGoodStatus = validate_session_get_userKey_open_file(userSession)
        
        if userFound and accGoodStatus:
            # add in your own code here for your C,R,U,D operation and remember to close() it after manipulating the data

            return render_template('users/loggedin/page.html')
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if [Note that this is similar to one above]
  - User session validity check needed (Logged in?)
  - User banned?
  
  - NOT using shelve but there's a need to retrieve user account data
  - Reading info from user account data
  
  - Webpage will not have admin view
  - Use case: User pages (user_profile.html, etc)
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route('', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
def insertName():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus = validate_session_get_userKey_open_file(userSession)

        if userFound and accGoodStatus:
            # add in your code below

            return render_template('users/loggedin/page.html')
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - User session validity check needed (Logged in?)
  - User banned?
  - Is user admin?
  
  - NOT using shelve
  
  - Webpage will have admin and user view
  e.g. General pages (about_us.html, etc) that check whether user/admin is logged in.
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route('', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
def insertName():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)
        
        if userFound and accActive:
            return render_template('users/admin/page.html')
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the login page or this function's html page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
            # render_template("users/guest/page.html)
    else:
        if "userSession" in session:
            userSession = session["userSession"]

            userFound, accGoodStatus = validate_session_open_file(userSession)

            if userFound and accGoodStatus:
                # add in your code here (if any)
                
                return render_template('users/loggedin/page.html')
            else:
                print("User not found or is banned.")
                # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
                # return redirect(url_for("this function name here")) # determine if it make sense to redirect the user to the home page or to this page (if you determine that it should redirect to this function again, make sure to render a guest version of the page in the else statement below)
        else:
            # determine if it make sense to redirect the user to the home page or the login page or this function's html page
            return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))
            # render_template("users/guest/page.html)

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - Admin session validity check needed (Logged in?)
  - Admin account active?
  
  - Using CUSTOM shelve files --> shelve.open("<name of shelve here>", "C") ONLY
  
  - Webpage will not have user view
  e.g. Admin pages
  - Use case: Admim pages
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
def function():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)
        # if there's a need to retrieve admin account details, use the function below instead of the one above
        # userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)
        
        if userFound and accActive:
            # add in your code here
            xDict = {}
            db = shelve.open("", "c") # change the flag accordingly
            # implement your try and except here to handle the shelve files

            return render_template('users/admin/page.html')
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - Admin session validity check needed (Logged in?)
  - Admin account active?
  
  - Using admin shelve files --> shelve.open("admin", "C") ONLY
  
  - Webpage will not have user view
  e.g. Admin pages
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
def function():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)

        db = shelve.open("admin", "c")
        try:
            if 'Admins' in db:
                adminDict = db['Admins']
            else:
                db.close()
                print("Admin account data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the admin shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Admins from admin.db")
            return redirect(url_for("home"))

        userKey, userFound, accActive = admin_get_key_and_validate(adminSession, adminDict)
        
        if userFound and accActive:
            # add in your code here

            db.close() # remember to close the admin shelve file!
            return render_template('users/admin/page.html')
        else:
            db.close()
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - Admin session validity check needed (Logged in?)
  - Admin account active?
  
  - NOT using shelve
  - Reading info from admin account data
  
  - Webpage will not have user view
  - Use case: Admin pages
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
def function():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)

        userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)
        
        if userFound and accActive:
            # add in your code here

            db.close() # remember to close the admin shelve file!
            return render_template('users/admin/page.html')
        else:
            db.close()
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

"""Custom Error Pages"""

# Unauthorised
@app.errorhandler(401)
def error401(e):
    return render_template("errors/401.html"), 401

# Forbidden
@app.errorhandler(403)
def error403(e):
    return render_template("errors/403.html"), 403

# Not Found
@app.errorhandler(404)
def error404(e):
    return render_template("errors/404.html"), 404

# Payload Too Large
@app.errorhandler(413)
def error413(e):
    return render_template("errors/413.html"), 413

# Too Many Requests
@app.errorhandler(429)
def error429(e):
    return render_template("errors/429.html"), 429

# Internal Server Error
@app.errorhandler(500)
def error500(e):
    return render_template("errors/500.html"), 500

# Not Implemented
@app.errorhandler(501)
def error501(e):
    return render_template("errors/501.html"), 501

# Bad Gateway
@app.errorhandler(502)
def error502(e):
    return render_template("errors/502.html"), 502

# Service Temporarily Unavailable
@app.errorhandler(503)
def error503(e):
    return render_template("errors/503.html"), 503

"""End of Custom Error Pages"""

if __name__ == '__main__':
    app.run(debug=True) # debug=True for development purposes

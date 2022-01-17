from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename # this is for sanitising a filename for security reasons, remove if not needed (E.g. if you're changing the filename to use a id such as 0a18dd92.png before storing the file, it is not needed)
import shelve, os, math, paypalrestsdk, difflib
import Student, Teacher, Forms
from Payment import Payment
from Security import hash_password, verify_password, sanitise, validate_email
from CardValidation import validate_card_number, get_credit_card_type, validate_cvv, validate_expiry_date, cardExpiryStringFormatter, validate_formatted_expiry_date
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
from flask_mail import Mail
from IntegratedFunctions import *
import vimeo
from datetime import date, timedelta

"""Rubrics (for Excellent)"""
"""Week 13 Progress Review (15%)
Flask Application (10%)
Completed at least 4 functions (C, R, U and/or D) with excellent use of
UI components, consistent layout and compellingly consideration to address
the user's needs.

OOP Concepts (5%)
Implemented 3 OOP concepts appropriately and correctly with strong
justification in supporting the functionality of the flask application.
 - Classes, Objects and Methods
 - Inheritance & Polymorphism
 - Persistence & Exceptions
"""

"""Web app configurations"""

# general Flask configurations
app = Flask(__name__)
app.config["SECRET_KEY"] = "a secret key" # for demonstration purposes, if deployed, change it to something more secure

# Maximum file size for uploading anything to the web app's server
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024 # 15MiB
app.config['MAX_PROFILE_IMAGE_FILESIZE'] = 2 * 1024 * 1024 # 2MiB

# configuration for email
# Make sure to enable access for less secure apps
app.config["MAIL_SERVER"] = "smtp.googlemail.com" # using gmail
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "CourseFinity123@gmail.com" # using gmail
app.config["MAIL_PASSWORD"] = os.environ.get("EMAIL_PASS") # setting password but hiding the password for the CourseFinity123@gmail.com password using system environment variables
mail = Mail(app)

# paypal sdk configuration
paypalrestsdk.configure({
  "mode": "sandbox",
  "client_id": "AUTh83JMz8mLNGNzpzJRJSbSLUAEp7oe1ieGGqYCmVXpq427DeSVElkHnc0tt70b8gHlWg4yETnLLu1s",
  "client_secret": os.environ.get("PAYPAL_SECRET") })

# Flask limiter configuration
limiter = Limiter(app, key_func=get_remote_address)

# vimeo api configurations
client = vimeo.VimeoClient(
    # client token, key, and secret all generated from vimeo
    token = os.environ.get("VIMEO_TOKEN"),
    key = '8ae482ba677dcdad1866b53280d00ea2a8e8ce05',
    secret = os.environ.get("VIMEO_SECRET")
)

""" # Uploading of videos
file_name = '{path_to_a_video_on_the_file_system}'
uri = client.upload(file_name, data={
    'name': 'Untitled',
    'description': 'The description goes here.'
})

print ('Your video URI is: %s' % (uri))

# Error handling while video transcodes
response = client.get(uri + '?fields=transcode.status').json()
if response['transcode']['status'] == 'complete':
    print ('Your video finished transcoding.')
elif response['transcode']['status'] == 'in_progress':
    print ('Your video is still transcoding.')
else:
    print ('Your video encountered an error during transcoding.')

response = client.get(uri + '?fields=link').json()
print("Your video link is: " + response['link']) """

"""End of Web app configurations"""

"""Home page by Jason"""

@app.route('/')
@limiter.limit("30/second") # to prevent ddos attacks
def home():
    courseDict = {}
    try:
        db = shelve.open("user", "r")
        courseDict = db['Courses']
        db.close()
        print("File found.")
    except:
        print("File could not be found.")
        # since the shelve files could not be found, it will create a placeholder/empty shelve files so that user can submit the login form but will still be unable to login
        db = shelve.open("user", "c")
        db["Courses"] = courseDict
        db.close()

    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)

        if userFound and accGoodStatus:
            imagesrcPath = retrieve_user_profile_pic(userKey)
            if accType != "Admin":
                # checking if the teacher recently added their payment method when signing up
                if "teacherPaymentAdded" in session:
                    teacherPaymentAdded = True
                    session.pop("teacherPaymentAdded", None)
                else:
                    teacherPaymentAdded = False

                # checking if the user recently completed a purchase
                if "paymentComplete" in session:
                    paymentComplete = True
                    session.pop("paymentComplete", None)
                else:
                    paymentComplete = False

                # for recommendation algorithm
                userTagDict = userKey.get_tags_viewed()
                highestWatchedByTag = max(userTagDict, key=userTagDict.get)
                userTagDict.pop(highestWatchedByTag)
                secondHighestWatchedByTag = max(userTagDict, key=userTagDict.get)
                userPurchasedCourses = userKey.get_purchases()

                recommendedCourseListByHighestTag = []
                recommendedCourseListBySecondHighestTag = []
                for key in courseDict:
                    courseObject = courseDict[key]
                    courseTag = courseObject.get_tags()
                    if courseTag == highestWatchedByTag:
                        if courseObject.get_courseID() not in userPurchasedCourses:
                            recommendedCourseListByHighestTag.append(courseObject)
                    elif courseTag == secondHighestWatchedByTag:
                        if courseObject.get_courseID() not in userPurchasedCourses:
                            recommendedCourseListBySecondHighestTag.append(courseObject)
                try: 
                    randomisedRecommendedCourseList = random.sample(recommendedCourseListByHighestTag, 2)
                    randomisedRecommendedCourseList.append(random.choice(recommendedCourseListBySecondHighestTag))
                except:
                    randomisedRecommendedCourseList = []

                # for trending algorithm
                
                

                return render_template('users/general/home.html', accType=accType, imagesrcPath=imagesrcPath, teacherPaymentAdded=teacherPaymentAdded, paymentComplete=paymentComplete)
            else:
                return render_template('users/general/home.html', accType=accType, imagesrcPath=imagesrcPath)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/home.html", accType="Guest")
    else:
        return render_template("users/general/home.html", accType="Guest")

"""End of Home pages by Jason"""

"""User login and logout by Jason"""

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10/second") # to prevent attackers from trying to crack passwords or doing enumeration attacks by sending too many automated requests from their ip address
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
            userDict = {}
            try:
                db = shelve.open("user", "r")
                userDict = db['Users']
                db.close()
                print("File found.")
            except:
                print("File could not be found.")
                # since the shelve files could not be found, it will create a placeholder/empty shelve files so that user can submit the login form but will still be unable to login
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

                password_matched = verify_password(passwordShelveData, passwordInput)

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
            # for notifying if they have verified their email from the link in their email
            if "emailVerified" in session:
                emailVerified = True
                session.pop("emailVerified", None)
            else:
                emailVerified = False
            # for notifying if the email verification link has expired/is invalid
            if "emailTokenInvalid" in session:
                emailTokenInvalid = True
                session.pop("emailTokenInvalid", None)
            else:
                emailTokenInvalid = False
            # for notifying if they have already verified their email (traversal attack)
            if "emailFailed" in session:
                emailAlreadyVerified = True
                session.pop("emailFailed", None)
            else:
                emailAlreadyVerified = False

            return render_template('users/guest/login.html', form=create_login_form, passwordUpdated=passwordUpdated, emailVerified=emailVerified, emailTokenInvalid=emailTokenInvalid, emailAlreadyVerified=emailAlreadyVerified)
    else:
        return redirect(url_for("home"))

@app.route('/logout')
@limiter.limit("30/second") # to prevent ddos attacks
def logout():
    if "userSession" in session or "adminSession" in session:
        session.clear()
    else:
        return redirect(url_for("home"))

    # sending a session data so that when it redirects the user to the homepage, jinja2 will render out a logout alert
    session["recentlyLoggedOut"] = True
    return redirect(url_for("home"))

"""End of User login and logout by Jason"""

"""Reset Password by Jason"""

@app.route('/reset_password', methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
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
            userDict = {}
            try:
                db = shelve.open("user", "r")
                userDict = db['Users']
                db.close()
                print("File found.")
                fileFound = True
            except:
                print("File could not be found.")
                fileFound = False
                # since the shelve files could not be found, it will create a placeholder/empty shelve files so that user can submit the login form but will still be unable to login
                db = shelve.open("user", "c")
                db["Users"] = userDict
                db.close()

            if fileFound:
                # Declaring the 2 variables below to prevent UnboundLocalError
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
                        return render_template('users/guest/request_password_reset.html', form=create_request_form, emailSent=True, emailInput=emailInput)
                    else:
                        # email found in database but the user is banned.
                        # However, it will still send an "email sent" alert to throw off enumeration attacks on banned accounts
                        print("User account banned, email not sent.")
                        return render_template('users/guest/request_password_reset.html', form=create_request_form, emailSent=True, emailInput=emailInput)
                else:
                    # email not found in database, but will send an "email sent" alert to throw off enumeration attacks
                    print("Email in database:", emailShelveData)
                    print("Email Input:", emailInput)
                    return render_template('users/guest/request_password_reset.html', form=create_request_form, emailSent=True, emailInput=emailInput)
            else:
                # email not found in database, but will send an "email sent" alert to throw off enumeration attacks
                print("No user account records found.")
                print("Email Input:", emailInput)
                return render_template('users/guest/request_password_reset.html', form=create_request_form, emailSent=True, emailInput=emailInput)
        else:
            return render_template('users/guest/request_password_reset.html', form=create_request_form, invalidToken=invalidToken)
    else:
        return redirect(url_for("home"))

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
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
                    db = shelve.open("user", "c")
                    try:
                        if 'Users' in db:
                            userDict = db['Users']
                        else:
                            db.close()
                            print("No user data in user shelve files.")
                            # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the user to the homepage
                            return redirect(url_for("home"))
                    except:
                        db.close()
                        print("Error in retrieving Users from user.db")
                        return redirect(url_for("home"))

                    userKey = userDict.get(validateToken)
                    # checking if the user is banned
                    accGoodStatus = userKey.get_status()
                    if accGoodStatus == "Good":
                        hashedPassword = hash_password(password)
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
        return redirect(url_for("userProfile"))

"""End of Reset Password by Jason"""

"""Student signup process by Jason"""

@app.route('/signup', methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
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
                    hashedPwd = hash_password(passwordInput)
                    print("Hashed password:", hashedPwd)

                    # setting user ID for the user
                    userID = generate_ID(userDict)
                    print("User ID setted: ", userID)

                    user = Student.Student(userID, usernameInput, emailInput, hashedPwd)

                    userDict[userID] = user
                    db["Users"] = userDict

                    db.close()
                    print("User added.")
                    send_verify_email(emailInput, userID)
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

"""Email verification by Jason"""

@app.route("/generate_verify_email_token")
@limiter.limit("30/second") # to prevent ddos attacks
def verifyEmail():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)
        email = userKey.get_email()
        userID = userKey.get_user_id()
        if userFound and accGoodStatus:
            emailVerified = userKey.get_email_verification()
            if emailVerified == "Not Verified":
                session["emailVerifySent"] = True
                send_another_verify_email(email, userID)
            else:
                session["emailFailed"] = False
                print("User's email already verified.")
            return redirect(url_for("userProfile"))
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the login page
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route("/verify_email/<token>")
@limiter.limit("30/second") # to prevent ddos attacks
def verifyEmailToken(token):
    if "adminSession" not in session:
        validateToken = verify_email_token(token)
        if validateToken != None:

            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("home"))

            userKey = userDict.get(validateToken)
            # checking if the user is banned
            accGoodStatus = userKey.get_status()
            if accGoodStatus == "Good":
                emailVerification = userKey.get_email_verification()
                if emailVerification == "Not Verified":
                    userKey.set_email_verification("Verified")
                    db["Users"] = userDict
                    db.close()
                    session["emailVerified"] = True
                    if "userSession" in session:
                        return redirect(url_for("userProfile"))
                    else:
                        return redirect(url_for("userLogin"))
                else:
                    db.close()
                    session["emailFailed"] = True
                    if "userSession" in session:
                        return redirect(url_for("userProfile"))
                    else:
                        print("Email already verified")
                        return redirect(url_for("userLogin"))
            else:
                db.close()
                print("User account banned.")
                return redirect(url_for("home"))
        else:
            session["emailTokenInvalid"] = True
            print("Invalid/Expired Token.")
            if "userSession" in session:
                return redirect(url_for("userProfile"))
            else:
                return redirect(url_for("userLogin"))
    else:
        print("Admin is logged in.")
        return redirect(url_for("home"))

"""End of Email verification by Jason"""

"""Teacher's signup process by Jason"""

@app.route('/teacher_signup', methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
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
                    hashedPwd = hash_password(passwordInput)
                    print("Hashed password:", hashedPwd)

                    # setting user ID for the teacher
                    userID = generate_ID(userDict)
                    print("User ID setted: ", userID)

                    user = Teacher.Teacher(userID, usernameInput, emailInput, hashedPwd)
                    user.set_teacher_join_date(date.today())

                    userDict[userID] = user
                    db["Users"] = userDict

                    session["teacher"] = userID # to send the user ID under the teacher session for user verification in the sign up payment process

                    print(userDict)
                    print("Teacher added.")

                    db.close()
                    send_verify_email(emailInput, userID)
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
@limiter.limit("30/second") # to prevent ddos attacks
def signUpPayment():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]
        if "teacher" in session:
            teacherID = session["teacher"]
            if teacherID == userSession:
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
                teacherKey, userFound, accGoodStatus, accType = get_key_and_validate(teacherID, userDict)

                create_teacher_payment_form = Forms.CreateAddPaymentForm(request.form)
                if request.method == 'POST' and create_teacher_payment_form.validate():
                    if userFound and accGoodStatus:
                        # further checking to see if the user ID in the session is equal to the teacher ID session from the teacher sign up process

                        cardName = sanitise(create_teacher_payment_form.cardName.data)

                        cardNo = sanitise(create_teacher_payment_form.cardNo.data)
                        cardValid = validate_card_number(cardNo)

                        cardType = get_credit_card_type(cardNo, cardValid)

                        cardExpiry = sanitise(create_teacher_payment_form.cardExpiry.data)
                        cardExpiryValid = validate_expiry_date(cardExpiry)

                        if cardValid and cardExpiryValid:
                            if cardType != False: # checking if the card type is supported
                                # setting the teacher's payment method which in a way editing the teacher's object
                                teacherKey.set_card_name(cardName)
                                teacherKey.set_card_no(cardNo)
                                cardExpiry = cardExpiryStringFormatter(cardExpiry)
                                teacherKey.set_card_expiry(cardExpiry)
                                teacherKey.set_card_type(cardType)
                                teacherKey.display_card_info()
                                db['Users'] = userDict
                                print("Payment added")

                                db.close()

                                session.pop("teacher", None) # deleting data from the session after registering the payment method
                                session["teacherPaymentAdded"] = True
                                return redirect(url_for("home"))
                            else:
                                return render_template('users/guest/teacher_signup_payment.html', form=create_teacher_payment_form, invalidCardType=True, accType=accType)
                        else:
                            db.close()
                            return render_template('users/guest/teacher_signup_payment.html', form=create_teacher_payment_form, cardValid=cardValid, cardExpiryValid=cardExpiryValid, accType=accType)
                    else:
                        db.close()
                        print("User not found or is banned.")
                        # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                        session.clear()
                        return redirect(url_for("home"))
                else:
                    db.close()
                    return render_template('users/guest/teacher_signup_payment.html', form=create_teacher_payment_form, accType=accType)
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
@limiter.limit("5/second") # to prevent attackers from trying to crack passwords or doing enumeration attacks by sending too many automated requests from their ip address
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

                password_matched = verify_password(passwordShelveData, passwordInput)

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

"""Admin profile settings by Jason"""

@app.route('/admin_profile', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def adminProfile():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)

        userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)

        if userFound and accActive:
            username = userKey.get_username()
            email = userKey.get_email()
            admin_id = userKey.get_user_id()

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

            return render_template('users/admin/admin_profile.html', username=username, email=email, usernameChanged=usernameChanged, emailChanged=emailChanged, passwordChanged=passwordChanged, admin_id=admin_id)
        else:

            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/admin_change_username", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def adminChangeUsername():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        create_update_username_form = Forms.CreateChangeUsername(request.form)
        if request.method == "POST" and create_update_username_form.validate():
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
                updatedUsername = sanitise(create_update_username_form.updateUsername.data)
                currentUsername = userKey.get_username()

                if updatedUsername != currentUsername:
                    # checking duplicates for username
                    for key in adminDict:
                        print("retrieving")
                        usernameShelveData = adminDict[key].get_username()
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
                        db['Admins'] = adminDict
                        print("Username updated")

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of password
                        session["username_changed"] = True

                        db.close()
                        return redirect(url_for("adminProfile"))
                    else:
                        return render_template('users/admin/change_username.html', form=create_update_username_form, username_duplicates=True)
                else:
                    print("Update username input same as user's current username")
                    return render_template('users/admin/change_username.html', form=create_update_username_form, sameUsername=True)
            else:
                db.close()
                print("Admin account is not found or is not active.")
                # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
                session.clear()
                return redirect(url_for("adminLogin"))
        else:
            return render_template('users/admin/change_username.html', form=create_update_username_form)

    else:
        return redirect(url_for("home"))

@app.route("/admin_change_email", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def adminChangeEmail():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        create_update_email_form = Forms.CreateChangeEmail(request.form)
        if request.method == "POST" and create_update_email_form.validate():
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
                updatedEmail = sanitise(create_update_email_form.updateEmail.data.lower())
                currentEmail = userKey.get_email()

                # Checking duplicates for email
                if updatedEmail != currentEmail:
                    for key in adminDict:
                        print("retrieving")
                        emailShelveData = adminDict[key].get_email()
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
                        # updating email of the admin
                        userKey.set_email(updatedEmail)
                        db['Admins'] = adminDict
                        print("Email updated")

                        # sending a session data so that when it redirects the admin to the admin profile page, jinja2 will render out an alert of the change of email
                        session["email_updated"] = True

                        db.close()
                        return redirect(url_for("adminProfile"))
                    else:
                        db.close()
                        return render_template('users/admin/change_email.html', form=create_update_email_form, email_duplicates=True)
                else:
                    db.close()
                    print("User updated email input is the same as their current email")
                    return render_template('users/admin/change_email.html', form=create_update_email_form, sameEmail=True)
            else:
                db.close()
                print("Admin account is not found or is not active.")
                # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
                session.clear()
                return redirect(url_for("adminLogin"))
        else:
            return render_template('users/admin/change_email.html', form=create_update_email_form)
    else:
        return redirect(url_for("home"))

@app.route("/admin_change_password", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def adminChangePassword():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        create_update_password_form = Forms.CreateChangePasswordForm(request.form)
        if request.method == "POST" and create_update_password_form.validate():

            # declaring passwordNotMatched, passwordVerification, and errorMessage variable to initialise and prevent unboundLocalError
            passwordNotMatched = True
            passwordVerification = False

            # for jinja2
            errorMessage = False

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
                currentPassword = create_update_password_form.currentPassword.data
                updatedPassword = create_update_password_form.updatePassword.data
                confirmPassword = create_update_password_form.confirmPassword.data

                # Retrieving current password of the user
                currentStoredPassword = userKey.get_password()

                # validation starts
                print("Updated password input:", updatedPassword)
                print("Confirm password input", confirmPassword)
                if updatedPassword == confirmPassword:
                    passwordNotMatched = False
                    print("New and confirm password inputs matched")
                else:
                    print("New and confirm password inputs did not match")

                print("Current password:", currentStoredPassword)
                print("Current password input:", currentPassword)

                passwordVerification = verify_password(currentStoredPassword, currentPassword)
                oldPassword = verify_password(currentStoredPassword, updatedPassword)

                # printing message for debugging purposes
                if passwordVerification:
                    print("User identity verified")
                else:
                    print("Current password input hash did not match with the one in the shelve database")

                # if there any validation error, errorMessage will become True for jinja2 to render the error message
                if passwordVerification == False or passwordNotMatched:
                    db.close()
                    errorMessage = True
                    return render_template('users/admin/change_password.html', form=create_update_password_form, errorMessage=errorMessage)
                else:
                    if oldPassword:
                        db.close()
                        print("User cannot change password to their current password!")
                        return render_template('users/admin/change_password.html', form=create_update_password_form, samePassword=True)
                    else:
                        # updating password of the user once validated
                        hashedPwd = hash_password(updatedPassword)
                        userKey.set_password(hashedPwd)
                        db['Admins'] = adminDict
                        print("Password updated")
                        db.close()

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of password
                        session["password_changed"] = True
                        return redirect(url_for("adminProfile"))
            else:
                db.close()
                print("Admin account is not found or is not active.")
                # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
                session.clear()
                return redirect(url_for("adminLogin"))

        else:
            return render_template('users/admin/change_password.html', form=create_update_password_form)
    else:
        return redirect(url_for("home"))

"""Admin profile settings by Jason"""

"""User Management for Admins by Jason"""

@app.route("/user_management/page/<int:pageNum>", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def userManagement(pageNum):
    if "adminSession" in session:
        adminSession = session["adminSession"]

        # removing session created when searching for users
        if "searchedPageRoute" in session:
            session.pop("searchedPageRoute", None)

        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)
        if userFound and accActive:
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

            # for resetting the user's password and updating the user's email for account recovery
            admin_reset_password_form = Forms.AdminResetPasswordForm(request.form)
            if request.method == "POST" and admin_reset_password_form.validate():
                password = generate_password()
                email = sanitise(admin_reset_password_form.email.data)
                validEmail = validate_email(email)

                # for redirecting the admin to the user management page that he/she was in
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

                if validEmail:
                    userID = int(request.form["userID"])
                    userKey = userDict.get(userID)
                    oldEmail = userKey.get_email()
                    duplicateEmail = check_duplicates(email, userDict, "email")
                    if oldEmail != email:
                        if duplicateEmail == False:
                            if userKey != None:
                                # changing the password of the user
                                hashedPwd = hash_password(password)
                                userKey.set_password(hashedPwd)
                                userKey.set_email(email)
                                userKey.set_email_verification("Not Verified")
                                db["Users"] = userDict
                                db.close()
                                send_admin_reset_email(email, password) # sending an email to the user to notify them of the change
                                print("User account recovered successfully and email sent.")
                                return redirect(redirectURL)
                            else:
                                db.close()
                                print("Error in retrieving user object.")
                                return redirect(redirectURL)
                        else:
                            db.close()
                            print("Inputted new user's email is not unique.")
                            session["duplicateEmail"] = True
                            return redirect(redirectURL)
                    else:
                        db.close()
                        print("User's new email inputted is the same as the old email.")
                        session["sameEmail"] = True
                        return redirect(redirectURL)
                else:
                    db.close()
                    print("Inputted new user's email is invalid.")
                    session["invalidEmail"] = True
                    return redirect(redirectURL)
            else:
                userList = []
                for users in userDict:
                    user = userDict.get(users)
                    userList.append(user)

                maxItemsPerPage = 10 # declare the number of items that can be seen per pages
                userListLen = len(userList) # get the length of the userList
                maxPages = math.ceil(userListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number

                # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/page/0" or negative numbers, "user_management/page/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/page/999999"
                if pageNum < 0:
                    return redirect("/user_management/page/0")
                elif userListLen > 0 and pageNum == 0:
                    return redirect("/user_management/page/1")
                elif pageNum > maxPages:
                    redirectRoute = "/user_management/page/" + str(maxPages)
                    return redirect(redirectRoute)
                else:
                    # pagination algorithm starts here
                    userList = userList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                    pageNumForPagination = pageNum - 1 # minus for the paginate function
                    paginatedUserList = paginate(userList, pageNumForPagination, maxItemsPerPage)
                    paginationList = get_pagination_button_list(pageNum, maxPages)

                    session["pageNum"] = pageNum # for uxd so that the admin can be on the same page after managing the user such as deleting the user account, etc.

                    previousPage = pageNum - 1
                    nextPage = pageNum + 1

                    if "invalidEmail" in session:
                        invalidEmail = True
                        session.pop("invalidEmail", None)
                    else:
                        invalidEmail = False

                    if "sameEmail" in session:
                        sameEmail = True
                        session.pop("sameEmail", None)
                    else:
                        sameEmail = False

                    if "duplicateEmail" in session:
                        duplicateEmail = True
                        session.pop("duplicateEmail", None)
                    else:
                        duplicateEmail = False

                    if "duplicateUsername" in session:
                        duplicateUsername = True
                        session.pop("duplicateUsername", None)
                    else:
                        duplicateUsername = False

                    return render_template('users/admin/user_management.html', userList=paginatedUserList, count=userListLen, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, form=admin_reset_password_form, invalidEmail=invalidEmail, sameEmail=sameEmail, duplicateEmail=duplicateEmail, searched=False, duplicateUsername=duplicateUsername, parameter="")
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/user_management/search/<int:pageNum>/", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def userSearchManagement(pageNum):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        userFound, accActive = admin_validate_session_open_file(adminSession)
        if userFound and accActive:
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

            parameter = str(sanitise(request.args.get("user")))
            # if user types in something such as a js script with bad intention or empty value form submission by tempering with the html required attribute via inspect element, it will return "False"
            if parameter == "False":
                # redirect the admin instead so that they know that the inputs are not accepted due to security reasons
                return redirect(url_for("userSearchManagementError"))

            parametersURL = "?user=" + parameter
            # for resetting the user's password and updating the user's email for account recovery
            admin_reset_password_form = Forms.AdminResetPasswordForm(request.form)
            if request.method == "POST" and admin_reset_password_form.validate():
                password = generate_password()
                email = sanitise(admin_reset_password_form.email.data)
                validEmail = validate_email(email)

                # for redirecting the admin to the user management page that he/she was in
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0

                redirectURL = "/user_management/search/" + str(pageNum) +"/" + parametersURL

                if validEmail:
                    userID = int(request.form["userID"])
                    userKey = userDict.get(userID)
                    oldEmail = userKey.get_email()
                    duplicateEmail = check_duplicates(email, userDict, "email")
                    if oldEmail != email:
                        if duplicateEmail == False:
                            if userKey != None:
                                # changing the password of the user
                                hashedPwd = hash_password(password)
                                userKey.set_password(hashedPwd)
                                userKey.set_email(email)
                                userKey.set_email_verification("Not Verified")
                                db["Users"] = userDict
                                db.close()
                                send_admin_reset_email(email, password) # sending an email to the user to notify them of the change
                                print("User account recovered successfully and email sent.")
                                return redirect(redirectURL)
                            else:
                                db.close()
                                print("Error in retrieving user object.")
                                return redirect(redirectURL)
                        else:
                            db.close()
                            print("Inputted new user's email is not unique.")
                            session["duplicateEmail"] = True
                            return redirect(redirectURL)
                    else:
                        db.close()
                        print("User's new email inputted is the same as the old email.")
                        session["sameEmail"] = True
                        return redirect(redirectURL)
                else:
                    db.close()
                    print("Inputted new user's email is invalid.")
                    session["invalidEmail"] = True
                    return redirect(redirectURL)
            else:
                query = request.args.get("user")
                print(query)
                userList = []
                if query in userDict: # if admin searches for the user using the user id
                    print("Query is a user's ID.")
                    userList.append(userDict.get(query))
                if validate_email(query):
                    print("Query is an email.")
                    for key in userDict:
                        userKey = userDict[key]
                        if userKey.get_email() == query:
                            userList.append(userKey)
                            break
                else: # if the admin searches for the user using the user's username
                    print("Query is a username")
                    usernameList = []
                    for users in userDict:
                        user = userDict.get(users)
                        usernameList.append(user.get_username())

                    try:
                        matchedUsernameList = difflib.get_close_matches(query, usernameList, len(usernameList), 0.85) # return a list of closest matched username with a length of the whole list as difflib will only return the 3 closest matches by default. I then set the cutoff to 0.85, i.e. must match to a certain percentage else it will be ignored.
                    except:
                        matchedUsernameList = []

                    print("Matched user (in a list):", matchedUsernameList)
                    for userKey in userDict:
                        userObject = userDict.get(userKey)
                        username = userObject.get_username()
                        for key in matchedUsernameList:
                            if username == key:
                                userList.append(userObject)

                maxItemsPerPage = 10 # declare the number of items that can be seen per pages
                userListLen = len(userList) # get the length of the userList
                maxPages = math.ceil(userListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number

                # redirecting for handling different situation where if the user manually keys in the url
                if pageNum < 0:
                    redirectRoute = "/user_management/search/0/" + parametersURL
                    return redirect(redirectRoute)
                elif userListLen > 0 and pageNum == 0:
                    redirectRoute = "/user_management/search/1" + "/" + parametersURL
                    return redirect(redirectRoute)
                elif pageNum > maxPages:
                    redirectRoute = "/user_management/search/" + str(maxPages) +"/" + parametersURL
                    return redirect(redirectRoute)
                else:
                   # pagination algorithm starts here
                    userList = userList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                    pageNumForPagination = pageNum - 1 # minus for the paginate function
                    paginatedUserList = paginate(userList, pageNumForPagination, maxItemsPerPage)
                    paginationList = get_pagination_button_list(pageNum, maxPages)

                    session["pageNum"] = pageNum # for uxd so that the admin can be on the same page after managing the user such as deleting the user account, etc.

                    previousPage = pageNum - 1
                    nextPage = pageNum + 1

                    if "invalidEmail" in session:
                        invalidEmail = True
                        session.pop("invalidEmail", None)
                    else:
                        invalidEmail = False

                    if "sameEmail" in session:
                        sameEmail = True
                        session.pop("sameEmail", None)
                    else:
                        sameEmail = False

                    if "duplicateEmail" in session:
                        duplicateEmail = True
                        session.pop("duplicateEmail", None)
                    else:
                        duplicateEmail = False

                    if "duplicateUsername" in session:
                        duplicateUsername = True
                        session.pop("duplicateUsername", None)
                    else:
                        duplicateUsername = False

                    session["searchedPageRoute"] = "/user_management/search/" + str(pageNum) + "/" + parametersURL

                    return render_template('users/admin/user_management.html', userList=paginatedUserList, count=userListLen, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, form=admin_reset_password_form, invalidEmail=invalidEmail, sameEmail=sameEmail, duplicateEmail=duplicateEmail, searched=True, submittedParameters=parametersURL, duplicateUsername=duplicateUsername, parameter=parameter)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

# if the user tempers with the html search input and removed the require attribute or if the user tries to XSS the site.
@app.route("/user_management/search/not_allowed")
@limiter.limit("30/second") # to prevent ddos attacks
def userSearchManagementError():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        userFound, accActive = admin_validate_session_open_file(adminSession)
        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)
            return render_template('users/admin/user_management.html', notAllowed = True, searched=True, redirectURL=redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/delete_user/uid/<userID>", methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def deleteUser(userID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the admin to the user management page
                    return redirect(url_for("userManagement"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("userManagement"))

            userKey = userDict.get(userID)

            if userKey != None:
                userImageFileName = userKey.get_profile_image()
                userDict.pop(userID)
                db['Users'] = userDict
                db.close()
                delete_user_profile(userImageFileName)
                print(f"User account with the ID, {userID}, has been deleted.")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/ban/uid/<userID>", methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def banUser(userID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the admin to the user management page
                    return redirect(url_for("userManagement"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("userManagement"))

            userKey = userDict.get(userID)

            if userKey != None:
                userKey.set_status("Banned")
                db['Users'] = userDict
                db.close()
                print(f"User account with the ID, {userID}, has been banned.")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/unban/uid/<userID>", methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def unbanUser(userID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the admin to the user management page
                    return redirect(url_for("userManagement"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("userManagement"))

            userKey = userDict.get(userID)

            if userKey != None:
                userKey.set_status("Good")
                db['Users'] = userDict
                db.close()
                print(f"User account with the ID, {userID}, has been unbanned.")
                send_admin_unban_email(userKey.get_email()) # sending an email to the user to notify that his/her account has been unbanned
                print("Successfully sent an email.")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/change_username/uid/<userID>", methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def changeUserUsername(userID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the admin to the user management page
                    return redirect(url_for("userManagement"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("userManagement"))

            userKey = userDict.get(userID)

            if userKey != None:
                username = sanitise(request.form["username"])
                duplicate_username = check_duplicates(username, userDict, "username")
                if duplicate_username == False:
                    userKey.set_username(username)
                    db['Users'] = userDict
                    db.close()
                    print("Username successfully changed.")
                    return redirect(redirectURL)
                else:
                    db.close()
                    print("Duplicate username.")
                    session["duplicateUsername"] = True
                    return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/reset_profile_image/uid/<userID>", methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def resetProfileImage(userID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the admin to the user management page
                    return redirect(url_for("userManagement"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("userManagement"))

            userKey = userDict.get(userID)

            if userKey != None:
                userKey.set_profile_image("")
                userImageFileName = userKey.get_profile_image()
                db['Users'] = userDict
                db.close()
                delete_user_profile(userImageFileName)
                print(f"User account with the ID, {userID}, has its profile picture reset.")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""End of User Management for Admins by Jason"""

"""User Profile Settings by Jason"""

@app.route('/user_profile', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def userProfile():
    if "userSession" in session and "adminSession" not in session:
        session.pop("teacher", None) # deleting data from the session if the user chooses to skip adding a payment method from the teacher signup process

        userSession = session["userSession"]

        # Retrieving data from shelve and to set the teacher's payment method info data
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
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

        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            emailVerified = userKey.get_email_verification()
            if emailVerified == "Not Verified":
                emailVerification = False
            else:
                emailVerification = True
            if request.method == "POST":
                typeOfFormSubmitted = request.form.get("submittedForm")
                if typeOfFormSubmitted == "bio":
                    teacherBioInput = sanitise(request.form.get("teacherBio"))
                    if teacherBioInput == False:
                        teacherBioInput = ""
                    userKey.set_bio(teacherBioInput)
                    db['Users'] = userDict
                    db.close()
                    print("Teacher bio saved.")
                    return redirect(url_for("userProfile"))
                elif typeOfFormSubmitted == "image":
                    if "profileImage" not in request.files:
                        print("No file sent.")
                        return redirect(url_for("userProfile"))

                    file = request.files["profileImage"]

                    extensionType = get_extension(file.filename)
                    if extensionType != False:
                        file.filename = userSession + extensionType # renaming the file name of the submitted image data payload
                        filename = file.filename
                    else:
                        filename = "invalid"

                    uploadedFileSize = request.cookies.get("filesize") # getting the uploaded file size value from the cookie made in the javascript when uploading the user profile image
                    print("Uploaded file size:", uploadedFileSize, "bytes")

                    withinFileLimit = allow_file_size(uploadedFileSize, app.config['MAX_PROFILE_IMAGE_FILESIZE'])

                    if file and allowed_image_file(filename) and withinFileLimit:
                        # will only accept .png, .jpg, .jpeg
                        print("File extension accepted and is within size limit.")

                        # to construct a file path for userID.extension (e.g. 0.jpg) for renaming the file

                        userImageFileName = file.filename
                        newFilePath = construct_path(PROFILE_UPLOAD_PATH, userImageFileName)

                        # constructing a file path to see if the user has already uploaded an image and if the file exists
                        userOldImageFilePath = construct_path(PROFILE_UPLOAD_PATH, userKey.get_profile_image())

                        # using Path from pathlib to check if the file path of userID.png (e.g. 0.png) already exist.
                        # if file already exist, it will remove and save the image and rename it to userID.png (e.g. 0.png) which in a way is overwriting the existing image
                        # else it will just save normally and rename it to userID.png (e.g. 0.png)
                        if Path(userOldImageFilePath).is_file():
                            print("User has already uploaded a profile image before.")
                            overwrite_file(file, userOldImageFilePath, newFilePath)
                            print("Image file has been overwrited.")
                        else:
                            file.save(newFilePath)
                            print("Image file has been saved.")

                        # resizing the image to a 1:1 ratio that was recently uploaded and stored in the server directory
                        imageResized = resize_image(newFilePath, (500, 500))

                        if imageResized:
                            # if file was successfully resized, it means the image is a valid image
                            userKey.set_profile_image(userImageFileName)
                            db['Users'] = userDict
                            db.close()

                            session["imageChanged"] = True
                            return redirect(url_for("userProfile"))
                        else:
                            # else this means that the image is not an image since Pillow is unable to open the image due to it being an unsupported image file in which the code below will reset the user's profile image but the corrupted image will still be stored on the server until it is overwritten
                            userKey.set_profile_image("")
                            db['Users'] = userDict
                            db.close()
                            session["imageFailed"] = True
                            return redirect(url_for("userProfile"))
                    else:
                        db.close()
                        print("Image extension not allowed or exceeded maximum image size of {} bytes" .format(app.config['MAX_PROFILE_IMAGE_FILESIZE']))
                        session["imageFailed"] = True
                        return redirect(url_for("userProfile"))
                else:
                    db.close()
                    print("Form value tampered...")
                    return redirect(url_for("userProfile"))
            else:
                db.close()
                userUsername = userKey.get_username()
                userEmail = userKey.get_email()

                if accType == "Teacher":
                    teacherBio = userKey.get_bio()
                else:
                    teacherBio = ""

                print(teacherBio)

                userProfileImage = userKey.get_profile_image() # will return a filename, e.g. "0.png"
                userProfileImagePath = construct_path(PROFILE_UPLOAD_PATH, userProfileImage)

                # checking if the user have uploaded a profile image before and if the image file exists
                imagesrcPath = get_user_profile_pic(userUsername, userProfileImage, userProfileImagePath)

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

                # email verification notifications checking
                # for notifying if the token has been sent to their email
                if "emailVerifySent" in session:
                    emailSent = True
                    session.pop("emailVerifySent", None)
                else:
                    emailSent = False

                # for notifying if they have already verified their email (traversal attack)
                if "emailFailed" in session:
                    emailAlreadyVerified = True
                    session.pop("emailFailed", None)
                else:
                    emailAlreadyVerified = False

                # for notifying if they have verified their email from the link in their email
                if "emailVerified" in session:
                    emailVerified = True
                    session.pop("emailVerified", None)
                else:
                    emailVerified = False

                # for notifying if the email verification link has expired/is invalid
                if "emailTokenInvalid" in session:
                    emailTokenInvalid = True
                    session.pop("emailTokenInvalid", None)
                else:
                    emailTokenInvalid = False

                return render_template('users/loggedin/user_profile.html', username=userUsername, email=userEmail, accType = accType, teacherBio=teacherBio, emailChanged=emailChanged, usernameChanged=usernameChanged, passwordChanged=passwordChanged, imageFailed=imageFailed, imageChanged=imageChanged, imagesrcPath=imagesrcPath, recentChangeAccType=recentChangeAccType, emailVerification=emailVerification, emailSent=emailSent, emailAlreadyVerified=emailAlreadyVerified, emailVerified=emailVerified, emailTokenInvalid=emailTokenInvalid)
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
@limiter.limit("30/second") # to prevent ddos attacks
def updateUsername():
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
                session.clear()
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object from the shelve based on the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            imagesrcPath = retrieve_user_profile_pic(userKey)
            create_update_username_form = Forms.CreateChangeUsername(request.form)
            if request.method == "POST" and create_update_username_form.validate():
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
                        db.close()
                        return render_template('users/loggedin/change_username.html', form=create_update_username_form, username_duplicates=True, accType=accType, imagesrcPath=imagesrcPath)
                else:
                    db.close()
                    print("Update username input same as user's current username")
                    return render_template('users/loggedin/change_username.html', form=create_update_username_form, sameUsername=True, accType=accType, imagesrcPath=imagesrcPath)
            else:
                db.close()
                return render_template('users/loggedin/change_username.html', form=create_update_username_form, accType=accType, imagesrcPath=imagesrcPath)
        else:
            db.close()
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route("/change_email", methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def updateEmail():
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
                session.clear()
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)
        if userFound and accGoodStatus:
            imagesrcPath = retrieve_user_profile_pic(userKey)
            create_update_email_form = Forms.CreateChangeEmail(request.form)
            if request.method == "POST" and create_update_email_form.validate():

                updatedEmail = sanitise(create_update_email_form.updateEmail.data.lower())
                currentEmail = userKey.get_email()
                if updatedEmail != currentEmail:
                    # Checking duplicates for email
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
                        userKey.set_email_verification("Not Verified")
                        send_verify_changed_email(updatedEmail, currentEmail, userSession)
                        db['Users'] = userDict
                        db.close()
                        print("Email updated")

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of email
                        session["email_updated"] = True

                        send_email_change_notification(currentEmail, updatedEmail) # sending an email to alert the user of the change of email so that the user will know about it and if his/her account was compromised, he/she will be able to react promptly by contacting CourseFinity support team
                        return redirect(url_for("userProfile"))
                    else:
                        db.close()
                        return render_template('users/loggedin/change_email.html', form=create_update_email_form, email_duplicates=True, accType=accType, imagesrcPath=imagesrcPath)
                else:
                    db.close()
                    print("User updated email input is the same as their current email")
                    return render_template('users/loggedin/change_email.html', form=create_update_email_form, sameEmail=True, accType=accType, imagesrcPath=imagesrcPath)
            else:
                db.close()
                return render_template('users/loggedin/change_email.html', form=create_update_email_form, accType=accType, imagesrcPath=imagesrcPath)
        else:
            db.close()
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route("/change_password", methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def updatePassword():
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
                session.clear()
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)
        if userFound and accGoodStatus:
            imagesrcPath = retrieve_user_profile_pic(userKey)
            create_update_password_form = Forms.CreateChangePasswordForm(request.form)
            if request.method == "POST" and create_update_password_form.validate():
                # declaring passwordNotMatched, passwordVerification, and errorMessage variable to initialise and prevent unboundLocalError
                passwordNotMatched = True
                passwordVerification = False

                # for jinja2
                errorMessage = False

                currentPassword = create_update_password_form.currentPassword.data
                updatedPassword = create_update_password_form.updatePassword.data
                confirmPassword = create_update_password_form.confirmPassword.data

                # Retrieving current password of the user
                currentStoredPassword = userKey.get_password()

                # validation starts
                print("Updated password input:", updatedPassword)
                print("Confirm password input", confirmPassword)
                if updatedPassword == confirmPassword:
                    passwordNotMatched = False
                    print("New and confirm password inputs matched")
                else:
                    print("New and confirm password inputs did not match")

                print("Current password:", currentStoredPassword)
                print("Current password input:", currentPassword)

                passwordVerification = verify_password(currentStoredPassword, currentPassword)
                oldPassword = verify_password(currentStoredPassword, updatedPassword)

                # printing message for debugging purposes
                if passwordVerification:
                    print("User identity verified")
                else:
                    print("Current password input hash did not match with the one in the shelve database")

                # if there any validation error, errorMessage will become True for jinja2 to render the error message
                if passwordVerification == False or passwordNotMatched:
                    db.close()
                    errorMessage = True
                    return render_template('users/loggedin/change_password.html', form=create_update_password_form, errorMessage=errorMessage, accType=accType, imagesrcPath=imagesrcPath)
                else:
                    if oldPassword:
                        db.close()
                        print("User cannot change password to their current password!")
                        return render_template('users/loggedin/change_password.html', form=create_update_password_form, samePassword=True, accType=accType, imagesrcPath=imagesrcPath)
                    else:
                        # updating password of the user once validated
                        hashedPwd = hash_password(updatedPassword)
                        userKey.set_password(hashedPwd)
                        userEmail = userKey.get_email()
                        db['Users'] = userDict
                        print("Password updated")
                        db.close()

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of password
                        session["password_changed"] = True

                        send_password_change_notification(userEmail) # sending an email to alert the user of the change of password so that the user will know about it and if his/her account was compromised, he/she will be able to react promptly by contacting CourseFinity support team or if the email was not changed, he/she can reset his/her password in the reset password page
                        return redirect(url_for("userProfile"))
            else:
                db.close()
                return render_template('users/loggedin/change_password.html', form=create_update_password_form, accType=accType, imagesrcPath=imagesrcPath)
        else:
            db.close()
            print("User not found is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route('/change_account_type', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
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
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        accType = userKey.get_acc_type()
        print("Account type:", accType)

        if userFound and accGoodStatus:
            imagesrcPath = retrieve_user_profile_pic(userKey)
            if accType == "Student":
                if request.method == "POST":
                    # changing the user's account type to teacher by deleting the student object and creating a new teacher object, and hence, changing the user ID as a whole.
                    username = userKey.get_username()
                    password = userKey.get_password()
                    email = userKey.get_email()
                    userID = userSession

                    # retrieving the user's payment info if the user has saved one
                    cardExists = bool(userKey.get_card_name())
                    if cardExists:
                        cardName = userKey.get_card_name()
                        cardNumber = userKey.get_card_no()
                        cardExpiry = userKey.get_card_expiry()
                        cardType = userKey.get_card_type()

                    # retrieving the user's profile image filename if the user has uploaded one
                    profileImageExists = bool(userKey.get_profile_image())
                    print("Does user have profile image:", profileImageExists)
                    if profileImageExists:
                        profileImageFilename = userKey.get_profile_image()
                        imagePath = construct_path(PROFILE_UPLOAD_PATH, profileImageFilename)
                        if Path(imagePath).is_file():
                            profileImagePathExists = True
                            print("Profile image exists:", profileImagePathExists)
                        else:
                            profileImagePathExists = False

                    userDict.pop(userID)
                    user = Teacher.Teacher(userID, username, email, password)
                    user.set_teacher_join_date(date.today())
                    userDict[userID] = user

                    # setting the user's payment method if the user has saved their payment method before
                    if cardExists:
                        user.set_card_name(cardName)
                        user.set_card_no(cardNumber)
                        user.set_card_expiry(cardExpiry)
                        user.set_card_type(cardType)

                    # saving the user's profile image if the user has uploaded their profile image
                    if profileImageExists and profileImagePathExists:
                        user.set_profile_image(profileImageFilename)

                    # add in other saved attributes of the student object

                    # checking if the user has already became a teacher
                    # Not needed but for scability as if there's a feature that allows teachers to revert back to a student in the future, the free three months 0% commission system can be abused.
                    if bool(user.get_teacher_join_date) == False:
                        user.set_teacher_join_date(date.today())
                        print("User has not been a teacher, setting today's date as joined date.")

                    db["Users"] = userDict
                    db.close()
                    session["userSession"] = userID
                    print("Account type updated to teacher.")
                    session["recentChangeAccType"] = True # making a session so that jinja2 can render a notification of the account type change
                    return redirect(url_for("userProfile"))
                else:
                    db.close()
                    return render_template("users/student/change_account_type.html", accType=accType, imagesrcPath=imagesrcPath)
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
            return redirect(url_for("teacherSignUp"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("teacherSignUp"))

"""End of User Profile Settings by Jason"""

"""User payment method settings by Jason"""

@app.route('/payment_method', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
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
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            imagesrcPath = retrieve_user_profile_pic(userKey)
            cardExist = bool(userKey.get_card_name())
            print("Card exist?:", cardExist)

            if cardExist == False:
                create_add_payment_form = Forms.CreateAddPaymentForm(request.form)
                if request.method == "POST" and create_add_payment_form.validate():
                    print("POST request sent and form entries validated")
                    cardName = sanitise(create_add_payment_form.cardName.data)

                    cardNo = sanitise(create_add_payment_form.cardNo.data)
                    cardValid = validate_card_number(cardNo)

                    cardType = get_credit_card_type(cardNo, cardValid) # get type of the credit card for specific warning so that the user would know that only Mastercard and Visa cards are only accepted

                    cardExpiry = sanitise(create_add_payment_form.cardExpiry.data)
                    cardExpiryValid = validate_expiry_date(cardExpiry)

                    if cardValid and cardExpiryValid:
                        if cardType != False:
                            # setting the user's payment method
                            userKey.set_card_name(cardName)
                            userKey.set_card_no(cardNo)
                            cardExpiry = cardExpiryStringFormatter(cardExpiry)
                            userKey.set_card_expiry(cardExpiry)
                            userKey.set_card_type(cardType)
                            userKey.display_card_info()
                            db['Users'] = userDict
                            print("Payment added")

                            # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of adding the payment method
                            session["payment_added"] = True

                            db.close()
                            return redirect(url_for("userPayment"))
                        else:
                            return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form, invalidCardType=True, accType=accType, imagesrcPath=imagesrcPath)
                    else:
                        return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form, cardValid=cardValid, cardExpiryValid=cardExpiryValid, accType=accType, imagesrcPath=imagesrcPath)
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

                    return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form, cardDeleted=cardDeleted, accType=accType, imagesrcPath=imagesrcPath)
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

                return render_template('users/loggedin/user_existing_payment.html', cardName=cardName, cardNo=cardNo, cardExpiry=cardExpiry, cardType=cardType, cardUpdated=cardUpdated, cardAdded=cardAdded, accType=accType, imagesrcPath=imagesrcPath)
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

@app.route('/edit_payment', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
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
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            imagesrcPath = retrieve_user_profile_pic(userKey)
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
                    cardExpiry = sanitise(create_edit_payment_form.cardExpiry.data)
                    cardExpiryValid = validate_expiry_date(cardExpiry)
                    if cardExpiryValid:
                        # changing the user's payment info
                        cardExpiry = cardExpiryStringFormatter(cardExpiry)
                        userKey.set_card_expiry(cardExpiry)
                        db['Users'] = userDict
                        print("Payment edited")
                        db.close()

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of the card details
                        session["card_updated"] = True

                        return redirect(url_for("userPayment"))
                    else:
                        db.close()
                        return render_template('users/loggedin/user_edit_payment.html', form=create_edit_payment_form, cardName=cardName, cardNo=cardNo, cardType=cardType, accType=accType, cardExpiryValid=cardExpiryValid, imagesrcPath=imagesrcPath)
                else:
                    db.close()
                    return render_template('users/loggedin/user_edit_payment.html', form=create_edit_payment_form, cardName=cardName, cardNo=cardNo, cardType=cardType, accType=accType, imagesrcPath=imagesrcPath)
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
@limiter.limit("30/second") # to prevent ddos attacks
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
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            # checking if the user has a credit card in the shelve database to prevent directory traversal if the logged in attackers send a POST request to the web app server
            cardExist = bool(userKey.get_card_name())
            print("Card exist?:", cardExist)

            if cardExist:
                # deleting user's payment info, specifically changing their payment info to empty strings
                userKey.set_card_name("")
                userKey.set_card_no("")
                userKey.set_card_expiry("")
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

"""Teacher Cashout System by Jason"""

@app.route("/teacher_cashout", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
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
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            if "cashedOut" in session:
                cashedOut = True
                session.pop("cashedOut", None)
            else:
                cashedOut = False
            
            if "failedToCashOut" in session:
                failedToCashOut = True
                session.pop("failedToCashOut", None)
            else:
                failedToCashOut = False

            if "noPayment" in session:
                noPayment = True
                session.pop("noPayment", None)
            else:
                noPayment = False

            imagesrcPath = retrieve_user_profile_pic(userKey)
            joinedDate = userKey.get_teacher_join_date()
            zeroCommissionEndDate = joinedDate + timedelta(days=90)
            currentDate = date.today()

            # if it's the first day of the month
            resetMonth = check_first_day_of_month(currentDate)
            initialEarnings = round(userKey.get_earnings(), 2)
            accumulatedEarnings = userKey.get_accumulated_earnings()
            if resetMonth:
                accumulatedEarnings += initialEarnings
                userKey.set_accumulated_earnings(accumulatedEarnings)
                userKey.set_earnings(0)

            lastDayOfMonth = check_last_day_of_month(currentDate)

            if request.method == "POST":
                typeOfCollection = request.form.get("typeOfCollection")
                if ((accumulatedEarnings + initialEarnings) > 0):
                    # simple resetting of teacher's income
                    doesCardExist = bool(userKey.get_card_name())
                    if doesCardExist != False:
                        if typeOfCollection == "collectingAll" and lastDayOfMonth:
                            session["cashedOut"] = True
                            userKey.set_earnings(0)
                            userKey.set_accumulated_earnings(0)
                            db.close()
                            return redirect(url_for("teacherCashOut"))
                        elif typeOfCollection == "collectingAccumulated":
                            session["cashedOut"] = True
                            userKey.set_accumulated_earnings(0)
                            db.close()
                            return redirect(url_for("teacherCashOut"))
                        else:
                            db.close()
                            print("POST request sent but it is not the last day of the month or post request sent but had tampered values in hidden input.")
                            session["failedToCashOut"] = True
                            return redirect(url_for("teacherCashOut"))
                    else:
                        db.close()
                        session["noPayment"] = True
                        print("POST request sent but user does not have a valid payment method to cash out to.")
                        return redirect(url_for("teacherCashOut"))
                else:
                    db.close()
                    print("POST request sent but user have already collected their revenue or user did not earn any this month.")
                    session["failedToCashOut"] = True
                    return redirect(url_for("teacherCashOut"))
            else:
                db.close()
                monthTuple = ("January ", "February ", "March ", "April ", "May ", "June ", "July ", "August ", "September ", "October ", "November ", "December ")
                month = monthTuple[(int(date.today().month) - 1)] # retrieves the month in a word format from the tuple instead of 1 for January.
                monthYear = month + str(date.today().year)
                remainingDays = int(str(zeroCommissionEndDate - currentDate)[0:2]) # to get the remaining days left to alert the user to make full use of it, since without string slicing, it will return a value such as "86 days, 0:00:00".

                if accumulatedEarnings > 0:
                    accumulatedCollect = True
                else:
                    accumulatedCollect = False

                if currentDate <= zeroCommissionEndDate:
                    commission = "0%"
                    totalEarned = round((initialEarnings + accumulatedEarnings), 2)

                    # converting the number of remaining days till the free 0% commission is over in a readable format as compared to "you have until 60 days till it is over" for an example.
                    if remainingDays > 60 and remainingDays <= 90:
                        remainingDays = "3 months"
                    elif remainingDays > 30 and remainingDays <= 60:
                        remainingDays = "2 months"
                    elif remainingDays == 30:
                        remainingDays = "1 month"
                    elif remainingDays > 7 and remainingDays < 30:
                        remainingDays = "less than a month"
                    elif remainingDays <= 7:
                        remainingDays = "less than a week"
                    elif remainingDays < 0:
                        remainingDays = 0
                        print("User's free 0% three months commission is over.")
                    else:
                        remainingDays = "Unexpected error, please contact CourseFinity support."
                else:
                    commission = "25%"
                    totalEarned = round(((initialEarnings + accumulatedEarnings) - (initialEarnings * 0.25)), 2)
                    
                totalEarnedInt = totalEarned
                # converting the numbers into strings of 2 decimal place for the earnings
                initialEarnings = get_two_decimal_pt(initialEarnings)
                totalEarned = get_two_decimal_pt(totalEarned)
                accumulatedEarnings = get_two_decimal_pt(accumulatedEarnings)

                return render_template('users/teacher/teacher_cashout.html', accType=accType, imagesrcPath=imagesrcPath, monthYear=monthYear, lastDayOfMonth=lastDayOfMonth, commission=commission, totalEarned=totalEarned, initialEarnings=initialEarnings, accumulatedEarnings=accumulatedEarnings, remainingDays=remainingDays, totalEarnedInt=totalEarnedInt, failedToCashOut=failedToCashOut, cashedOut=cashedOut, accumulatedCollect=accumulatedCollect, noPayment=noPayment)
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

"""End of Teacher Cashout System by Jason"""

"""Search Function by Royston"""

@app.route('/search/<int:pageNum>/', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
@limiter.limit("30/second") # to prevent ddos attacks
def search(pageNum):
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

            userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)

            if userFound and accGoodStatus:
                imagesrcPath = retrieve_user_profile_pic(userKey)
                # add in your code here (if any)
                checker = ""
                courseDict = {}
                courseTitleList = []
                try:
                    db = shelve.open("user", "r")
                    courseDict = db["Courses"]

                except:
                    print("Error in obtaining course.db data")
                    return redirect(url_for("home"))

                searchInput = request.args.get("q")
                print(searchInput)
                titleList = []
                for courseID in courseDict:
                    courseTitle = courseDict.get(courseID).get_title()
                    courseTitleList.append(courseTitle)
                try:
                    matchedCourseTitleList = difflib.get_close_matches(searchInput, courseTitleList, len(courseTitleList), 0.80) # return a list of closest matched search with a length of the whole list as difflib will only return the 3 closest matches by default. I then set the cutoff to 0.80, i.e. must match to a certain percentage else it will be ignored.
                except:
                    matchedCourseTitleList = []
                print(matchedCourseTitleList)
                for courseID in courseDict:
                    courseObject = courseDict.get(courseID)
                    titleCourse = courseObject.get_title()
                for key in matchedCourseTitleList:
                    if titleCourse == key:
                        titleList.append(courseObject)
                print(titleList)
                if bool(titleList):
                    checker = False
                else:
                    checker = True
                

                db.close()

                maxItemsPerPage = 5 # declare the number of items that can be seen per pages
                courseListLen = len(courseTitleList) # get the length of the userList
                maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
                pageNum = int(pageNum)
                # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
                if pageNum < 0:
                    return redirect("/search/0")
                elif courseListLen > 0 and pageNum == 0:
                    return redirect("/search/1")
                elif pageNum > maxPages:
                    redirectRoute = "/search/" + str(maxPages)
                    return redirect(redirectRoute)
                else:
                    # pagination algorithm starts here
                    courseTitleList = courseTitleList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                    pageNumForPagination = pageNum - 1 # minus for the paginate function
                    paginatedCourseList = paginate(courseTitleList, pageNumForPagination, maxItemsPerPage)
                    courseTitleList = paginate(courseTitleList[::-1], pageNumForPagination, maxItemsPerPage)

                    paginationList = get_pagination_button_list(pageNum, maxPages)

                    previousPage = pageNum - 1
                    nextPage = pageNum + 1

                    db.close()
                    return render_template('users/general/search.html', accType=accType, courseDict=courseDict, matchedCourseTitleList=matchedCourseTitleList,searchInput=searchInput, pageNum=pageNum, previousPage = previousPage, nextPage = nextPage, paginationList = paginationList, maxPages=maxPages, imagesrcPath=imagesrcPath, checker=checker, individualCount=len(paginatedCourseList), courseTitleList=paginatedCourseList)

            else:
                print("Admin/User account is not found or is not active/banned.")
                session.clear()
                return render_template("users/guest/guest_home.html", accType="Guest")
    else:
        checker = ""
        courseDict = {}
        courseTitleList = []
        try:
            db = shelve.open("course", "r")
            courseDict = db["Courses"]

        except:
            print("Error in obtaining course.db data")
            return redirect(url_for("home"))

        searchInput = request.args.get("q")
        print(searchInput)
        titleList = []
        for courseID in courseDict:
            courseTitle = courseDict.get(courseID).get_title()
            courseTitleList.append(courseTitle)
        try:
            matchedCourseTitleList = difflib.get_close_matches(searchInput, courseTitleList, len(courseTitleList), 0.80) # return a list of closest matched search with a length of the whole list as difflib will only return the 3 closest matches by default. I then set the cutoff to 0.80, i.e. must match to a certain percentage else it will be ignored.
        except:
            matchedCourseTitleList = []
        print(matchedCourseTitleList)
        for courseID in courseDict:
            courseObject = courseDict.get(courseID)
            titleCourse = courseObject.get_title()
        for key in matchedCourseTitleList:
            if titleCourse == key:
                titleList.append(courseObject)
        print(titleList)
        if bool(titleList):
            checker = False
        else:
            checker = True
        print("What is in the titeList?: ",titleList)

        db.close()

        maxItemsPerPage = 5 # declare the number of items that can be seen per pages
        courseListLen = len(courseTitleList) # get the length of the userList
        maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
        pageNum = int(pageNum)
        # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
        if pageNum < 0:
            return redirect("/search/0")
        elif courseListLen > 0 and pageNum == 0:
            return redirect("/search/1")
        elif pageNum > maxPages:
            redirectRoute = "/search/" + str(maxPages)
            return redirect(redirectRoute)
        else:
            # pagination algorithm starts here
            courseTitleList = courseTitleList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
            pageNumForPagination = pageNum - 1 # minus for the paginate function
            paginatedCourseList = paginate(courseTitleList, pageNumForPagination, maxItemsPerPage)
            courseTitleList = paginate(courseTitleList[::-1], pageNumForPagination, maxItemsPerPage)

            paginationList = get_pagination_button_list(pageNum, maxPages)

            previousPage = pageNum - 1
            nextPage = pageNum + 1

            db.close()
            return render_template('users/general/search.html', courseDict=courseDict, matchedCourseTitleList=matchedCourseTitleList,searchInput=searchInput, pageNum=pageNum, previousPage = previousPage, nextPage = nextPage, paginationList = paginationList, maxPages=maxPages, checker=checker, individualCount=len(paginatedCourseList), courseTitleList=paginatedCourseList)

""""End of Search Function by Royston"""

"""Purchase History by Royston"""

@app.route("/purchasehistory/<int:pageNum>")
@limiter.limit("30/second") # to prevent ddos attacks
def purchaseHistory(pageNum):
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
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            imagesrcPath = retrieve_user_profile_pic(userKey)
            # insert your C,R,U,D operation here to deal with the user shelve data files
            courseID = ""
            courseType = ""
            historyCheck = True
            historyList = []
            showCourse = ""
            # Get purchased courses
            purchasedCourses = userKey.get_purchases()
            print("PurchaseID exists?: ", purchasedCourses)

            if purchasedCourses != []:
                try:
                    courseDict = {}
                    db = shelve.open("user", "r")
                    courseDict = db["Courses"]
                except:
                    print("Unable to open up course shelve")
                    db.close()

                # Get specific course with course ID
                for courseInfo in list(purchasedCourses.keys()):
                    print(courseInfo)
                    # courseInfo is key
                    courseID = courseInfo.split("_")[0]
                    courseType = courseInfo.split("_")[1]

                # Find the correct course
                course = courseDict[courseID]


                #id will be an integer

                video = {id :
                    {courseDict : {"Title":course.get_title(),
                    "Description":course.get_description(),
                    "Thumbnail":course.get_thumbnail(),
                    "VideoCheck":course.get_courseType()["Video"],
                    "ZoomCheck":course.get_courseType()["Zoom"],
                    "Price":course.get_price(),
                    "Owner":course.get_owner()}
                        }
                    }
                for i in purchasedCourses:
                    showCourse(video[i])
                    historyList.append(showCourse)
                    print(historyList)

                db.close()
            else:
                print("Purchase History is Empty")
                historyCheck = False

            maxItemsPerPage = 5 # declare the number of items that can be seen per pages
            courseListLen = len(purchasedCourses) # get the length of the userList
            maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
            pageNum = int(pageNum)
            # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
            if pageNum < 0:
                return redirect("/purchasehistory/0")
            elif courseListLen > 0 and pageNum == 0:
                return redirect("/purchasehistory/1")
            elif pageNum > maxPages:
                redirectRoute = "/purchasehistory/" + str(maxPages)
                return redirect(redirectRoute)
            else:
                # pagination algorithm starts here
                courseList = purchasedCourses[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                pageNumForPagination = pageNum - 1 # minus for the paginate function
                paginatedCourseList = paginate(courseList, pageNumForPagination, maxItemsPerPage)
                purchasedCourses = paginate(purchasedCourses[::-1], pageNumForPagination, maxItemsPerPage)

                paginationList = get_pagination_button_list(pageNum, maxPages)

                previousPage = pageNum - 1
                nextPage = pageNum + 1

                db.close() # remember to close your shelve files!
                return render_template('users/loggedin/purchasehistory.html', courseID=courseID, courseType=courseType,courseList=paginatedCourseList, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, accType=accType, imagesrcPath=imagesrcPath,historyCheck=historyCheck)
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
@limiter.limit("30/second") # to prevent ddos attacks
def purchaseReview():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # userFound, accGoodStatus = validate_session_open_file(userSession)
        # if there's a need to retrieve the userKey for reading the user's account details, use the function below instead of the one above
        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)


        if userFound and accGoodStatus:
            # add in your own code here for your C,R,U,D operation and remember to close() it after manipulating the data
            imagesrcPath = retrieve_user_profile_pic(userKey)
            reviewID = userKey.get_reviewID()
            print("ReviewID exists?: ", reviewID)
            reviewDict = {}
            db = shelve.open("user", "c")

            try:
                reviewDict = db["Review"]
                createReview = Forms.CreateReviewText(request.form)
                if request.method == 'POST' and createReview.validate():
                    reviewID = createReview.review.data
                    reviewDict.append(reviewID)
                    reviewDict["Review"] = db
                    db.close()
                    dbCourse = {}
                    db = shelve.open("course","c")
                    try:
                        if "Courses" in db:
                            dbCourse = db["Courses"]

                        else:
                            db["Courses"] = dbCourse

                    except:
                        print("Error in retrieving course from course.db")
                        db.close()
                        return render_template('users/loggedin/purchasereview.html')

                else:
                    print("Review creation failed")
                    db.close()
                    return render_template('users/loggedin/purchasereview.html')

            except:
                print("Error in retrieving review from review.db")
                db.close()
                return render_template('users/loggedin/purchasereview.html')

            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/purchasereview.html', accType=accType, reviewDict=reviewDict, reviewID=reviewID, dbCourse=dbCourse, imagesrcPath=imagesrcPath)
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

"""End of Purchase Review by Royston"""

"""Purchase View by Royston"""

@app.route("/purchaseview")
@limiter.limit("30/second") # to prevent ddos attacks
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
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            imagesrcPath = retrieve_user_profile_pic(userKey)
            purchaseHistoryList = []
            showCourse = ""
            purchaseID = bool(userKey.get_purchaseID())
            print("PurchaseID exists?: ", purchaseID)

            if purchaseID == True:
                try:
                    historyDict = {}
                    dbCourse = shelve.open("course", "r")
                    historyDict = dbCourse[""]
                    for courseID in purchaseHistoryList(5):
                        history = dbCourse[courseID]

                        #id will be an integer

                        video = {id :
                            {historyDict : {"Title":history.get_title(),
                            "Description":history.get_description(),
                            "Thumbnail":history.get_thumbnail(),
                            "VideoCheck":history.get_courseType()["Video"],
                            "ZoomCheck":history.get_courseType()["Zoom"],
                            "Price":history.get_price(),
                            "Owner":history.get_owner()}
                            }
                        }
                    for i in purchaseHistoryList:
                        showCourse(video[i])

                    db.close()

                except:
                    print("Unable to open up course shelve")

            else:
                db.close()
                print("Nothing to view here.")
                return redirect(url_for("purchaseview"))

            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/purchaseview.html', accType=accType, imagesrcPath=imagesrcPath)
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


"""Template Redirect Shopping Cart by Jason because Opera is bad"""
@app.route("/shopping_cart", methods = ["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def shoppingCartDefault():
    return redirect("/shopping_cart/1")
"""End of Redirect Shopping Cart by Jason because Opera is bad"""


"""Template Shopping Cart by Wei Ren"""

@app.route("/shopping_cart/<int:pageNum>", methods = ["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def shoppingCart(pageNum):
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
        # userKey is the object (e.g. Student() or Teacher())
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            imagesrcPath = retrieve_user_profile_pic(userKey)
            removeCourseForm = Forms.RemoveShoppingCartCourse(request.form)
            checkoutCompleteForm = Forms.CheckoutComplete(request.form)
            shoppingCart = userKey.get_shoppingCart()
            print("Shopping Cart:", userKey.get_shoppingCart())

            # Remember to validate
            try:
                if "Courses" in db:
                    courseDict = db['Courses']
                else:
                    print("user.db has no course entries.")
                    courseDict = {}
            except:
                print("Error in retrieving Course from user.db")

            if request.method == "POST":
                if bool(checkoutCompleteForm.checkoutComplete.data):
                    print(checkoutCompleteForm.checkoutComplete.data)
                    # Remove courses from cart into purchases
                    for courseInfo in shoppingCart:
                        timing = checkoutCompleteForm.checkoutTiming.data.upper()               # U for Update
                        date = timing.split("T")[0]
                        time = timing.split("T")[1]

                        cost = courseDict[courseInfo[0]].get_price()
                        orderID = checkoutCompleteForm.checkoutOrderID.data
                        payerID = checkoutCompleteForm.checkoutPayerID.data

                        userKey.addCartToPurchases(courseInfo[0], courseInfo[1], date, time, cost, orderID, payerID)

                    print("Shopping Cart:", userKey.get_shoppingCart())
                    print("Purchases:", userKey.get_purchases())

                    userDict[userKey.get_user_id()] = userKey
                    db['Users'] = userDict

                    session["paymentComplete"] = True

                    return redirect(url_for('home'))

                elif removeCourseForm.validate():
                    courseID =  removeCourseForm.courseID.data
                    courseType = removeCourseForm.courseType.data

                    print("Removing course with Course ID, Type:", [courseID, courseType])      # D for Delete

                    for course in shoppingCart:
                        try:
                            if course == [courseID,courseType]:
                                shoppingCart.remove(course)
                                userDict[userKey.get_user_id] = userKey
                                db["Users"] = userDict
                                db.close()
                                break
                        except:
                            db.close()
                            print("Error. Shopping cart courses are missing values.")

                    return redirect("/shopping_cart/"+str(pageNum))

                else:
                    print("Error with form.")
                    return redirect(url_for('home'))

            # Render the page
            else:                                                                               # R for Read
                userKey.get_purchases()
                # Initialise lists for jinja2 tags
                ownerProfileImageList = []
                ownerUsernameList = []
                courseList = []
                courseTypeList = []
                subtotal = 0

                for courseInfo in shoppingCart:
                    # Getting course info
                    print("Course Info [ID, Type]:", courseInfo)
                    print(courseDict)
                    course = courseDict[courseInfo[0]]
                    courseList.append(course)

                    # Getting subtototal
                    subtotal += float(course.get_price())

                    # Getting course type chosen
                    courseTypeList.append(courseInfo[1])

                    # Getting course owner username
                    courseOwnerUsername = userDict[course.get_userID()].get_username()
                    ownerUsernameList.append(courseOwnerUsername)

                    # Getting course owner profile
                    userProfileImage = userDict[course.get_userID()].get_profile_image() # will return a filename, e.g. "0.png"
                    userProfileImagePath = construct_path(PROFILE_UPLOAD_PATH, userProfileImage)

                    # checking if the user have uploaded a profile image before and if the image file exists
                    imagesrcPath = get_user_profile_pic(courseOwnerUsername, userProfileImage, userProfileImagePath)

                    ownerProfileImageList.append(imagesrcPath)

                maxItemsPerPage = 5 # declare the number of items that can be seen per pages
                courseListLen = len(courseList) # get the length of the userList
                maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
                # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
                if pageNum < 0:
                    return redirect("/shopping_cart/0")
                elif courseListLen > 0 and pageNum == 0:
                    return redirect("/shopping_cart/1")
                elif pageNum > maxPages:
                    redirectRoute = "/shopping_cart/" + str(maxPages)
                    return redirect(redirectRoute)
                else:
                    # pagination algorithm starts here
                    courseList = courseList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                    pageNumForPagination = pageNum - 1 # minus for the paginate function
                    paginatedCourseList = paginate(courseList, pageNumForPagination, maxItemsPerPage)

                    previousPage = pageNum - 1
                    nextPage = pageNum + 1

                    ownerProfileImageList = paginate(ownerProfileImageList[::-1], pageNumForPagination, maxItemsPerPage)
                    ownerUsernameList = paginate(ownerUsernameList[::-1], pageNumForPagination, maxItemsPerPage)
                    courseTypeList = paginate(courseTypeList[::-1], pageNumForPagination, maxItemsPerPage)

                    paginationList = get_pagination_button_list(pageNum, maxPages)

                    db.close() # remember to close your shelve files!
                    return render_template('users/student/shopping_cart.html', nextPage = nextPage, previousPage = previousPage, individualCount=len(paginatedCourseList), courseList=paginatedCourseList, count=courseListLen, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, ownerUsernameList = ownerUsernameList, ownerProfileImageList = ownerProfileImageList, courseTypeList = courseTypeList, form = removeCourseForm, checkoutForm = checkoutCompleteForm, subtotal = "{:,.2f}".format(subtotal), accType=accType, imagesrcPath=imagesrcPath)

        else:
            db["Users"] = userDict  # Save changes
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # user is redirected to the home page, as they are not/no longer logged in
            return redirect(url_for("home"))

"""End of Template Shopping Cart by Wei Ren"""

"""Contact Us by Wei Ren"""

@app.route("/contact_us", methods = ["GET", "POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def contactUs():

    db = shelve.open("user", "c")
    # Remember to validate
    try:
        if "Contacts" in db:
            contactDict = db['Contacts']
        else:
            print("user.db has no contact entries.")
            contactDict = []
    except:
        print("Error in retrieving Contacts from user.db")

    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)


        if userFound and accGoodStanding:
            contactForm = Forms.ContactUs(request.form)
            if request.method == "POST" and contactForm.validate():

                contact = {"Name" : contactForm.name.data,
                           "Email" : contactForm.email.data,
                           "Subject" : contactForm.subject.data,
                           "Enquiry" : contactForm.enquiry.data}

                contactDict.append(contact)

                db["Contacts"] = contactDict
                db.close()

                return render_template('users/general/contact_us.html', accType=accType, imagesrcPath=imagesrcPath, success=True)
            elif accType == 'Admin':

                return render_template('admin/general/contact_us.html', accType="Admin")
            else:

                return render_template('users/general/contact_us.html', accType=accType, imagesrcPath=imagesrcPath, form = contactForm)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            contactForm = Forms.ContactUs(request.form)
            return render_template("users/general/contact_us.html", accType="Guest", form = contactForm)
    else:
        contactForm = Forms.ContactUs(request.form)
        return render_template("users/general/contact_us.html", accType="Guest", form = contactForm)

"""End of Contact Us by Wei Ren"""

"""Teacher's Channel Page by Clarence"""

@app.route("/teacher_page")
@limiter.limit("30/second") # to prevent ddos attacks
def function():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)
        # if there's a need to retrieve the userKey for reading the user's account details, use the function below instead of the one above

        if userFound and accGoodStatus:
            # add in your own code here for your C,R,U,D operation and remember to close() it after manipulating the data
            userProfileImage = userKey.get_profile_image() # will return a filename, e.g. "0.png"
            userProfileImagePath = construct_path(PROFILE_UPLOAD_PATH, userProfileImage)

            # checking if the user have uploaded a profile image before and if the image file exists
            imagesrcPath = get_user_profile_pic(userKey.get_username(), userProfileImage, userProfileImagePath)
            return render_template('users/teacher/teacher_page.html', accType=accType, imagesrcPath=imagesrcPath)
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

@app.route('/teacher_page/<teacherUID>', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
@limiter.limit("30/second") # to prevent ddos attacks
def teacherPage(teacherUID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            return render_template('users/admin/teacher_page.html')
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the login page or this function's html page
            redirect(url_for("teacher_page/teacherUID"))
            redirectURL = "/teacher_page/" + teacherUID
            return redirect(redirectURL)

    else:
        if "userSession" in session:
            userSession = session["userSession"]

            userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)


            if userFound and accGoodStatus:
                # add in your code here (if any)
                imagesrcPath = retrieve_user_profile_pic(userKey)
                """
                To Clarence, this template code is outdated, please use the new one for the general page
                - Jason
                """

                return render_template('users/teacher/teacher_page.html', accType=accType, teacherUID=teacherUID, imagesrcPath=imagesrcPath)
            else:
                print("User not found or is banned.")
                # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
                # return redirect(url_for("this function name here")) # determine if it make sense to redirect the user to the home page or to this page (if you determine that it should redirect to this function again, make sure to render a guest version of the page in the else statement below)
        else:
            # determine if it make sense to redirect the user to the home page or the login page or this function's html page
            return render_template("users/teacher/teacher_page.html")

"""End of Teacher's Channel Page by Clarence"""

"""Teacher's Courses Page by Clarence"""

@app.route('/<teacherUID>/teacher_courses', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
@limiter.limit("30/second") # to prevent ddos attacks
def teacherCourses(teacherUID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            return render_template('users/admin/teacher_courses.html')
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the login page or this function's html page
            return redirect("/" + teacherUID + "/teacher_courses")

    else:
        if "userSession" in session:
            userSession = session["userSession"]

            userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)


            if userFound and accGoodStatus:
                # add in your code here (if any)
                imagesrcPath = retrieve_user_profile_pic(userKey)
                """
                To Clarence, this template code is outdated, please use the new one for the general page
                - Jason
                """

                return render_template('users/teacher/teacher_courses.html', accType=accType, teacherUID=teacherUID, imagesrcPath=imagesrcPath)
            else:
                print("User not found or is banned.")
                # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
                # return redirect(url_for("this function name here")) # determine if it make sense to redirect the user to the home page or to this page (if you determine that it should redirect to this function again, make sure to render a guest version of the page in the else statement below)
        else:
            # determine if it make sense to redirect the user to the home page or the login page or this function's html page
            return render_template("users/teacher/teacher_courses.html")

"""End of Teacher's Courses Page by Clarence"""

"""General Pages"""

@app.route('/cookie_policy')
@limiter.limit("30/second") # to prevent ddos attacks
def cookiePolicy():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)

        if userFound and accGoodStanding:
            return render_template('users/general/cookie_policy.html', accType=accType, imagesrcPath=imagesrcPath)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/cookie_policy.html", accType="Guest")
    else:
        return render_template("users/general/cookie_policy.html", accType="Guest")

@app.route('/terms_and_conditions')
@limiter.limit("30/second") # to prevent ddos attacks
def termsAndConditions():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)

        if userFound and accGoodStanding:
            return render_template('users/general/terms_and_conditions.html', accType=accType, imagesrcPath=imagesrcPath)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/terms_and_conditions.html", accType="Guest")
    else:
        return render_template("users/general/terms_and_conditions.html", accType="Guest")

@app.route('/privacy_policy')
@limiter.limit("30/second") # to prevent ddos attacks
def privacyPolicy():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)

        if userFound and accGoodStanding:
            return render_template('users/general/privacy_policy.html', accType=accType, imagesrcPath=imagesrcPath)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/privacy_policy.html", accType="Guest")
    else:
        return render_template("users/general/privacy_policy.html", accType="Guest")

@app.route("/faq")
@limiter.limit("30/second") # to prevent ddos attacks
def faq():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)

        if userFound and accGoodStanding:
            return render_template('users/general/faq.html', accType=accType, imagesrcPath=imagesrcPath)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/faq.html", accType="Guest")
    else:
        return render_template("users/general/faq.html", accType="Guest")

"""End of Genral Pages"""

# 8 template app.route("") for you guys :prayge:
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
@limiter.limit("30/second") # to prevent ddos attacks
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
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            imagesrcPath = retrieve_user_profile_pic(userKey)

            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html', accType=accType, imagesrcPath=imagesrcPath)
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
@limiter.limit("30/second") # to prevent ddos attacks
def function():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)


        if userFound and accGoodStatus:
            # add in your own code here for your C,R,U,D operation and remember to close() it after manipulating the data
            imagesrcPath = retrieve_user_profile_pic(userKey)

            return render_template('users/loggedin/page.html', accType=accType, imagesrcPath=imagesrcPath)
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

  - Only READING from shelve (user data)

  - Webpage will not have admin view
  - Use case: User pages (user_profile.html, etc)
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route('', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
@limiter.limit("30/second") # to prevent ddos attacks
def insertName():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)


        if userFound and accGoodStatus:
            # add in your code below
            imagesrcPath = retrieve_user_profile_pic(userKey)
            return render_template('users/loggedin/page.html', accType=accType, imagesrcPath=imagesrcPath)
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
@limiter.limit("30/second") # to prevent ddos attacks
def insertName():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)

        if userFound and accGoodStanding:
            return render_template('users/general/page.html', accType=accType, imagesrcPath=imagesrcPath)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/page.html", accType="Guest")
    else:
        return render_template("users/general/page.html", accType="Guest")

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - User session validity check needed (Logged in?)
  - User banned?
  - Is user admin?

  - Using CUSTOM shelve or reading user info

  - Webpage will have admin and user view
  e.g. General pages (home page) that check whether user/admin is logged in.
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route('', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
@limiter.limit("30/second") # to prevent ddos attacks
def insertName():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)

        if userFound and accGoodStanding:
            imagesrcPath = retrieve_user_profile_pic(userKey)
            # add in your CRUD or other code
            return render_template('users/general/page.html', accType=accType, imagesrcPath=imagesrcPath)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/page.html", accType="Guest")
    else:
        return render_template("users/general/page.html", accType="Guest")

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
@limiter.limit("30/second") # to prevent ddos attacks
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
@limiter.limit("30/second") # to prevent ddos attacks
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

  - Only READING from shelve (admin data)

  - Webpage will not have user view
  - Use case: Admin pages
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
@limiter.limit("30/second") # to prevent ddos attacks
def function():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)

        userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)

        if userFound and accActive:
            # add in your code here

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

"""Custom Error Pages"""

# Bad Request
@app.errorhandler(400)
def error400(e):
    return render_template("errors/401.html"), 400

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

# Method Not Allowed
@app.errorhandler(405)
def error405(e):
    return render_template("errors/405.html"), 405

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

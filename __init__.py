from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import shelve, Forms, os
import Student, Teacher, Admin
from Security import PasswordManager, Sanitise
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
from PIL import Image

"""Useful Functions"""

# use this function if you want to validate and get the userKey to manipulate the data in the user shelve files (provided you have already opened the user shelve files previously)
def get_key_and_validate(userSession, userDict):
    userKey = ""
    userFound = False
    print("ID in session:", userSession)
    for key in userDict:
        print("retrieving")
        userIDShelveData = userDict[key].get_user_id()
        print("ID in database:", userIDShelveData)
        if userSession == userIDShelveData:
            print("Verdict: User ID Matched.")
            userKey = userDict[key]
            userFound = True
            return userKey, userFound
    print("Verdict: User ID not found.")
    return userKey, userFound

# Use this function if you want to validate the session and get the userKey but not manipulating the data in the user shelve files (usually this will be used for reading the user account data or other data relevant to the user)
def validate_session_get_userKey_open_file(userSession):
    userDict = {}
    # Retrieving data from shelve to check validity of the session and to check if the files has been deleted
    try:
        db = shelve.open("user", "r")
        userDict = db['Users']
        print("File found.")
        db.close()
    except:
        print("File could not be found.")
        # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the guest homepage
        session.clear()
        return redirect(url_for("home"))
        
    userKey = ""
    userFound = False
    print("ID in session:", userSession)
    for key in userDict:
        print("retrieving")
        userIDShelveData = userDict[key].get_user_id()
        print("ID in database:", userIDShelveData)
        if userSession == userIDShelveData:
            print("Verdict: User ID Matched.")
            userKey = userDict[key]
            userFound = True
            return userKey, userFound
    print("Verdict: User ID not found.")
    return userKey, userFound


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

# use the function below if you just want to validate the session but there is no need to manipulate the data in the user shelve data files and also assuming that the user must be logged in, meaning the user shelve data must be present in the directory
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
        session.clear()
        return redirect(url_for("home"))
        
    userFound = False
    print("User ID in session:", userSession)
    for key in userDict:
        print("retrieving")
        userIDShelveData = userDict[key].get_user_id()
        print("User ID in database:", userIDShelveData)
        if userSession == userIDShelveData:
            print("Verdict: User ID Matched.")
            userFound = True
            return userFound # will be true if found
    return userFound # will be false as it could not find the user based on the user ID

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

# use this function to check for the allowed extension of images when uploading the image to the web app's server
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

"""End of Useful Functions"""

"""Web app configurations"""

# general Flask configurations
app = Flask(__name__)
app.secret_key = "a secret key" # for demonstration purposes, if deployed, change it to something more secure

# for uploading images to the web app's server configurations
UPLOAD_PATH = 'static/images/user'
ALLOWED_EXTENSIONS = {"png"}

# Flask limiter configuration
limiter = Limiter(app, key_func=get_remote_address)

"""End of Web app configurations"""

"""General pages"""

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

    if "userSession" in session:
        userSession = session["userSession"]

        userFound = validate_session_open_file(userSession)

        if userFound:
            return render_template('users/loggedin/user_home.html')
        else:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return render_template('users/guest/guest_home.html')
    else:
        return render_template('users/guest/guest_home.html', recentlyLoggedOut=recentlyLoggedOut)

"""End of General pages"""

"""User login and logout"""

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("2/second") # to prevent attackers from trying to crack passwords by sending too many automated requests from their ip address
def userLogin():
    if "userSession" not in session:
        create_login_form = Forms.CreateLoginForm(request.form)
        if request.method == "POST" and create_login_form.validate():
            emailInput = Sanitise(create_login_form.email.data.lower())
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

                password_matched = PasswordManager().verify_password(passwordShelveData, passwordInput)

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

                # setting the user session based on the user's user ID
                userID = email_key.get_user_id()
                session["userSession"] = userID

                return redirect(url_for("userProfile"))
            else:
                print("Email in database:", emailShelveData)
                print("Email Input:", emailInput)
                print("Password in database:", passwordShelveData)
                print("Password Input:", passwordInput)
                return render_template('users/guest/login.html', form=create_login_form, failedAttempt=True)
        else:
            return render_template('users/guest/login.html', form=create_login_form)
    else:
        return redirect(url_for("home"))

@app.route('/logout')
def logout():
    session.pop("userSession", None)
    
    # sending a session data so that when it redirects the user to the homepage, jinja2 will render out a logout alert
    session["recentlyLoggedOut"] = True

    return redirect(url_for("home"))

"""End of User login and logout"""

"""Student signup process"""
@app.route('/signup', methods=['GET', 'POST'])
def userSignUp():
    if "userSession" not in session:
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

            emailInput = Sanitise(create_signup_form.email.data.lower())
            usernameInput = Sanitise(create_signup_form.username.data)

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
                print("Error in retrieving Users from user.db")

            # Checking duplicates for email and username
            email_duplicates = check_duplicates(emailInput, userDict, "email")
            username_duplicates = check_duplicates(usernameInput, userDict, "username")
            
            # If there were no duplicates and passwords entered were the same, create a new user
            if (pwd_were_not_matched == False) and (email_duplicates == False) and (username_duplicates == False):
                hashedPwd = PasswordManager().hash_password(passwordInput)
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
            return render_template('users/guest/signup.html', form=create_signup_form)    
    else:
        return redirect(url_for("home"))

"""End of Student signup process"""

"""Teacher's signup process"""

@app.route('/teacher_signup', methods=['GET', 'POST'])
def teacherSignUp():
    if "userSession" not in session:
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

            emailInput = Sanitise(create_teacher_sign_up_form.email.data.lower())
            usernameInput = Sanitise(create_teacher_sign_up_form.username.data)

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
                print("Error in retrieving Users from user.db")

            # Checking duplicates for email and username
            email_duplicates = check_duplicates(emailInput, userDict, "email")
            username_duplicates = check_duplicates(usernameInput, userDict, "username")

            if (pwd_were_not_matched == False) and (email_duplicates == False) and (username_duplicates == False):
                print("User info validated.")
                hashedPwd = PasswordManager().hash_password(passwordInput)
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
            return render_template('users/guest/teacher_signup.html', form=create_teacher_sign_up_form) 
    else:
        return redirect(url_for("home"))

@app.route('/sign_up_payment', methods=['GET', 'POST'])
def signUpPayment():
    if "userSession" in session:
        userSession = session["userSession"]
        if "teacher" in session:
            teacherID = session["teacher"]
            print(teacherID)

            create_teacher_payment_form = Forms.CreateTeacherPayment(request.form)
            if request.method == 'POST' and create_teacher_payment_form.validate():
                userFound = False # declaring this variable to prevent unboundLocalError

                # Retrieving data from shelve and to set the teacher's payment method info data
                userDict = {}
                db = shelve.open("user", "c")
                try:
                    if 'Users' in db:
                        # there must be user data in the user shelve files as this is the 2nd part of the teacher signup process which would have created the teacher acc and store in the user shelve files previously
                        userDict = db['Users']
                    else:
                        print("No user data in user shelve files.")
                        # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                        session.clear()
                        return redirect(url_for("home"))
                except:
                    print("Error in retrieving Users from user.db")

                # retrieving the object from the shelve based on the user's email
                teacherKey, userFound = get_key_and_validate(teacherID, userDict)
                
                if userFound == False:
                    db.close()
                    print("User not found")
                    # if user is not found for some reason, it will delete any session and redirect the user to the homepage
                    session.clear()
                    return redirect(url_for("home"))
                else:
                    if userSession == teacherID:
                        # further checking to see if the user ID in the session is equal to the teacher ID session from the teacher sign up process

                        cardName = Sanitise(create_teacher_payment_form.cardName.data)
                        cardNo = create_teacher_payment_form.cardNo.data
                        cardExpiry = str(create_teacher_payment_form.cardExpiry.data)
                        cardCVV = create_teacher_payment_form.cardCVV.data
                        cardType = create_teacher_payment_form.cardType.data

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
                        return redirect(url_for("home"))
                    else:
                        db.close()
                        # clear the teacher session if the logged in user somehow have a teacher session and submits the form, it will then redirect them to the home page
                        session.pop("teacher", None)
                        return redirect(url_for("home"))
            else:
                return render_template('users/guest/teacher_signup_payment.html', form=create_teacher_payment_form)
        else:
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))

"""End of Teacher's login/signup process"""

"""User Profile Settings"""

@app.route('/user_profile', methods=["GET","POST"])
def userProfile():
    if "userSession" in session:
        session.pop("teacher", None) # deleting data from the session if the user chooses to skip adding a payment method from the teacher signup process

        userSession = session["userSession"]
        userKey, userFound = validate_session_get_userKey_open_file(userSession)
        if userFound:
            if request.method == "POST":
                if "profileImage" not in request.files:
                    print("No file sent.")
                    return redirect(url_for("userProfile"))

                file = request.files["profileImage"]
                filename = file.filename

                if filename != "":
                    if file and allowed_file(filename):
                        # will only accept .png
                        print("File extension accepted.")

                        #  “never trust user input” principle, all submitted form data can be forged, and filenames can be dangerous.
                        # hence, secure_filename() is used because it will return a secure version of the filepath so that when constructing a file path to store the image, the server OS will be able to safely store the image 
                        filename = secure_filename(filename) 
                        
                        # constructing the file path so that the it will know where to store the image
                        filePath = os.path.join(app.root_path, UPLOAD_PATH, filename)
                        userID = str(userKey.get_user_id()) + ".png"
                        newFilePath = os.path.join(app.root_path, UPLOAD_PATH, userID)

                        # using Path from pathlib to check if the file path of userID.png (e.g. 0.png) already exist.
                        # if file already exist, it will remove and save the image and rename it to userID.png (e.g. 0.png) which in a way is overwriting the existing image
                        # else it will just save normally and rename it to userID.png (e.g. 0.png)
                        if Path(newFilePath).is_file():
                            print("Removing existing image.")
                            os.remove(newFilePath)
                            file.save(filePath)
                            os.rename(filePath, newFilePath)
                            print("File renamed to", newFilePath, "and has been overwrited.")
                        else:
                            print("Saving image file.")
                            file.save(filePath)
                            os.rename(filePath, newFilePath)
                            print("File renamed to", newFilePath, "and has been saved.")

                        # resizing the image to a 1:1 ratio that was recently uploaded and stored in the server directory
                        profileImage = Image.open(newFilePath)
                        resizedImage = profileImage.resize((500, 500))
                        os.remove(newFilePath)
                        resizedImage.save(newFilePath)

                        session["imageChanged"] = True
                        return redirect(url_for("userProfile"))
                    else:
                        print("Image extension not allowed.")
                        session["imageFailed"] = True
                        return redirect(url_for("userProfile"))
                else:
                    print("No selected file/the user sent a empty file without a filename")
                    return redirect(url_for("userProfile"))
            else:
                userUsername = userKey.get_username()
                userEmail = userKey.get_email()
                userAccType = userKey.get_acc_type()

                # checking if the user have uploaded a profile image before
                imageName = str(userKey.get_user_id()) + ".png"
                imageFilePath = os.path.join(app.root_path, UPLOAD_PATH, imageName)
                if Path(imageFilePath).is_file():
                    imagesrcPath = "static/images/user/" + imageName
                else:
                    imagesrcPath = "static/images/user/default.png"

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
                
                return render_template('users/loggedin/user_profile.html', username=userUsername, email=userEmail, accType = userAccType, emailChanged=emailChanged, usernameChanged=usernameChanged, passwordChanged=passwordChanged, imageFailed=imageFailed, imageChanged=imageChanged, imagesrcPath=imagesrcPath)
        else:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        return redirect(url_for("userLogin"))

@app.route("/change_username", methods=["GET","POST"])
def updateUsername():
    if "userSession" in session:
        create_update_username_form = Forms.CreateChangeUsername(request.form)
        if request.method == "POST" and create_update_username_form.validate():
            userSession = session["userSession"]

            # declaring userKey, userFound, username_duplicates, and sameUsername variable to prevent unboundLocalError
            userKey = ""
            userFound = False
            username_duplicates = True
            sameUsername = False

            # Retrieving data from shelve and to write the data into it later
            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    print("User data in shelve is empty.")
                    session.clear() 
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                print("Error in retrieving Users from user.db")

            # retrieving the object from the shelve based on the user's user ID
            userKey, userFound = get_key_and_validate(userSession, userDict)
            
            if userFound == False:
                print("User not found")
                # if user is not found for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
            else:
                updatedUsername = Sanitise(create_update_username_form.updateUsername.data)
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
                        return render_template('users/loggedin/change_username.html', form=create_update_username_form, username_duplicates=username_duplicates)
                else:
                    print("Update username input same as user's current username")
                    return render_template('users/loggedin/change_username.html', form=create_update_username_form, sameUsername=sameUsername)
        else:
            return render_template('users/loggedin/change_username.html', form=create_update_username_form)
    else:
        return redirect(url_for("userLogin"))

@app.route("/change_email", methods=["GET","POST"])
def updateEmail():
    if "userSession" in session:
        create_update_email_form = Forms.CreateChangeEmail(request.form)
        if request.method == "POST" and create_update_email_form.validate():
            userSession = session["userSession"]

            # declaring userKey, userFound, email_duplicates, sameEmail variable to prevent unboundLocalError
            userKey = ""
            userFound = False
            email_duplicates = True
            sameEmail = False

            # Retrieving data from shelve and to write the data into it later
            userDict = {}
            db = shelve.open("user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    print("User data in shelve is empty.")
                    session.clear() 
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                print("Error in retrieving Users from user.db")

            # retrieving the object based on the shelve files using the user's user ID
            userKey, userFound = get_key_and_validate(userSession, userDict)
            
            if userFound == False:
                print("User not found")
                # if user is not found for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
            else:
                updatedEmail = Sanitise(create_update_email_form.updateEmail.data.lower())
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
                        return render_template('users/loggedin/change_email.html', form=create_update_email_form, email_duplicates=email_duplicates)
                else:
                    db.close()
                    print("User updated email input is the same as their current email")
                    return render_template('users/loggedin/change_email.html', form=create_update_email_form, sameEmail=sameEmail)
        else:
            return render_template('users/loggedin/change_email.html', form=create_update_email_form)
    else:
        return redirect(url_for("userLogin"))

@app.route("/change_password", methods=["GET","POST"])
def updatePassword():
    if "userSession" in session:
        create_update_password_form = Forms.CreateChangePasswordForm(request.form)
        if request.method == "POST" and create_update_password_form.validate():
            userSession = session["userSession"]

            # declaring userKey, userFound, password_not_matched, and errorMessage variable to prevent unboundLocalError
            userKey = ""
            userFound = False
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
                    print("User data in shelve is empty.")
                    session.clear() 
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                print("Error in retrieving Users from user.db")

            # retrieving the object based on the shelve files using the user's user ID
            userKey, userFound = get_key_and_validate(userSession, userDict)
            
            if userFound == False:
                print("User not found")
                # if user is not found for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
            else:
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

                password_verification = PasswordManager().verify_password(currentStoredPassword, currentPassword)
                
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
                    # updating password of the user
                    hashedPwd = PasswordManager().hash_password(updatedPassword)
                    userKey.set_password(hashedPwd)
                    db['Users'] = userDict
                    print("Password updated")
                    db.close()

                    # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of password
                    session["password_changed"] = True
                    return redirect(url_for("userProfile"))
        else:
            return render_template('users/loggedin/change_password.html', form=create_update_password_form)
    else:
        return redirect(url_for("userLogin"))

"""End of User Profile Settings"""

"""User payment method settings"""

@app.route('/payment_method', methods=["GET","POST"])
def userPayment():
    if "userSession" in session:
        userSession = session["userSession"]

        # declaring userKey and userFound variable to prevent unboundLocalError
        userKey = ""
        userFound = False

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                print("User data in shelve is empty.")
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                session.clear() 
                return redirect(url_for("home"))
        except:
            print("Error in retrieving Users from user.db")

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound = get_key_and_validate(userSession, userDict)
        
        if userFound == False:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
        else:
            cardExist = bool(userKey.get_card_name())
            print("Card exist?:", cardExist)
            
            if cardExist == False:
                print("Entered if loop")
                create_add_payment_form = Forms.CreateAddPaymentForm(request.form)
                if request.method == "POST" and create_add_payment_form.validate():
                    print("POST request sent and form entries validated")
                    cardName = Sanitise(create_add_payment_form.cardName.data)
                    cardNo = create_add_payment_form.cardNo.data
                    cardType = create_add_payment_form.cardType.data
                    cardExpiry = str(create_add_payment_form.cardExpiry.data)
                    cardCVV = create_add_payment_form.cardCVV.data

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

                    return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form, cardDeleted=cardDeleted)
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

                return render_template('users/loggedin/user_existing_payment.html', cardName=cardName, cardNo=cardNo, cardExpiry=cardExpiry, cardType=cardType, cardUpdated=cardUpdated, cardAdded=cardAdded)
    else:
        return redirect(url_for("userLogin"))

@app.route('/edit_payment', methods=["GET","POST"])
def userEditPayment():
    if "userSession" in session:
        # checking if the user has a credit card in the shelve database to prevent directory traversal which may break the web app

        userSession = session["userSession"]

        # declaring userKey and userFound variable to prevent unboundLocalError
        userKey = ""
        userFound = False

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                print("User data in shelve is empty.")
                session.clear() 
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            print("Error in retrieving Users from user.db")

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound = get_key_and_validate(userSession, userDict)
        
        if userFound == False:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
        else:
            cardExist = bool(userKey.get_card_name())
            print("Card exist?:", cardExist)
            cardName = userKey.get_card_name()

            cardNo = str(userKey.get_card_no())
            print("Original card number:", cardNo)
            cardNo = cardNo[-5:-1] # string slicing to get the last 4 digits of the credit card number
            print("Sliced card number:", cardNo)

            cardType = userKey.get_card_type()
            if cardExist:
                create_edit_payment_form = Forms.CreateEditPaymentForm(request.form)
                if request.method == "POST" and create_edit_payment_form.validate():
                    cardCVV = create_edit_payment_form.cardCVV.data
                    cardExpiry = str(create_edit_payment_form.cardExpiry.data)

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
                    db.close()
                    return render_template('users/loggedin/user_edit_payment.html', form=create_edit_payment_form, cardName=cardName, cardNo=cardNo, cardType=cardType)
            else:
                db.close()
                return redirect(url_for("user_profile"))
    else:
        return redirect(url_for("userLogin"))

@app.route('/delete_card', methods=['POST'])
def deleteCard():
    if "userSession" in session:
        userSession = session["userSession"]

        # declaring userKey and userFound variable to prevent unboundLocalError
        userKey = ""
        userFound = False

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            print("Error in retrieving Users from user.db")

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound = get_key_and_validate(userSession, userDict)
        
        if userFound == False:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
        else:
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
                return redirect(url_for("user_profile"))
    else:
        return redirect(url_for("userLogin"))

"""End of User payment method settings"""

"""Search Function"""

@app.route("/search")
def search():
    if "userSession" in session:
        userSession = session["userSession"]

        # declaring userKey and userFound variable to prevent unboundLocalError
        userKey = ""
        userFound = False

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            print("Error in retrieving Users from user.db")

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound = get_key_and_validate(userSession, userDict)

        if userFound == False:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
        else:
            # insert your C,R,U,D operation here to deal with the user shelve data files

            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
    else:
        return redirect(url_for("home"))

""""End of Search Function"""

"""Purchase History"""

@app.route("/purchasehistory")
def purchaseHistory():
    if "userSession" in session:
        userSession = session["userSession"]

        # declaring userKey and userFound variable to prevent unboundLocalError
        userKey = ""
        userFound = False

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            print("Error in retrieving Users from user.db")

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound = get_key_and_validate(userSession, userDict)

        if userFound == False:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
        else:
            # insert your C,R,U,D operation here to deal with the user shelve data files

            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
    else:
        return redirect(url_for("userLogin"))

"""End of Purchase History"""

"""Purchase Review"""

@app.route("/purchasereview")
def purchaseReview():
    if "userSession" in session:
        userSession = session["userSession"]

        # declaring userKey and userFound variable to prevent unboundLocalError
        userKey = ""
        userFound = False

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            print("Error in retrieving Users from user.db")

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound = get_key_and_validate(userSession, userDict)

        if userFound == False:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
        else:
            # insert your C,R,U,D operation here to deal with the user shelve data files

            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
    else:
        return redirect(url_for("userLogin"))

"""End of Purchase Review"""

"""Purchase View"""

@app.route("/purchaseview")
def purchaseView():
    if "userSession" in session:
        userSession = session["userSession"]

        # declaring userKey and userFound variable to prevent unboundLocalError
        userKey = ""
        userFound = False

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            print("Error in retrieving Users from user.db")

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound = get_key_and_validate(userSession, userDict)

        if userFound == False:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
        else:
            # insert your C,R,U,D operation here to deal with the user shelve data files

            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
    else:
        return redirect(url_for("userLogin"))

"""End of Purchase View"""

"""Teacher Cashout System"""

@app.route("/teacher_cashout")
def teacherCashOut():
    if "userSession" in session:
        userSession = session["userSession"]

        # declaring userKey and userFound variable to prevent unboundLocalError
        userKey = ""
        userFound = False

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            print("Error in retrieving Users from user.db")

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound = get_key_and_validate(userSession, userDict)

        if userFound == False:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
        else:
            # insert your C,R,U,D operation here to deal with the user shelve data files

            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
    else:
        return redirect(url_for("userLogin"))

"""End of Teacher Cashout System"""


# 4 template app.route("") for you guys :prayge:

'''
# below will be the template for your app.route("") if there's a need to check validity of the user session if the user is logged in or not but you are also dealing with shelve with regards to the USER shelve files, meaning you are dealing with shelve.open("user", "C") ONLY
"""Template app.route(") (use this when adding a new app route)"""

@app.route("/")
def function():
    if "userSession" in session:
        userSession = session["userSession"]

        # declaring userKey and userFound variable to prevent unboundLocalError
        userKey = ""
        userFound = False

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            print("Error in retrieving Users from user.db")

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound = get_key_and_validate(userSession, userDict)
        
        if userFound == False:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
        else:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            
            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html')
    else:
        # determine if it make sense to redirect the user to the home page or the login page
        return redirect(url_for("home"))
        # return redirect(url_for("userLogin"))

"""End of Template app.route"""
'''

'''
# below will be the template for your app.route("") if there's a need to check validity of the user session if the user is logged in or not but you are also dealing with shelve with regards to your own CUSTOM shelve files, meaning you are dealing with shelve.open("insert your shelve file name", "C")
"""Template app.route(") (use this when adding a new app route)"""

@app.route("/")
def function():
    if "userSession" in session:
        userSession = session["userSession"]

        userFound = validate_session_open_file(userSession)
        
        if userFound == True:
            # add in your own code here for your C,R,U,D operation and remember to close() it after manipulating the data

            return render_template('users/loggedin/page.html')
        else:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        # determine if it make sense to redirect the user to the home page or the login page
        return redirect(url_for("home"))
        # return redirect(url_for("userLogin"))

"""End of Template app.route"""
'''

'''
# below will be the template for your app.route("") if there's a need to check validity of the user session if the user is logged in or not but not dealing with shelve
# e.g. for general pages such as about_us.html, etc. 
"""Template app.route(") (use this when adding a new app route)"""

@app.route('', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
def insertName():
    if "userSession" in session:
        userSession = session["userSession"]

        userFound = validate_session_open_file(userSession)

        if userFound == True:
            # add in your code here
            
            return render_template('users/loggedin/page.html')
        else:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        # determine if it make sense to redirect the user to the home page or the login page
        return redirect(url_for("home"))
        # return redirect(url_for("userLogin"))

"""End of Template app.route"""
'''

'''
# below will be the template for your app.route("") if there's a need to check validity of the user session if the user is logged in or not but not dealing with shelve and you need to read information from the user's account data
# e.g. for user pages such as user_profile.html, etc. 
"""Template app.route(") (use this when adding a new app route)"""

@app.route('', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
def insertName():
    if "userSession" in session:
        userSession = session["userSession"]

        userKey, userFound = validate_session_get_userKey_open_file(userSession)

        if userFound == True:
            # add in your code below

            return render_template('users/loggedin/page.html')
        else:
            print("User not found")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        # determine if it make sense to redirect the user to the home page or the login page
        return redirect(url_for("home"))
        # return redirect(url_for("userLogin"))

"""End of Template app.route"""
'''


"""Custom Error Pages"""

@app.errorhandler(401)
def error401(error):
    return render_template("errors/401.html"), 401

@app.errorhandler(403)
def error403(error):
    return render_template("errors/403.html"), 403

@app.errorhandler(404)
def error404(error):
    return render_template("errors/404.html"), 404

@app.errorhandler(429)
def error429(error):
    return render_template("errors/429.html"), 429

@app.errorhandler(500)
def error500(error):
    return render_template("errors/500.html"), 500

@app.errorhandler(502)
def error502(error):
    return render_template("errors/502.html"), 502

@app.errorhandler(503)
def error503(error):
    return render_template("errors/503.html"), 503

"""End of Custom Error Pages"""

if __name__ == '__main__':
    app.run(debug=True) # debug=True for development purposes

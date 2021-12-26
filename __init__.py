from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import shelve, Forms, os
import Student, Teacher, Admin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


"""General"""

app = Flask(__name__)
UPLOAD_PATH = 'static/images/user'
ALLOWED_EXTENSIONS = {"png"}
app.config['UPLOAD_PATH'] = "uploads"
app.config['MAX_CONTENT_LENGTH'] = 5120 * 5120
limiter = Limiter(app, key_func=get_remote_address)

app.secret_key = "a secret key" # for demonstration purposes, if deployed, change it to something more secure

@app.route('/', methods=["GET","POST"])
def home():
    if "userSession" in session:
        return render_template('users/loggedin/user_home.html')
    else:
        return render_template('users/guest/guest_home.html')

"""End of General"""

"""User login and logout"""

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("2/second") # to prevent attackers from trying to crack passwords by sending too many automated requests from their ip address
def userLogin():
    if "userSession" not in session:
        create_login_form = Forms.CreateLoginForm(request.form)
        if request.method == "POST" and create_login_form.validate():
            emailInput = create_login_form.email.data.lower()
            passwordInput = create_login_form.password.data
            try:
                userDict = {}
                db = shelve.open("user", "r")
                userDict = db['Users']
                print("File found.")
            except:
                print("File could not be found.")
                # since the shelve files could not be found, it will create a placeholder/empty shelve files
                userDict = {}
                db = shelve.open("user", "c")
                db["Users"] = userDict

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
                if passwordInput == passwordShelveData:
                    password_matched = True
                else:
                    print("Password incorrect.")
                    
            if email_found and password_matched:
                print("User validated...")
                print("Email in database:", emailShelveData)
                print("Email Input:", emailInput)
                print("Password in database:", passwordShelveData)
                print("Password Input:", passwordInput)
                print("Account type:", email_key.get_acc_type())
                db.close()

                username = email_key.get_username()
                session["userSession"] = username

                return redirect(url_for("userProfile"))
            else:
                print("Email in database:", emailShelveData)
                print("Email Input:", emailInput)
                print("Password in database:", passwordShelveData)
                print("Password Input:", passwordInput)
                db.close()
                return render_template('users/guest/login.html', form=create_login_form, failedAttempt=True)
        else:
            return render_template('users/guest/login.html', form=create_login_form)
    else:
        return redirect(url_for("home"))

@app.route('/logout')
def logout():
    session.pop("userSession", None)
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

            emailInput = create_signup_form.email.data.lower()
            usernameInput = create_signup_form.username.data

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

            # Checking duplicates for email
            for key in userDict:
                print("retrieving")
                emailShelveData = userDict[key].get_email()
                if emailInput == emailShelveData:
                    print("Email in database:", emailShelveData)
                    print("Email input:", emailInput)
                    print("Verdict: User email already exists.")
                    email_duplicates = True
                    break
                else:
                    print("Email in database:", emailShelveData)
                    print("Email input:", emailInput)
                    print("Verdict: User email is unique.")
                    email_duplicates = False
            
            # checking duplicates for username
            for key in userDict:
                print("retrieving")
                usernameShelveData = userDict[key].get_username()
                if usernameInput == usernameShelveData:
                    print("Username in database:", usernameShelveData)
                    print("Username input:", usernameInput)
                    print("Verdict: Username already taken.")
                    username_duplicates = True
                    break
                else:
                    print("Username in database:", usernameShelveData)
                    print("Username input:", usernameInput)
                    print("Verdict: Username is unique.")
                    username_duplicates = False
            
            # If there were no duplicates and passwords entered were the same, create a new user
            if (pwd_were_not_matched == False) and (email_duplicates == False) and (username_duplicates == False):

                user = Student.Student(usernameInput, emailInput, passwordInput)
                print(user)

                userDict[user.get_username()] = user
                db["Users"] = userDict
                
                print(userDict)

                db.close()
                print("User added.")
                session["userSession"] = usernameInput
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

            emailInput = create_teacher_sign_up_form.email.data.lower()
            usernameInput = create_teacher_sign_up_form.username.data

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

            # Checking duplicates for email
            for key in userDict:
                print("retrieving")
                emailShelveData = userDict[key].get_email()
                if emailInput == emailShelveData:
                    print("Email in database:", emailShelveData)
                    print("Email input:", emailInput)
                    print("Verdict: User email already exists.")
                    email_duplicates = True
                    break
                else:
                    print("Email in database:", emailShelveData)
                    print("Email input:", emailInput)
                    print("Verdict: User email is unique.")
                    email_duplicates = False
            
            # checking duplicates for username
            for key in userDict:
                print("retrieving")
                usernameShelveData = userDict[key].get_username()
                if usernameInput == usernameShelveData:
                    print("Username in database:", usernameShelveData)
                    print("Username input:", usernameInput)
                    print("Verdict: Username already taken.")
                    username_duplicates = True
                    break
                else:
                    print("Username in database:", usernameShelveData)
                    print("Username input:", usernameInput)
                    print("Verdict: Username is unique.")
                    username_duplicates = False

            if (pwd_were_not_matched == False) and (email_duplicates == False) and (username_duplicates == False):
                print("User info validated.")
                user = Teacher.Teacher(usernameInput, emailInput, passwordInput)
                print(user)

                userDict[user.get_username()] = user
                db["Users"] = userDict
                
                session["teacher"] = emailInput # to send the email to the add payment form as part of the teacher sign up process and for setting the payment method information into the teacher object

                print(userDict)
                print("Teacher added and payment method added.")

                db.close()
                
                session["userSession"] = usernameInput

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
        if "teacher" in session:
            teacherEmail = session["teacher"]

            print(teacherEmail)
            create_teacher_payment_form = Forms.CreateTeacherPayment(request.form)
            if request.method == 'POST' and create_teacher_payment_form.validate():
                cardName = create_teacher_payment_form.cardName.data
                cardNo = create_teacher_payment_form.cardNo.data
                cardExpiry = create_teacher_payment_form.cardExpiry.data
                cardCVV = create_teacher_payment_form.cardCVV.data
                cardType = create_teacher_payment_form.cardType.data

                # Retrieving data from shelve
                userDict = {}
                db = shelve.open("user", "c")
                try:
                    userDict = {}
                    db = shelve.open("user", "r")
                    userDict = db['Users']
                    print("File found.")
                except:
                    print("File could not be found.")
                    # since the file could not be found either due to the admin deleting or something else, it will clear any session and redirect the user to the homepage
                    session.clear()
                    return redirect(url_for("home"))

                # retrieving the object from the shelve based on the user's email
                for key in userDict:
                    print("retrieving")
                    emailShelveData = userDict[key].get_email()
                    if teacherEmail == emailShelveData:
                        print("Email in database:", emailShelveData)
                        print("Email input:", teacherEmail)
                        print("Verdict: User email found.")
                        teacherKey = userDict[key]
                        break
                    else:
                        print("Error, teacher's email not found.")

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
        usernameSession = session["userSession"]
        create_image_upload_form = Forms.CreateImageUploadForm(request.form)
        if request.method == "POST" and create_image_upload_form.validate():
            return redirect(url_for("home"))
        else:
            # declaring userKey variable to prevent unboundLocalError
            userKey = ""

            # Retrieving data from shelve
            try:
                userDict = {}
                db = shelve.open("user", "r")
                userDict = db['Users']
                print("File found.")
            except:
                print("File could not be found.")
                # since the file could not be found either due to the admin deleting or something else, it will clear any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))


            # retrieving the object from the shelve based on the user's username
            print("Username session:", usernameSession)
            for key in userDict:
                print("retrieving")
                usernameShelveData = userDict[key].get_username()
                print("Username in database:", usernameShelveData)
                
                if usernameSession == usernameShelveData:
                    print("Verdict: Username found.")
                    userKey = userDict[key]
                    break
                else:
                    print("Error, user not found.")
            
            userEmail = userKey.get_email()
            userAccType = userKey.get_acc_type()

            return render_template('users/loggedin/user_profile.html', form=create_image_upload_form, username=usernameSession, email=userEmail, accType = userAccType)
    else:
        return redirect(url_for("home"))

@app.route('/payment_method', methods=["GET","POST"])
def userPayment():
    if "userSession" in session:
        usernameSession = session["userSession"]

        # declaring userKey variable to prevent unboundLocalError
        userKey = ""

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open("user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                print("User data in shelve is empty.")
                session.clear() # since the file could not be found either due to the admin deleting or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            print("Error in retrieving Users from user.db")

        # retrieving the object from the shelve based on the user's username
        print("Username session:", usernameSession)
        for key in userDict:
            print("retrieving")
            usernameShelveData = userDict[key].get_username()
            print("Username in database:", usernameShelveData)
            if usernameSession == usernameShelveData:
                print("Verdict: Username found.")
                userKey = userDict[key]
                break
            else:
                print("Error, user not found.")

        cardExist = bool(userKey.get_card_name())
        print("Card exist?:", cardExist)
        
        if cardExist == False:
            print("Entered if loop")
            create_add_payment_form = Forms.CreateAddPaymentForm(request.form)
            if request.method == "POST" and create_add_payment_form.validate():
                print("POST request sent and form entries validated")
                cardName = create_add_payment_form.cardName.data
                cardNo = create_add_payment_form.cardNo.data
                cardType = create_add_payment_form.cardType.data
                cardExpiry = create_add_payment_form.cardExpiry.data
                cardCVV = create_add_payment_form.cardCVV.data

                # setting the user's payment method
                userKey.set_card_name(cardName)
                userKey.set_card_no(cardNo)
                userKey.set_card_expiry(cardExpiry)
                userKey.set_card_cvv(cardCVV)
                userKey.set_card_type(cardType)
                userKey.display_card_info()
                db['Users'] = userDict
                print("Payment added")

                db.close()
                return redirect(url_for("userPayment"))
            else:
                print("POST request sent but form not validated")
                db.close()
                return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form)
        else:
            cardName = userKey.get_card_name()
            cardNo = str(userKey.get_card_no())
            cardNo = cardNo[-5:-1] # string slicing to get the last 4 digits of the credit card number
            print("Sliced credit number:", cardNo)
            cardExpiry = str(userKey.get_card_expiry())
            cardYear = cardExpiry[:4] # string slicing to get the year from the date format "YYYY-MM-DD"
            cardMonth = cardExpiry[5:7] # string slicing to get the month from the date format "YYYY-MM-DD"
            cardExpiry = cardMonth + "/" + cardYear
            print("Sliced card expiry date:", cardExpiry)

            db.close()
            return render_template('users/loggedin/user_existing_payment.html', cardName=cardName, cardNo=cardNo, cardExpiry=cardExpiry)
    else:
        return redirect(url_for("home"))

@app.route('/edit_payment', methods=["GET","POST"])
def userEditPayment():
    if "userSession" in session:
        create_edit_payment_form = Forms.CreateEditPaymentForm(request.form)
        return render_template('users/loggedin/user_edit_payment.html', form=create_edit_payment_form)
    else:
        return redirect(url_for("home"))

"""End of User Profile Settings"""

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
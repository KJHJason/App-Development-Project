from flask import Flask, render_template, request, redirect, url_for, session
from wtforms import StringField, PasswordField
from werkzeug.utils import secure_filename
import os
import Forms
import User
import shelve

app = Flask(__name__)
UPLOAD_PATH = 'static/images/user'
ALLOWED_EXTENSIONS = {"png"}
app.config['UPLOAD_PATH'] = "uploads"
app.config['MAX_CONTENT_LENGTH'] = 5120 * 5120


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/user_profile')
def userProfile():
    return render_template('user_profile.html')

@app.route('/payment_method', methods=["GET","POST"])
def userPayment():
    #return render_template('user_existing_payment.html')

    create_add_payment_form = Forms.CreateAddPaymentForm(request.form)
    #if request.method == "POST" and create_add_payment_form.validate():
        #return render_template("home.html")
    return render_template('user_add_payment.html', form=create_add_payment_form)

@app.route('/edit_payment', methods=["GET","POST"])
def userEditPayment():
    create_edit_payment_form = Forms.CreateEditPaymentForm(request.form)
    return render_template('user_edit_payment.html', form=create_edit_payment_form)    

@app.route('/login', methods=['GET', 'POST'])
def userLogin():
    create_login_form = Forms.CreateLoginForm(request.form)
    if request.method == "POST" and create_login_form.validate():
        emailInput = create_login_form.email.data
        passwordInput = create_login_form.password.data
        userDict = {}
        db = shelve.open("user", "r")

        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db["Users"] = userDict
        except:
            print("Error in retrieving Users from user.db")

        for key in userDict:
            emailShelveData = userDict[key].get_email()
            passwordShelveData = userDict[key].get_password()
            if emailInput == emailShelveData:
                if passwordInput == passwordShelveData:
                    db.close()
                    return redirect(url_for("userProfile"))
                else:
                    print("User password incorrect.")
                    db.close()
                    return render_template('login.html', form=create_login_form, failedAttempt=True)
            else:
                print("User email not found.")
                db.close()
                return render_template('login.html', form=create_login_form, failedAttempt=True)
        
    return render_template('login.html', form=create_login_form)

@app.route('/signup', methods=['GET', 'POST'])
def userSignUp():
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

        emailInput = create_signup_form.email.data
        usernameInput = create_signup_form.username.data

        # Retrieving data from shelve for duplicate data checking
        userDict = {}
        db = shelve.open("user", "c")  # "c" flag as to create the files if there were no files to retrieve from and also to create the user if the validation conditions are met
        
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
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

            user = User.User(usernameInput, emailInput, passwordInput, "student", "good")
            print(user)

            userDict[user.get_user_id()] = user
            db["Users"] = userDict
            
            print(userDict)

            db.close()
            print("User added.")
            return redirect(url_for("home"))
        else:
            # if there were still duplicates or passwords entered were not the same, used Jinja to show the error messages
            db.close()
            print("Validation conditions were not met.")
            return render_template('signup.html', form=create_signup_form, email_duplicates=email_duplicates, username_duplicates=username_duplicates, pwd_were_not_matched=pwd_were_not_matched) 
            
    else:
        print("Failed to add user.")

    return render_template('signup.html', form=create_signup_form)    

if __name__ == '__main__':
    app.run()
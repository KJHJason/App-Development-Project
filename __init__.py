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
                    return redirect(url_for("userProfile"))
                else:
                    return render_template('login_failed.html', form=create_login_form)
            else:
                    return render_template('login_failed.html', form=create_login_form)

    return render_template('login.html', form=create_login_form)

@app.route('/signup', methods=['GET', 'POST'])
def userSignUp():
    create_signup_form = Forms.CreateSignUpForm(request.form)
    if request.method == 'POST' and create_signup_form.validate():

        userDict = {}
        db = shelve.open("user", "c")

        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db["Users"] = userDict

        except:
            print("Error in retrieving Users from user.db")

        user = User.User(create_signup_form.username.data, create_signup_form.email.data, create_signup_form.password.data, "student", "good")
        print(user)

        userDict[user.get_user_id()] = user
        db["Users"] = userDict

        db.close()
        # print("user added")
        return redirect(url_for("home"))
    # else:
    #     print("failed")

    return render_template('signup.html', form=create_signup_form)    

if __name__ == '__main__':
    app.run()

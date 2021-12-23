from flask import Flask, render_template, request, redirect, url_for, session
from wtforms import StringField, PasswordField
from werkzeug.utils import secure_filename
import os
import Forms

app = Flask(__name__)
UPLOAD_PATH = '/static/images/user'
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

@app.route('/login')
def userLogin():
    return render_template('login.html')

@app.route('/signup')
def userSignUp():
    return render_template('signup.html')    

if __name__ == '__main__':
    app.run()

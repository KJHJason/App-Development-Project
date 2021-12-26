from wtforms import Form, StringField, RadioField, SelectField, TextAreaField, validators, EmailField, DateField, MonthField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import PasswordField
from flask_wtf.file import FileField

class CreateEditPaymentForm(Form):
    cardExpiry = MonthField("Expiry Date:", [validators.DataRequired()])
    cardCVV = IntegerField("CVV:", [validators.NumberRange(min=0, max=999), validators.DataRequired()])

class CreateAddPaymentForm(Form):
    cardName = StringField("Card Name:", [validators.Length(min=1, max=150), validators.DataRequired()])
    cardNo = IntegerField("Card Number:", [validators.DataRequired()])
    cardExpiry = MonthField("Expiry Date:", [validators.DataRequired()])
    cardCVV = IntegerField("CVV:", [validators.NumberRange(min=0, max=999), validators.DataRequired()])
    cardType = SelectField('Card Type:', [validators.DataRequired()], choices=[('', 'Select card type'), ('mastercard', 'Mastercard'), ('visa', 'Visa')], default='')

class CreateLoginForm(Form):
    email = EmailField("Email:", [validators.Email(), validators.DataRequired()])
    password = PasswordField("Password:", [validators.DataRequired()])

class CreateSignUpForm(Form):
    username = StringField("Username:", [validators.Length(min=1, max=30), validators.DataRequired()])
    email = EmailField("Email:", [validators.Email(), validators.DataRequired()])
    password = PasswordField("Password:", [validators.Length(min=6, max=15), validators.DataRequired()])
    cfm_password = PasswordField("Confirm Password:", [validators.Length(min=6, max=15), validators.DataRequired()])

class CreateImageUploadForm(Form):
    imageFormFile = FileField("Upload Profile Image")

class CreateTeacherSignUpForm(Form):
    username = StringField("Username:", [validators.Length(min=1, max=30), validators.DataRequired()])
    email = EmailField("Email:", [validators.Email(), validators.DataRequired()])
    password = PasswordField("Password:", [validators.Length(min=6, max=15), validators.DataRequired()])
    cfm_password = PasswordField("Confirm Password:", [validators.Length(min=6, max=15), validators.DataRequired()])

class CreateTeacherPayment(Form):
    cardName = StringField("Card Name:", [validators.Length(min=1, max=50), validators.DataRequired()])
    cardNo = IntegerField("Card Number:", [validators.DataRequired()])
    cardExpiry = MonthField("Expiry Date:", [validators.DataRequired()])
    cardCVV = IntegerField("CVV:", [validators.NumberRange(min=0, max=999), validators.DataRequired()])
    cardType = SelectField('Card Type:', [validators.DataRequired()], choices=[('', 'Select card type'), ('mastercard', 'Mastercard'), ('visa', 'Visa')], default='')

class CreateChangeUsername(Form):
    updateUsername = StringField("Enter a new username:", [validators.Length(min=1, max=30), validators.DataRequired()])

class CreateChangeEmail(Form):
    updateEmail = EmailField("Enter a new email address:", [validators.Email(), validators.DataRequired()])

class CreateChangePasswordForm(Form):
    currentPassword = PasswordField("Enter your current password:", [validators.Length(min=6, max=15), validators.DataRequired()])
    updatePassword =  PasswordField("Enter a new password:", [validators.Length(min=6, max=15), validators.DataRequired()])
    confirmPassword = PasswordField("Confirm password:", [validators.Length(min=6, max=15), validators.DataRequired()])
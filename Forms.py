from wtforms import Form, StringField, RadioField, SelectField, TextAreaField, validators, EmailField, DateField, MonthField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import PasswordField

class CreateEditPaymentForm(Form):
    cardExpiry = MonthField("Expiry Date:", [validators.DataRequired()])
    cardCVV = IntegerField("CVV:", [validators.NumberRange(min=-999, max=999), validators.DataRequired()])

class CreateAddPaymentForm(Form):
    cardName = StringField("Card Name:", [validators.Length(min=1, max=150), validators.DataRequired()])
    cardNo = IntegerField("Card Number:", [validators.DataRequired()])
    cardType = SelectField('Card Type:', [validators.DataRequired()], choices=[('', 'Select card type'), ('mastercard', 'Mastercard'), ('visa', 'Visa')], default='')
    cardExpiry = MonthField("Expiry Date:", [validators.DataRequired()])
    cardCVV = IntegerField("CVV:", [validators.NumberRange(min=-999, max=999), validators.DataRequired()])

class CreateLoginForm(Form):
    email = EmailField("Email:", [validators.Email(), validators.DataRequired()])
    password = PasswordField("Password:", [validators.DataRequired()])

class CreateSignUpForm(Form):
    username = StringField("Username:", [validators.DataRequired()])
    email = EmailField("Email:", [validators.Email(), validators.DataRequired()])
    password = PasswordField("Password:", [validators.DataRequired()])
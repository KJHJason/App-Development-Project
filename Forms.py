from wtforms import Form, validators, StringField, RadioField, SelectField, TextAreaField, EmailField, DateField, HiddenField, FormField, IntegerField, PasswordField, BooleanField

"""WTForms by Jason"""

# Research notes for the different types of credit cards: 
# https://support.cybersource.com/s/article/What-are-the-number-formats-for-different-credit-cards
# https://www.experian.com/blogs/ask-experian/what-is-a-credit-card-cvv/

# Research note for email length:
# https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address

class CreateEditPaymentForm(Form):
    cardExpiry = StringField("Expiry Date:", [validators.Length(min=4, max=7), validators.DataRequired()])
    cardCVV = StringField("CVV:", [validators.Length(min=3, max=4), validators.DataRequired()])

class CreateAddPaymentForm(Form):
    cardName = StringField("Card Name:", [validators.Length(min=1, max=50), validators.DataRequired()])
    cardNo = StringField("Card Number:", [validators.Length(min=14, max=19), validators.DataRequired()])
    cardExpiry = StringField("Expiry Date:", [validators.Length(min=4, max=7), validators.DataRequired()])
    cardCVV = StringField("CVV:", [validators.Length(min=3, max=4), validators.DataRequired()])

class CreateLoginForm(Form):
    email = EmailField("Email:", [validators.Email(), validators.Length(min=3, max=254), validators.DataRequired()])
    password = PasswordField("Password:", [validators.DataRequired()])

class CreateSignUpForm(Form):
    username = StringField("Username:", [validators.Length(min=1, max=30), validators.DataRequired()])
    email = EmailField("Email:", [validators.Email(), validators.Length(min=3, max=254), validators.DataRequired()])
    password = PasswordField("Password:", [validators.Length(min=6, max=15), validators.DataRequired()])
    cfm_password = PasswordField("Confirm Password:", [validators.Length(min=6, max=15), validators.DataRequired()])

class CreateTeacherSignUpForm(Form):
    username = StringField("Username:", [validators.Length(min=1, max=30), validators.DataRequired()])
    email = EmailField("Email:", [validators.Email(), validators.Length(min=3, max=254), validators.DataRequired()])
    password = PasswordField("Password:", [validators.Length(min=6, max=15), validators.DataRequired()])
    cfm_password = PasswordField("Confirm Password:", [validators.Length(min=6, max=15), validators.DataRequired()])

class CreateChangeUsername(Form):
    updateUsername = StringField("Enter a new username:", [validators.Length(min=1, max=30), validators.DataRequired()])

class CreateChangeEmail(Form):
    updateEmail = EmailField("Enter a new email address:", [validators.Email(), validators.Length(min=3, max=254), validators.DataRequired()])

class CreateChangePasswordForm(Form):
    currentPassword = PasswordField("Enter your current password:", [validators.Length(min=6, max=15), validators.DataRequired()])
    updatePassword =  PasswordField("Enter a new password:", [validators.Length(min=6, max=15), validators.DataRequired()])
    confirmPassword = PasswordField("Confirm password:", [validators.Length(min=6, max=15), validators.DataRequired()])

class RequestResetPasswordForm(Form):
    email = EmailField("Enter your email:", [validators.Email(), validators.Length(min=3, max=254), validators.DataRequired()])

class CreateResetPasswordForm(Form):
    resetPassword =  PasswordField("Reset password:", [validators.Length(min=6, max=15), validators.DataRequired()])
    confirmPassword = PasswordField("Confirm password:", [validators.Length(min=6, max=15), validators.DataRequired()])

class AdminResetPasswordForm(Form):
    email = EmailField("Enter user's new email:", [validators.Email(), validators.Length(min=3, max=254), validators.DataRequired()])
    password = PasswordField("Enter a new password:", [validators.Length(min=6, max=15), validators.DataRequired()])

"""End of WTForms by Jason"""

"""WTForms by Royston"""

class CreateReviewText(Form):
    review = StringField("Review:", [validators.Length(min=20, max=2000), validators.DataRequired()])

"""End of WTForms by Royston"""

"""WTForms by Wei Ren"""

class RemoveShoppingCartCourse(Form):
    courseID = HiddenField("Course ID: Easter Egg Text", [validators.DataRequired()])
    courseType = HiddenField("Course Type: More Easter Eggs!", [validators.DataRequired()])

# Variables
class PaymentInfo(Form):
    cardName = StringField("Card Name:", [validators.Length(min=1, max=50), validators.DataRequired()])
    cardNo = StringField("Card Number (Only Visa, Mastercard, and American Express):", [validators.Length(min=14, max=19), validators.DataRequired()])
    cardExpiry = StringField("Expiry Date:", [validators.Length(min=4, max=7), validators.DataRequired()])
    cardCVV = StringField("CVV:", [validators.Length(min=3, max=4), validators.DataRequired()])
    savePaymentInfo = BooleanField("Save/Update Payment Info?", [validators.DataRequired()])
    firstName = StringField("First Name:", [validators.DataRequired()])
    lastName = StringField("Last Name:", [validators.DataRequired()])
    billAddress1 = StringField("Billing Address:", [validators.DataRequired()])
    billAddress2 = StringField("Billing Address, Line 2:", [validators.DataRequired()])
    billAddress3 = StringField("Billing Address, Line 3:", [validators.DataRequired()])
    city = StringField("City:", [validators.DataRequired()])
    country = StringField("Country:", [validators.DataRequired()])
    zipCode = IntegerField("Zip/Postal Code:", [validators.DataRequired()])
    countryCode = SelectField("Country Code:", [validators.DataRequired()], choices=[('cpp', 'C++'), ('py', 'Python'), ('text', 'Plain Text')])
    phoneNumber = IntegerField("Phone Number:", [validators.DataRequired()])

"""End of WTForms by Wei Ren"""

from wtforms import Form, validators, ValidationError, StringField, RadioField, SelectField, TextAreaField, EmailField, DateField, TimeField, HiddenField, FormField, IntegerField, PasswordField, BooleanField, FileField

"""WTForms by Jason"""

# Research notes for the different types of credit cards:
# https://support.cybersource.com/s/article/What-are-the-number-formats-for-different-credit-cards

# Research note for email length:
# https://stackoverflow.com/questions/386294/what-is-the-maximum-length-of-a-valid-email-address

class CreateEditPaymentForm(Form):
    cardExpiry = StringField("Expiry Date:", [validators.Length(min=4, max=7), validators.DataRequired()])

class CreateAddPaymentForm(Form):
    cardName = StringField("Card Name:", [validators.Length(min=1, max=50), validators.DataRequired()])
    cardNo = StringField("Card Number:", [validators.Length(min=13, max=19), validators.DataRequired()])
    cardExpiry = StringField("Expiry Date:", [validators.Length(min=4, max=7), validators.DataRequired()])

class CreateLoginForm(Form):
    email = EmailField("Email:", [validators.Email(), validators.Length(min=3, max=254), validators.DataRequired()])
    password = PasswordField("Password:", [validators.DataRequired()])

class CreateSignUpForm(Form):
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

"""End of WTForms by Jason"""

"""WTForms by Royston"""

class CreateReviewText(Form):
    review = TextAreaField("Review:", [validators.Length(min=20, max=2000), validators.DataRequired()])
    title = StringField("Title:", [validators.Length(min=20, max=100), validators.DataRequired()])

"""End of WTForms by Royston"""

"""WTForms by Wei Ren"""

def IntegerCheck(form, field):
    try:
        if int(field.data) - float(field.data) != 0:
            raise ValidationError("Value must be a whole number.")
    except:
        raise ValidationError("Value must be a whole number.")

def NoNumbers(form,field):
    value = str(field.data)
    for character in value:
        if not value.isdigit():
            raise ValidationError("Value should not contain numbers.")


class RemoveShoppingCartCourse(Form):
    courseID = HiddenField("Course ID: Easter Egg Text, Now with More Easter Eggs!")
    #courseType = HiddenField("Course Type: More Easter Eggs!")

class CheckoutComplete(Form):
    checkoutComplete = HiddenField("Check whether PayPal is complete: Extra Secret Easter Egg", [validators.DataRequired()], default = False)
    # Internet Date & Time Format: https://datatracker.ietf.org/doc/html/rfc3339#section-5.6
    checkoutTiming = HiddenField("Timing of Transaction: The past, present, future, where Eggs are found!", [validators.DataRequired()])
    checkoutOrderID = HiddenField("PayPal's own ID for transaction: Easter Egg to you!", [validators.DataRequired()])
    checkoutPayerID = HiddenField("PayPal's own ID for identifying account: Easter Egg Number 4!", [validators.DataRequired()])

class ContactUs(Form):
    name = StringField("Name: Easter Egg", [validators.DataRequired()])
    email = EmailField("Email: easter@bunny.com", [validators.DataRequired(), validators.Email()])
    subject = SelectField("Subject: 17 April 2022", [validators.DataRequired()], choices = [("","Subject"),
                                                                                            ("General","General Enquiry"),
                                                                                            ("Account", "Account Enquiry"),
                                                                                            ("Business","Business Enquiry"),
                                                                                            ("Bugs", "Bug Report"),
                                                                                            ("Jobs","Job-Seeking"),
                                                                                            ("News","News Media"),
                                                                                            ("Others","Others")])
                                                                                           #("Value", "Label")
    enquiry = TextAreaField("Enquiry: Easter Sunday", [validators.DataRequired()])

class TicketSearchForm(Form):# Very cursed. I love lack of Checkbox Field.
    query = HiddenField([validators.Optional()])
    checkedFilters = HiddenField([validators.DataRequired(), validators.InputRequired()])

#   filterStatus = RadioField("Ticket Status", [validators.DataRequired()], choices = ['Open','Closed'], default = 'Open')
#   filterAccount = RadioField("Account Type", [validators.DataRequired()], choices = ['Guest','Student','Teacher'], default = 'Guest')
#   filterSubject = RadioField("Subject", [validators.DataRequired()], choices = ['General','Account','Business','Bugs','Jobs','News','Other'], default = 'General')

class TicketAction(Form):
    ticketID = HiddenField("Greetings to you, the lucky finder of this Golden Ticket!",[validators.DataRequired()], default = "")
    ticketAction = HiddenField("I shake you warmly by the hand!",[validators.DataRequired()], default = "")

""""End of WTForms by Wei Ren"""

"""WTForms by Clarence"""
class CreateCourse(Form):
    '''title
    description = StringField("Description")
    thumbnail
    zoomprices = StringField("")
    videoprice = StringField("")
    zoomconditions
    videocondiction
    tags = StringField("")
    zoomschedule'''
    title = StringField("Course Title: ", [validators.DataRequired(), validators.Length(min=3, max=100)])
    description = StringField("Description: ", [validators.DataRequired(), validators.Length(min=1)])
    #thumbnail use HTML to validate size, type
    coursePrice = StringField("Price for Course (USD$): ", [validators.DataRequired(), validators.NumberRange(min=0, max=500)])
"""End of WTForms by Clarence"""

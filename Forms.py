from wtforms import Form, StringField, RadioField, SelectField, TextAreaField, validators, EmailField, DateField, MonthField
from wtforms.fields.numeric import IntegerField

class CreateEditPaymentForm(Form):
    cardExpiry = MonthField("Expiry Date:", [validators.DataRequired()])
    cardCVV = IntegerField("CVV:", [validators.NumberRange(min=-999, max=999), validators.DataRequired()])

class CreateAddPaymentForm(Form):
    cardName = StringField("Card Name:", [validators.Length(min=1, max=150), validators.DataRequired()])
    cardNo = IntegerField("Card Number:", [validators.DataRequired()])
    cardType = SelectField('Card Type:', [validators.DataRequired()], choices=[('', 'Select card type'), ('mastercard', 'Mastercard'), ('visa', 'Visa')], default='')
    cardExpiry = MonthField("Expiry Date:", [validators.DataRequired()])
    cardCVV = IntegerField("CVV:", [validators.NumberRange(min=-999, max=999), validators.DataRequired()])
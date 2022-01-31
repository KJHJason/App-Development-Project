import json

from wtforms import Form, validators, ValidationError, StringField, RadioField, SelectField, TextAreaField, EmailField, DateField, TimeField, HiddenField, FormField, IntegerField, PasswordField, BooleanField, FileField

"""WTForms by Jason"""

# Research notes for the different types of credit cards:
# https://support.cybersource.com/s/article/Whatarethenumberformatsfordifferentcreditcards

# Research note for email length:
# https://stackoverflow.com/questions/386294/whatisthemaximumlengthofavalidemailaddress
"""
class CreateEditPaymentForm(Form):
    cardExpiry = StringField("Expiry Date:", [validators.Length(min=4, max=7), validators.DataRequired()])

class CreateAddPaymentForm(Form):
    cardName = StringField("Card Name:", [validators.Length(min=1, max=50), validators.DataRequired()])
    cardNo = StringField("Card Number:", [validators.Length(min=13, max=19), validators.DataRequired()])
    cardExpiry = StringField("Expiry Date:", [validators.Length(min=4, max=7), validators.DataRequired()])
"""
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

def NotOwnEmail(form,field):
    if field.data.lower() == "coursefinity123@gmail.com":
        raise ValidationError("Email should be your own.")

class RemoveShoppingCartCourse(Form):
    courseID = HiddenField("Course ID: Easter Egg Text, Now with More Easter Eggs!")
    #courseType = HiddenField("Course Type: More Easter Eggs!")

class CheckoutComplete(Form):
    checkoutComplete = HiddenField("Check whether PayPal is complete: Extra Secret Easter Egg", [validators.DataRequired()], default = False)
    # Internet Date & Time Format: https://datatracker.ietf.org/doc/html/rfc3339#section5.6
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
                                                                                            ("Jobs","JobSeeking"),
                                                                                            ("News","News Media"),
                                                                                            ("Others","Others")])
                                                                                           #("Value", "Label")
    enquiry = TextAreaField("Enquiry: Easter Sunday", [validators.DataRequired()])

class TicketSearchForm(Form):# Very cursed. I love lack of Checkbox Field.
    query = HiddenField([validators.Optional()])
    checkedFilters = HiddenField([validators.DataRequired(), validators.InputRequired()])

#   filterStatus = RadioField("Ticket Status", [validators.DataRequired()], choices = ['Open','Closed'], default = 'Open'),
#   filterAccount = RadioField("Account Type", [validators.DataRequired()], choices = ['Guest','Student','Teacher'], default = 'Guest'),
#   filterSubject = RadioField("Subject", [validators.DataRequired()], choices = ['General','Account','Business','Bugs','Jobs','News','Other'], default = 'General'),

class TicketAction(Form):
    ticketID = HiddenField("Greetings to you, the lucky finder of this Golden Ticket!",[validators.DataRequired()], default = "")
    ticketAction = HiddenField("I shake you warmly by the hand!",[validators.DataRequired()], default = "")

class CashoutForm(Form):
    deleteInfo = HiddenField([validators.DataRequired()], default=json.dumps(False))
    cashoutPreference = RadioField([validators.DataRequired()], choices=[("Phone","Phone"),
                                                                         ("Email","Email")])
    countryCode = SelectField("Country Code:", choices=[('Afghanistan (+93)', 'Afghanistan (+93)'),
                                                        ('Albania (+355)', 'Albania (+355)'),
                                                        ('Algeria (+213)', 'Algeria (+213)'),
                                                        ('American Samoa (+1684)', 'American Samoa (+1684)'),
                                                        ('Andorra (+376)', 'Andorra (+376)'),
                                                        ('Angola (+244)', 'Angola (+244)'),
                                                        ('Anguilla (+1264)', 'Anguilla (+1264)'),
                                                        ('Antarctica (+672)', 'Antarctica (+672)'),
                                                        ('Antigua and Barbuda (+1268)', 'Antigua and Barbuda (+1268)'),
                                                        ('Argentina (+54)', 'Argentina (+54)'),
                                                        ('Armenia (+374)', 'Armenia (+374)'),
                                                        ('Aruba (+297)', 'Aruba (+297)'),
                                                        ('Australia (+61)', 'Australia (+61)'),
                                                        ('Austria (+43)', 'Austria (+43)'),
                                                        ('Azerbaijan (+994)', 'Azerbaijan (+994)'),
                                                        ('Bahamas (+1242)', 'Bahamas (+1242)'),
                                                        ('Bahrain (+973)', 'Bahrain (+973)'),
                                                        ('Bangladesh (+880)', 'Bangladesh (+880)'),
                                                        ('Barbados (+1246)', 'Barbados (+1246)'),
                                                        ('Belarus (+375)', 'Belarus (+375)'),
                                                        ('Belgium (+32)', 'Belgium (+32)'),
                                                        ('Belize (+501)', 'Belize (+501)'),
                                                        ('Benin (+229)', 'Benin (+229)'),
                                                        ('Bermuda (+1441)', 'Bermuda (+1441)'),
                                                        ('Bhutan (+975)', 'Bhutan (+975)'),
                                                        ('Bolivia (+591)', 'Bolivia (+591)'),
                                                        ('Bosnia and Herzegovina (+387)', 'Bosnia and Herzegovina (+387)'),
                                                        ('Botswana (+267)', 'Botswana (+267)'),
                                                        ('Brazil (+55)', 'Brazil (+55)'),
                                                        ('British Indian Ocean Territory (+246)', 'British Indian Ocean Territory (+246)'),
                                                        ('British Virgin Islands (+1284)', 'British Virgin Islands (+1284)'),
                                                        ('Brunei (+673)', 'Brunei (+673)'),
                                                        ('Bulgaria (+359)', 'Bulgaria (+359)'),
                                                        ('Burkina Faso (+226)', 'Burkina Faso (+226)'),
                                                        ('Burundi (+257)', 'Burundi (+257)'),
                                                        ('Cambodia (+855)', 'Cambodia (+855)'),
                                                        ('Cameroon (+237)', 'Cameroon (+237)'),
                                                        ('Canada (+1)', 'Canada (+1)'),
                                                        ('Cape Verde (+238)', 'Cape Verde (+238)'),
                                                        ('Cayman Islands (+1345)', 'Cayman Islands (+1345)'),
                                                        ('Central African Republic (+236)', 'Central African Republic (+236)'),
                                                        ('Chad (+235)', 'Chad (+235)'),
                                                        ('Chile (+56)', 'Chile (+56)'),
                                                        ('China (+86)', 'China (+86)'),
                                                        ('Christmas Island (+61)', 'Christmas Island (+61)'),
                                                        ('Cocos Islands (+61)', 'Cocos Islands (+61)'),
                                                        ('Colombia (+57)', 'Colombia (+57)'),
                                                        ('Comoros (+269)', 'Comoros (+269)'),
                                                        ('Cook Islands (+682)', 'Cook Islands (+682)'),
                                                        ('Costa Rica (+506)', 'Costa Rica (+506)'),
                                                        ('Croatia (+385)', 'Croatia (+385)'),
                                                        ('Cuba (+53)', 'Cuba (+53)'),
                                                        ('Curacao (+599)', 'Curacao (+599)'),
                                                        ('Cyprus (+357)', 'Cyprus (+357)'),
                                                        ('Czech Republic (+420)', 'Czech Republic (+420)'),
                                                        ('Democratic Republic of the Congo (+243)', 'Democratic Republic of the Congo (+243)'),
                                                        ('Denmark (+45)', 'Denmark (+45)'),
                                                        ('Djibouti (+253)', 'Djibouti (+253)'),
                                                        ('Dominica (+1767)', 'Dominica (+1767)'),
                                                        ('Dominican Republic (+1809)', 'Dominican Republic (+1809)'),
                                                        ('Dominican Republic (+1829)', 'Dominican Republic (+1829)'),
                                                        ('Dominican Republic (+1849)', 'Dominican Republic (+1849)'),
                                                        ('East Timor (+670)', 'East Timor (+670)'),
                                                        ('Ecuador (+593)', 'Ecuador (+593)'),
                                                        ('Egypt (+20)', 'Egypt (+20)'),
                                                        ('El Salvador (+503)', 'El Salvador (+503)'),
                                                        ('Equatorial Guinea (+240)', 'Equatorial Guinea (+240)'),
                                                        ('Eritrea (+291)', 'Eritrea (+291)'),
                                                        ('Estonia (+372)', 'Estonia (+372)'),
                                                        ('Ethiopia (+251)', 'Ethiopia (+251)'),
                                                        ('Falkland Islands (+500)', 'Falkland Islands (+500)'),
                                                        ('Faroe Islands (+298)', 'Faroe Islands (+298)'),
                                                        ('Fiji (+679)', 'Fiji (+679)'),
                                                        ('Finland (+358)', 'Finland (+358)'),
                                                        ('France (+33)', 'France (+33)'),
                                                        ('French Polynesia (+689)', 'French Polynesia (+689)'),
                                                        ('Gabon (+241)', 'Gabon (+241)'),
                                                        ('Gambia (+220)', 'Gambia (+220)'),
                                                        ('Georgia (+995)', 'Georgia (+995)'),
                                                        ('Germany (+49)', 'Germany (+49)'),
                                                        ('Ghana (+233)', 'Ghana (+233)'),
                                                        ('Gibraltar (+350)', 'Gibraltar (+350)'),
                                                        ('Greece (+30)', 'Greece (+30)'),
                                                        ('Greenland (+299)', 'Greenland (+299)'),
                                                        ('Grenada (+1473)', 'Grenada (+1473)'),
                                                        ('Guam (+1671)', 'Guam (+1671)'),
                                                        ('Guatemala (+502)', 'Guatemala (+502)'),
                                                        ('Guernsey (+441481)', 'Guernsey (+441481)'),
                                                        ('Guinea (+224)', 'Guinea (+224)'),
                                                        ('GuineaBissau (+245)', 'GuineaBissau (+245)'),
                                                        ('Guyana (+592)', 'Guyana (+592)'),
                                                        ('Haiti (+509)', 'Haiti (+509)'),
                                                        ('Honduras (+504)', 'Honduras (+504)'),
                                                        ('Hong Kong (+852)', 'Hong Kong (+852)'),
                                                        ('Hungary (+36)', 'Hungary (+36)'),
                                                        ('Iceland (+354)', 'Iceland (+354)'),
                                                        ('India (+91)', 'India (+91)'),
                                                        ('Indonesia (+62)', 'Indonesia (+62)'),
                                                        ('Iran (+98)', 'Iran (+98)'),
                                                        ('Iraq (+964)', 'Iraq (+964)'),
                                                        ('Ireland (+353)', 'Ireland (+353)'),
                                                        ('Isle of Man (+441624)', 'Isle of Man (+441624)'),
                                                        ('Israel (+972)', 'Israel (+972)'),
                                                        ('Italy (+39)', 'Italy (+39)'),
                                                        ('Ivory Coast (+225)', 'Ivory Coast (+225)'),
                                                        ('Jamaica (+1876)', 'Jamaica (+1876)'),
                                                        ('Japan (+81)', 'Japan (+81)'),
                                                        ('Jersey (+441534)', 'Jersey (+441534)'),
                                                        ('Jordan (+962)', 'Jordan (+962)'),
                                                        ('Kazakhstan (+7)', 'Kazakhstan (+7)'),
                                                        ('Kenya (+254)', 'Kenya (+254)'),
                                                        ('Kiribati (+686)', 'Kiribati (+686)'),
                                                        ('Kosovo (+383)', 'Kosovo (+383)'),
                                                        ('Kuwait (+965)', 'Kuwait (+965)'),
                                                        ('Kyrgyzstan (+996)', 'Kyrgyzstan (+996)'),
                                                        ('Laos (+856)', 'Laos (+856)'),
                                                        ('Latvia (+371)', 'Latvia (+371)'),
                                                        ('Lebanon (+961)', 'Lebanon (+961)'),
                                                        ('Lesotho (+266)', 'Lesotho (+266)'),
                                                        ('Liberia (+231)', 'Liberia (+231)'),
                                                        ('Libya (+218)', 'Libya (+218)'),
                                                        ('Liechtenstein (+423)', 'Liechtenstein (+423)'),
                                                        ('Lithuania (+370)', 'Lithuania (+370)'),
                                                        ('Luxembourg (+352)', 'Luxembourg (+352)'),
                                                        ('Macau (+853)', 'Macau (+853)'),
                                                        ('Macedonia (+389)', 'Macedonia (+389)'),
                                                        ('Madagascar (+261)', 'Madagascar (+261)'),
                                                        ('Malawi (+265)', 'Malawi (+265)'),
                                                        ('Malaysia (+60)', 'Malaysia (+60)'),
                                                        ('Maldives (+960)', 'Maldives (+960)'),
                                                        ('Mali (+223)', 'Mali (+223)'),
                                                        ('Malta (+356)', 'Malta (+356)'),
                                                        ('Marshall Islands (+692)', 'Marshall Islands (+692)'),
                                                        ('Mauritania (+222)', 'Mauritania (+222)'),
                                                        ('Mauritius (+230)', 'Mauritius (+230)'),
                                                        ('Mayotte (+262)', 'Mayotte (+262)'),
                                                        ('Mexico (+52)', 'Mexico (+52)'),
                                                        ('Micronesia (+691)', 'Micronesia (+691)'),
                                                        ('Moldova (+373)', 'Moldova (+373)'),
                                                        ('Monaco (+377)', 'Monaco (+377)'),
                                                        ('Mongolia (+976)', 'Mongolia (+976)'),
                                                        ('Montenegro (+382)', 'Montenegro (+382)'),
                                                        ('Montserrat (+1664)', 'Montserrat (+1664)'),
                                                        ('Morocco (+212)', 'Morocco (+212)'),
                                                        ('Mozambique (+258)', 'Mozambique (+258)'),
                                                        ('Myanmar (+95)', 'Myanmar (+95)'),
                                                        ('Namibia (+264)', 'Namibia (+264)'),
                                                        ('Nauru (+674)', 'Nauru (+674)'),
                                                        ('Nepal (+977)', 'Nepal (+977)'),
                                                        ('Netherlands (+31)', 'Netherlands (+31)'),
                                                        ('Netherlands Antilles (+599)', 'Netherlands Antilles (+599)'),
                                                        ('New Caledonia (+687)', 'New Caledonia (+687)'),
                                                        ('New Zealand (+64)', 'New Zealand (+64)'),
                                                        ('Nicaragua (+505)', 'Nicaragua (+505)'),
                                                        ('Niger (+227)', 'Niger (+227)'),
                                                        ('Nigeria (+234)', 'Nigeria (+234)'),
                                                        ('Niue (+683)', 'Niue (+683)'),
                                                        ('North Korea (+850)', 'North Korea (+850)'),
                                                        ('Northern Mariana Islands (+1670)', 'Northern Mariana Islands (+1670)'),
                                                        ('Norway (+47)', 'Norway (+47)'),
                                                        ('Oman (+968)', 'Oman (+968)'),
                                                        ('Pakistan (+92)', 'Pakistan (+92)'),
                                                        ('Palau (+680)', 'Palau (+680)'),
                                                        ('Palestine (+970)', 'Palestine (+970)'),
                                                        ('Panama (+507)', 'Panama (+507)'),
                                                        ('Papua New Guinea (+675)', 'Papua New Guinea (+675)'),
                                                        ('Paraguay (+595)', 'Paraguay (+595)'),
                                                        ('Peru (+51)', 'Peru (+51)'),
                                                        ('Philippines (+63)', 'Philippines (+63)'),
                                                        ('Pitcairn (+64)', 'Pitcairn (+64)'),
                                                        ('Poland (+48)', 'Poland (+48)'),
                                                        ('Portugal (+351)', 'Portugal (+351)'),
                                                        ('Puerto Rico (+1787)', 'Puerto Rico (+1787)'),
                                                        ('Puerto Rico (+1939)', 'Puerto Rico (+1939)'),
                                                        ('Qatar (+974)', 'Qatar (+974)'),
                                                        ('Republic of the Congo (+242)', 'Republic of the Congo (+242)'),
                                                        ('Reunion (+262)', 'Reunion (+262)'),
                                                        ('Romania (+40)', 'Romania (+40)'),
                                                        ('Russia (+7)', 'Russia (+7)'),
                                                        ('Rwanda (+250)', 'Rwanda (+250)'),
                                                        ('Saint Barthelemy (+590)', 'Saint Barthelemy (+590)'),
                                                        ('Saint Helena (+290)', 'Saint Helena (+290)'),
                                                        ('Saint Kitts and Nevis (+1869)', 'Saint Kitts and Nevis (+1869)'),
                                                        ('Saint Lucia (+1758)', 'Saint Lucia (+1758)'),
                                                        ('Saint Martin (+590)', 'Saint Martin (+590)'),
                                                        ('Saint Pierre and Miquelon (+508)', 'Saint Pierre and Miquelon (+508)'),
                                                        ('Saint Vincent and the Grenadines (+1784)', 'Saint Vincent and the Grenadines (+1784)'),
                                                        ('Samoa (+685)', 'Samoa (+685)'),
                                                        ('San Marino (+378)', 'San Marino (+378)'),
                                                        ('Sao Tome and Principe (+239)', 'Sao Tome and Principe (+239)'),
                                                        ('Saudi Arabia (+966)', 'Saudi Arabia (+966)'),
                                                        ('Senegal (+221)', 'Senegal (+221)'),
                                                        ('Serbia (+381)', 'Serbia (+381)'),
                                                        ('Seychelles (+248)', 'Seychelles (+248)'),
                                                        ('Sierra Leone (+232)', 'Sierra Leone (+232)'),
                                                        ('Singapore (+65)', 'Singapore (+65)'),
                                                        ('Sint Maarten (+1721)', 'Sint Maarten (+1721)'),
                                                        ('Slovakia (+421)', 'Slovakia (+421)'),
                                                        ('Slovenia (+386)', 'Slovenia (+386)'),
                                                        ('Solomon Islands (+677)', 'Solomon Islands (+677)'),
                                                        ('Somalia (+252)', 'Somalia (+252)'),
                                                        ('South Africa (+27)', 'South Africa (+27)'),
                                                        ('South Korea (+82)', 'South Korea (+82)'),
                                                        ('South Sudan (+211)', 'South Sudan (+211)'),
                                                        ('Spain (+34)', 'Spain (+34)'),
                                                        ('Sri Lanka (+94)', 'Sri Lanka (+94)'),
                                                        ('Sudan (+249)', 'Sudan (+249)'),
                                                        ('Suriname (+597)', 'Suriname (+597)'),
                                                        ('Svalbard and Jan Mayen (+47)', 'Svalbard and Jan Mayen (+47)'),
                                                        ('Swaziland (+268)', 'Swaziland (+268)'),
                                                        ('Sweden (+46)', 'Sweden (+46)'),
                                                        ('Switzerland (+41)', 'Switzerland (+41)'),
                                                        ('Syria (+963)', 'Syria (+963)'),
                                                        ('Taiwan (+886)', 'Taiwan (+886)'),
                                                        ('Tajikistan (+992)', 'Tajikistan (+992)'),
                                                        ('Tanzania (+255)', 'Tanzania (+255)'),
                                                        ('Thailand (+66)', 'Thailand (+66)'),
                                                        ('Togo (+228)', 'Togo (+228)'),
                                                        ('Tokelau (+690)', 'Tokelau (+690)'),
                                                        ('Tonga (+676)', 'Tonga (+676)'),
                                                        ('Trinidad and Tobago (+1868)', 'Trinidad and Tobago (+1868)'),
                                                        ('Tunisia (+216)', 'Tunisia (+216)'),
                                                        ('Turkey (+90)', 'Turkey (+90)'),
                                                        ('Turkmenistan (+993)', 'Turkmenistan (+993)'),
                                                        ('Turks and Caicos Islands (+1649)', 'Turks and Caicos Islands (+1649)'),
                                                        ('Tuvalu (+688)', 'Tuvalu (+688)'),
                                                        ('U.S. Virgin Islands (+1340)', 'U.S. Virgin Islands (+1340)'),
                                                        ('Uganda (+256)', 'Uganda (+256)'),
                                                        ('Ukraine (+380)', 'Ukraine (+380)'),
                                                        ('United Arab Emirates (+971)', 'United Arab Emirates (+971)'),
                                                        ('United Kingdom (+44)', 'United Kingdom (+44)'),
                                                        ('United States (+1)', 'United States (+1)'),
                                                        ('Uruguay (+598)', 'Uruguay (+598)'),
                                                        ('Uzbekistan (+998)', 'Uzbekistan (+998)'),
                                                        ('Vanuatu (+678)', 'Vanuatu (+678)'),
                                                        ('Vatican (+379)', 'Vatican (+379)'),
                                                        ('Venezuela (+58)', 'Venezuela (+58)'),
                                                        ('Vietnam (+84)', 'Vietnam (+84)'),
                                                        ('Wallis and Futuna (+681)', 'Wallis and Futuna (+681)'),
                                                        ('Western Sahara (+212)', 'Western Sahara (+212)'),
                                                        ('Yemen (+967)', 'Yemen (+967)'),
                                                        ('Zambia (+260)', 'Zambia (+260)'),
                                                        ('Zimbabwe (+263)', 'Zimbabwe (+263)'),
                                                        ])
    phoneNumber = StringField("Phone Number: ", default="")

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
    courseTitle = StringField("Course Title: ", [validators.DataRequired(), validators.Length(min=3, max=100)])
    courseDescription = StringField("Description: ", [validators.DataRequired(), validators.Length(min=1)])
    #thumbnail use HTML to validate size, type
    coursePrice = IntegerField("Price for Course (USD$): ", [validators.DataRequired(), validators.NumberRange(min=0, max=500)])
"""End of WTForms by Clarence"""

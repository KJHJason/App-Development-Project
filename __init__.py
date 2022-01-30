from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from werkzeug.utils import secure_filename # this is for sanitising a filename for security reasons, remove if not needed (E.g. if you're changing the filename to use a id such as 0a18dd92.png before storing the file, it is not needed)
import shelve, os, math, paypalrestsdk, difflib, copy, json, csv, vimeo, pathlib
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
from flask_mail import Mail
from datetime import date, timedelta, datetime
from base64 import b64encode, b64decode
from apscheduler.schedulers.background import BackgroundScheduler
from matplotlib import pyplot as plt
from dicebear import DOptions
from python_files import Student, Teacher, Forms
from python_files import Payment
from python_files.Security import sanitise
from python_files.CardValidation import validate_card_number, get_credit_card_type, validate_cvv, validate_expiry_date, cardExpiryStringFormatter, validate_formatted_expiry_date
from python_files.IntegratedFunctions import *

"""Web app configurations"""

# general Flask configurations
app = Flask(__name__)
app.config["SECRET_KEY"] = "a secret key" # for demonstration purposes, if deployed, change it to something more secure
scheduler = BackgroundScheduler()

# Maximum file size for uploading anything to the web app's server
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024 # 200MiB

# Configurations for dicebear api for user profile image options
app.config["DICEBEAR_OPTIONS"] = options = DOptions(
    size=250
)

# creating an absolute path for storing the shelve files
app.config["DATABASE_FOLDER"] = str(pathlib.Path.cwd()) + "\\databases"

# configuration for email
# Make sure to enable access for less secure apps
app.config["MAIL_SERVER"] = "smtp.googlemail.com" # using gmail
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "CourseFinity123@gmail.com" # using gmail
app.config["MAIL_PASSWORD"] = os.environ.get("EMAIL_PASS") # setting password but hiding the password for the CourseFinity123@gmail.com password using system environment variables
mail = Mail(app)

# paypal sdk configuration
paypalrestsdk.configure({
  "mode": "sandbox",
  "client_id": "AUTh83JMz8mLNGNzpzJRJSbSLUAEp7oe1ieGGqYCmVXpq427DeSVElkHnc0tt70b8gHlWg4yETnLLu1s",
  "client_secret": os.environ.get("PAYPAL_SECRET") })

# Flask limiter configuration
limiter = Limiter(app, key_func=get_remote_address)

# vimeo api configurations
client = vimeo.VimeoClient(
    # client token, key, and secret all generated from vimeo
    token = os.environ.get("VIMEO_TOKEN"),
    key = '8ae482ba677dcdad1866b53280d00ea2a8e8ce05',
    secret = os.environ.get("VIMEO_SECRET")
)

""" # Uploading of videos
file_name = '{path_to_a_video_on_the_file_system}'
uri = client.upload(file_name, data={
    'name': 'Untitled',
    'description': 'The description goes here.'
})

print ('Your video URI is: %s' % (uri))

# Error handling while video transcodes
response = client.get(uri + '?fields=transcode.status').json()
if response['transcode']['status'] == 'complete':
    print ('Your video finished transcoding.')
elif response['transcode']['status'] == 'in_progress':
    print ('Your video is still transcoding.')
else:
    print ('Your video encountered an error during transcoding.')

response = client.get(uri + '?fields=link').json()
print("Your video link is: " + response['link']) """

"""End of Web app configurations"""

"""Home page by Jason"""

@app.route('/')
@limiter.limit("30/second") # to prevent ddos attacks
def home():
    courseDict = {}
    userDict = {}
    try:
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
        courseDict = db['Courses']
        userDict = db['Users']
        db.close()
        print("File found.")
    except:
        print("File could not be found.")
        # since the shelve files could not be found, it will create a placeholder/empty shelve files
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        db["Courses"] = courseDict
        db["Users"] = userDict
        db.close()

    # for trending algorithm
    trendingCourseList = []
    count = 0
    try:
        courseDictCopy = copy.deepcopy(courseDict)
        while count != 3:
            highestViewedCourse = max(courseDictCopy, key=lambda courseID: courseDictCopy[courseID].get_views())
            # retrieve teacher user ID
            courseTeacherID = courseDict.get(highestViewedCourse).get_userID()
            # based on the teacher user ID and check if the teacher is banned
            if userDict.get(courseTeacherID).get_status() == "Good":
                # append course object if the teacher is not banned
                trendingCourseList.append(courseDict.get(highestViewedCourse))
                courseDictCopy.pop(highestViewedCourse)
                count += 1
            else:
                # remove the course object from the courseDictCopy if the teacher is banned
                courseDictCopy.pop(highestViewedCourse)
    except:
        print("No courses or not enough courses (requires 3 courses)")
        trendingCourseList = []
        for values in courseDict.values():
            if userDict.get(values.get_userID()).get_status() == "Good":
                trendingCourseList.append(values)

    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            if accType != "Admin":
                # checking if the teacher recently added their payment method when signing up
                if "teacherPaymentAdded" in session:
                    teacherPaymentAdded = True
                    session.pop("teacherPaymentAdded", None)
                else:
                    teacherPaymentAdded = False

                # checking if the user recently completed a purchase
                if "paymentComplete" in session:
                    paymentComplete = True
                    session.pop("paymentComplete", None)
                else:
                    paymentComplete = False

                # for recommendation algorithm
                recommendCourseList = []
                if len(courseDict) > 3:
                    userTagDict = userKey.get_tags_viewed()
                    userPurchasedCourses = userKey.get_purchases() # to be edited once the attribute in the class has been updated
                    numberOfUniqueViews = checkUniqueElements(userTagDict)
                    if numberOfUniqueViews > 1:
                        highestWatchedByTag = max(userTagDict, key=userTagDict.get)
                        userTagDict.pop(highestWatchedByTag)
                        numberOfUnqiueViews = checkUniqueElements(userTagDict)
                        if numberOfUnqiueViews > 1:
                            secondHighestWatchedByTag = max(userTagDict, key=userTagDict.get)
                        else:
                            # meaning that the user has watched some tags but only one tag is the highest while the rest of tags are the same (assuming the dictionary has not popped its highest tag yet)
                            try:
                                # hence choosing one other random course objects
                                while True:
                                    randomisedCourse = random.choice(list(courseDict.values()))
                                    if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                                        if randomisedCourse not in userPurchasedCourses:
                                            recommendCourseList.append(randomisedCourse)
                                            courseDict.pop(randomisedCourse.get_courseID())
                                            break
                                        else:
                                            # user has purchased the course
                                            courseDict.pop(randomisedCourse.get_courseID())
                                    else:
                                        # if the teacher of the course has been banned
                                        courseDict.pop(randomisedCourse.get_courseID())
                            except:
                                print("No course found.")
                    else:
                        # meaning that the user has either not seen any tags or has watched an equal balance of various tags
                        # hence choosing three random course objects
                        try:
                            while len(recommendCourseList) != 3:
                                randomisedCourse = random.choice(list(courseDict.values()))
                                if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                                    if (randomisedCourse not in userPurchasedCourses) and (randomisedCourse not in recommendCourseList):
                                        recommendCourseList.append(randomisedCourse)
                                        courseDict.pop(randomisedCourse.get_courseID())
                                    else:
                                        # user has purchased the course
                                        courseDict.pop(randomisedCourse.get_courseID())
                                else:
                                    # if the teacher of the course has been banned
                                    courseDict.pop(randomisedCourse.get_courseID())
                        except:
                            print("No courses found.")

                    recommendedCourseListByHighestTag = []

                    # checking current length of the recommendCourseList if the length is less than 3, then adding courses to make it a length of 3
                    courseListLen = len(recommendCourseList)
                    if courseListLen == 0: # condition will be true when the user has two unique highest tags
                        recommendedCourseListBySecondHighestTag = []
                        for key in courseDict:
                            courseObject = courseDict[key]
                            courseTag = courseObject.get_tags()
                            if courseTag == highestWatchedByTag:
                                if courseObject.get_courseID() not in userPurchasedCourses:
                                    if userDict.get(courseObject.get_userID()).get_status() == "Good":
                                        recommendedCourseListByHighestTag.append(courseObject)
                                    else:
                                        # if the teacher of the course has been banned
                                        courseDict.pop(randomisedCourse.get_courseID())
                                else:
                                    # user has bought the course
                                    courseDict.pop(randomisedCourse.get_courseID())
                            elif courseTag == secondHighestWatchedByTag:
                                if courseObject.get_courseID() not in userPurchasedCourses:
                                    if userDict.get(courseObject.get_userID()).get_status() == "Good":
                                        recommendedCourseListBySecondHighestTag.append(courseObject)
                                    else:
                                        # if the teacher of the course has been banned
                                        courseDict.pop(randomisedCourse.get_courseID())
                                else:
                                    # user has bought the course
                                    courseDict.pop(randomisedCourse.get_courseID())

                        # appending course object for recommendations
                        count = 0
                        try:
                            while count != 2:
                                randomisedCourse = random.choice(recommendedCourseListByHighestTag)
                                if (randomisedCourse not in userPurchasedCourses) and (randomisedCourse not in recommendCourseList):
                                    recommendCourseList.append(randomisedCourse)
                                    count += 1
                                else:
                                    courseDict.pop(randomisedCourse.get_courseID())
                            while count != 3:
                                randomisedCourse = random.choice(recommendedCourseListBySecondHighestTag)
                                if (randomisedCourse not in userPurchasedCourses) and (randomisedCourse not in recommendCourseList):
                                    recommendCourseList.append(randomisedCourse)
                                    count += 1
                                else:
                                    courseDict.pop(randomisedCourse.get_courseID())
                        except:
                            print("Not enough courses with the user's corresponding tags.")

                    elif courseListLen == 1: # condition will be true when the user has only one unique highest tag
                        for key in courseDict:
                            courseObject = courseDict[key]
                            courseTag = courseObject.get_tags()
                            if courseTag == highestWatchedByTag:
                                if courseObject.get_courseID() not in userPurchasedCourses:
                                    if userDict.get(courseObject.get_userID()).get_status() == "Good":
                                        recommendedCourseListByHighestTag.append(courseObject)
                                    else:
                                        # if the teacher of the course has been banned
                                        courseDict.pop(randomisedCourse.get_courseID())
                                else:
                                    # user has bought the course
                                    courseDict.pop(randomisedCourse.get_courseID())

                        # appending course object for recommendations
                        count = 0
                        try:
                            while count != 2:
                                randomisedCourse = random.choice(recommendedCourseListByHighestTag)
                                if (randomisedCourse not in userPurchasedCourses) and (randomisedCourse not in recommendCourseList):
                                    recommendCourseList.append(randomisedCourse)
                                    count += 1
                                else:
                                    # already has been recommended or bought
                                    courseDict.pop(randomisedCourse.get_courseID())
                        except:
                            print("Not enough courses with the user's corresponding tags.")

                    # in the event where there is insufficient tags to recommend, it will randomly choose another course object
                    if len(recommendCourseList) != 3:
                        while len(recommendCourseList) != 3:
                            try:
                                randomisedCourse = random.choice(list(courseDict.values()))
                            except:
                                break
                            if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                                if (randomisedCourse not in userPurchasedCourses) and (randomisedCourse not in recommendCourseList):
                                    recommendCourseList.append(randomisedCourse)
                            else:
                                courseDict.pop(randomisedCourse.get_courseID())
                else:
                    for value in courseDict.values():
                        if userDict.get(value.get_courseID()).get_status() == "Good":
                            recommendCourseList.append(value)

                # logged in users
                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""
                return render_template('users/general/home.html', accType=accType, imagesrcPath=imagesrcPath, teacherPaymentAdded=teacherPaymentAdded, paymentComplete=paymentComplete, trendingCourseList=trendingCourseList, recommendCourseList=recommendCourseList, trendingCourseLen=len(trendingCourseList), recommendCourseLen=len(recommendCourseList), teacherUID=teacherUID)
            else:
                # admins
                recommendCourseList = get_random_courses(courseDict)
                return render_template('users/general/home.html', accType=accType, imagesrcPath=imagesrcPath, trendingCourseList=trendingCourseList, recommendCourseList=recommendCourseList, trendingCourseLen=len(trendingCourseList), recommendCourseLen=len(recommendCourseList))
        else:
            # users with invalid session, aka guest
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return redirect(url_for("home"))
    else:
        # guests
        if not request.cookies.get("guestSeenTags"):
            print("Guest user do not have cookie.")
            session["sessionCookieCreated"] = True
            return redirect(url_for("guestCookies"))
        else:
            print("Guest user has a cookie.")
            userTagDict = json.loads(b64decode(request.cookies.get("guestSeenTags")))

            # for recommendation algorithm
            recommendCourseList = []
            if len(courseDict) > 3:
                numberOfUniqueViews = checkUniqueElements(userTagDict)
                if numberOfUniqueViews > 1:
                    highestWatchedByTag = max(userTagDict, key=userTagDict.get)
                    userTagDict.pop(highestWatchedByTag)
                    numberOfUnqiueViews = checkUniqueElements(userTagDict)
                    if numberOfUnqiueViews > 1:
                        secondHighestWatchedByTag = max(userTagDict, key=userTagDict.get)
                    else:
                        # meaning that the user has watched some tags but only one tag is the highest while the rest of tags are the same (assuming the dictionary has not popped its highest tag yet)
                        try:
                            # hence choosing one other random course objects
                            while True:
                                randomisedCourse = random.choice(list(courseDict.values()))
                                if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                                    recommendCourseList.append(randomisedCourse)
                                    break
                                else:
                                    courseDict.pop(randomisedCourse.get_courseID())
                        except:
                            print("No course found.")
                else:
                    # meaning that the user has either not seen any tags or has watched an equal balance of various tags
                    # hence choosing three random course objects
                    try:
                        while len(recommendCourseList) != 3:
                            randomisedCourse = random.choice(list(courseDict.values()))
                            if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                                if randomisedCourse not in recommendCourseList:
                                    recommendCourseList.append(randomisedCourse)
                                else:
                                    # if course has been recommended already
                                    courseDict.pop(randomisedCourse.get_courseID())
                            else:
                                # if teacher has been banned
                                courseDict.pop(randomisedCourse.get_courseID())
                    except:
                        print("No courses found.")

                recommendedCourseListByHighestTag = []

                # checking current length of the recommendCourseList if the length is less than 3, then adding courses to make it a length of 3
                courseListLen = len(recommendCourseList)
                if courseListLen == 0: # condition will be true when the user has two unique highest tags
                    recommendedCourseListBySecondHighestTag = []
                    for key in courseDict:
                        courseObject = courseDict[key]
                        courseTag = courseObject.get_tags()
                        if courseTag == highestWatchedByTag:
                            if userDict.get(courseObject.get_userID()).get_status() == "Good":
                                recommendedCourseListByHighestTag.append(courseObject)
                            else:
                                # if the teacher of the course has been banned
                                courseDict.pop(randomisedCourse.get_courseID())
                        elif courseTag == secondHighestWatchedByTag:
                            if userDict.get(courseObject.get_userID()).get_status() == "Good":
                                recommendedCourseListBySecondHighestTag.append(courseObject)
                            else:
                                # if the teacher of the course has been banned
                                courseDict.pop(randomisedCourse.get_courseID())

                    # appending course object for recommendations
                    count = 0
                    try:
                        while count != 2:
                            randomisedCourse = random.choice(recommendedCourseListByHighestTag)
                            if randomisedCourse not in recommendCourseList:
                                recommendCourseList.append(randomisedCourse)
                                count += 1
                            else:
                                # course has been already recommended
                                courseDict.pop(randomisedCourse.get_courseID())
                        while count != 3:
                            randomisedCourse = random.choice(recommendedCourseListBySecondHighestTag)
                            if randomisedCourse not in recommendCourseList:
                                recommendCourseList.append(randomisedCourse)
                                count += 1
                            else:
                                # course has been already recommended
                                courseDict.pop(randomisedCourse.get_courseID())
                    except:
                        print("Not enough courses with the user's corresponding tags.")

                elif courseListLen == 1: # condition will be true when the user has one unique highest tag
                    for key in courseDict:
                        courseObject = courseDict[key]
                        courseTag = courseObject.get_tags()
                        if courseTag == highestWatchedByTag:
                            if userDict.get(courseObject.get_userID()).get_status() == "Good":
                                recommendedCourseListByHighestTag.append(courseObject)
                            else:
                                # if the teacher of the course has been banned
                                courseDict.pop(randomisedCourse.get_courseID())
                    count = 0
                    try:
                        while count != 2:
                            randomisedCourse = random.choice(recommendedCourseListByHighestTag)
                            if randomisedCourse not in recommendCourseList:
                                recommendCourseList.append(randomisedCourse)
                                count += 1
                            else:
                                # course has been already recommended
                                recommendedCourseListByHighestTag.pop(randomisedCourse)
                    except:
                        print("Not enough courses with the user's corresponding tags.")

                # in the event where there is insufficient tags to recommend, it will randomly choose another course object
                if len(recommendCourseList) != 3:
                    while len(recommendCourseList) != 3:
                        try:
                            randomisedCourse = random.choice(list(courseDict.values()))
                        except:
                            break
                        if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                            if randomisedCourse not in recommendCourseList:
                                recommendCourseList.append(randomisedCourse)
                        else:
                            # if the teacher of the course has been banned
                            courseDict.pop(randomisedCourse.get_courseID())
            else:
                for value in courseDict.values():
                    if userDict.get(value.get_courseID()).get_status() == "Good":
                        recommendCourseList.append(value)

        return render_template("users/general/home.html", accType="Guest", trendingCourseList=trendingCourseList, recommendCourseList=recommendCourseList, trendingCourseLen=len(trendingCourseList), recommendCourseLen=len(recommendCourseList))

# for setting a cookie for the guest for content personalisation
@app.route('/set_cookies')
@limiter.limit("10/second")
def guestCookies():
    res = make_response(redirect(url_for("home")))
    cookieCreated = False
    if "sessionCookieCreated" in session:
        cookieCreated = session["sessionCookieCreated"]
        print("Retrieved session cookie.")
    else:
        print("Guest user had disabled cookie.")
    if not request.cookies.get("guestSeenTags") and cookieCreated:
        # encoding the cookie value with base64 such that the guest cannot replace the cookie with tampered values in the dictionary too easily
        res.set_cookie(
            "guestSeenTags",
            value=b64encode(json.dumps({"Programming": 0,
            "Web_Development": 0,
            "Game_Development": 0,
            "Mobile_App_Development": 0,
            "Software_Development": 0,
            "Other_Development": 0,
            "Entrepreneurship": 0,
            "Project_Management": 0,
            "BI_Analytics": 0,
            "Business_Strategy": 0,
            "Other_Business": 0,
            "3D_Modelling": 0,
            "Animation": 0,
            "UX_Design": 0,
            "Design_Tools": 0,
            "Other_Design": 0,
            "Digital_Photography": 0,
            "Photography_Tools": 0,
            "Video_Production": 0,
            "Video_Design_Tools": 0,
            "Other_Photography_Videography": 0,
            "Science": 0,
            "Math": 0,
            "Language": 0,
            "Test_Prep": 0,
            "Other_Academics": 0}).encode("utf-8")),
            expires=datetime.now() + timedelta(days=90)
        )
    if not request.cookies.get("guestSeenTags") and cookieCreated == False:
        return redirect("/home/no_cookies") # if the user had disabled cookies
    return res

@app.route('/home/no_cookies')
@limiter.limit("30/second") # to prevent ddos attacks
def homeNoCookies():
    if "userSession" not in session and "adminSession" not in session: # since if the user is logged in, it means that their cookie is enabled as the login uses session cookies
        courseDict = {}
        userDict = {}
        try:
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
            courseDict = db['Courses']
            userDict = db['Users']
            db.close()
            print("File found.")
        except:
            print("File could not be found.")
            # since the shelve files could not be found, it will create a placeholder/empty shelve files
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            db["Courses"] = courseDict
            db['Users'] = userDict
            db.close()

        # for trending algorithm
        trendingCourseList = []
        count = 0
        try:
            courseDictCopy = copy.deepcopy(courseDict)
            while count != 3:
                highestViewedCourse = max(courseDictCopy, key=lambda courseID: courseDictCopy[courseID].get_views())
                # retrieve teacher user ID
                courseTeacherID = courseDict.get(highestViewedCourse).get_userID()
                # based on the teacher user ID and check if the teacher is banned
                if userDict.get(courseTeacherID).get_status() == "Good":
                    print("Username:", userDict.get(courseTeacherID).get_username() )
                    print("User status:", userDict.get(courseTeacherID).get_status() )
                    # append course object if the teacher is not banned
                    trendingCourseList.append(courseDict.get(highestViewedCourse))
                    courseDictCopy.pop(highestViewedCourse)
                    count += 1
                else:
                    # remove the course object from the courseDictCopy if the teacher is banned
                    courseDictCopy.pop(highestViewedCourse)
        except:
            print("No courses or not enough courses (requires 3 courses)")
            trendingCourseList = []
            for values in courseDict.values():
                if userDict.get(values.get_userID()).get_status() == "Good":
                    trendingCourseList.append(values)

        recommendCourseList = get_random_courses(courseDict)

        return render_template("users/general/home.html", accType="Guest", trendingCourseList=trendingCourseList, recommendCourseList=recommendCourseList, trendingCourseLen=len(trendingCourseList), recommendCourseLen=len(recommendCourseList))
    else:
        return redirect(url_for("home"))

"""End of Home pages by Jason"""

"""Editing Cookie"""

@app.route('/edit_cookie/<teacherUID>/<courseID>/<courseTag>')
@limiter.limit("10/second")
def guestEditCookie(teacherUID, courseID, courseTag):
    redirectURL = "/" + teacherUID + "/" + courseID
    res = make_response(redirect(redirectURL))
    cookieCreated = False
    if "sessionCookieCreated" in session:
        cookieCreated = session["sessionCookieCreated"]
        print("Retrieved session cookie.")
    else:
        print("Guest user had disabled cookie.")
    if request.cookies.get("guestSeenTags") and cookieCreated:
        # if user have an existing cookie with the name guestSeenTags
        try:
            userTagDict = json.loads(b64decode(request.cookies.get("guestSeenTags")))
            if courseTag in userTagDict:
                userTagDict[courseTag] += 1
                res.set_cookie(
                    "guestSeenTags",
                    value=b64encode(json.dumps(userTagDict).encode("utf-8")),
                    expires=datetime.now() + datetime.timedelta(days=90)
                )
        except:
            print("Error with editing guest's cookie.")
            # if the guest user had tampered with the cookie value
            res.set_cookie(
                "guestSeenTags",
                value=b64encode(json.dumps({"Programming": 0,
                "Web_Development": 0,
                "Game_Development": 0,
                "Mobile_App_Development": 0,
                "Software_Development": 0,
                "Other_Development": 0,
                "Entrepreneurship": 0,
                "Project_Management": 0,
                "BI_Analytics": 0,
                "Business_Strategy": 0,
                "Other_Business": 0,
                "3D_Modelling": 0,
                "Animation": 0,
                "UX_Design": 0,
                "Design_Tools": 0,
                "Other_Design": 0,
                "Digital_Photography": 0,
                "Photography_Tools": 0,
                "Video_Production": 0,
                "Video_Design_Tools": 0,
                "Other_Photography_Videography": 0,
                "Science": 0,
                "Math": 0,
                "Language": 0,
                "Test_Prep": 0,
                "Other_Academics": 0}).encode("utf-8")),
                expires=datetime.now() + timedelta(days=90)
            )
    elif not request.cookies.get("guestSeenTags") and cookieCreated:
        # if user do not have an existing cookie with the name guestSeenTags
        originalCourseTagDict = {"Programming": 0,
                                "Web_Development": 0,
                                "Game_Development": 0,
                                "Mobile_App_Development": 0,
                                "Software_Development": 0,
                                "Other_Development": 0,
                                "Entrepreneurship": 0,
                                "Project_Management": 0,
                                "BI_Analytics": 0,
                                "Business_Strategy": 0,
                                "Other_Business": 0,
                                "3D_Modelling": 0,
                                "Animation": 0,
                                "UX_Design": 0,
                                "Design_Tools": 0,
                                "Other_Design": 0,
                                "Digital_Photography": 0,
                                "Photography_Tools": 0,
                                "Video_Production": 0,
                                "Video_Design_Tools": 0,
                                "Other_Photography_Videography": 0,
                                "Science": 0,
                                "Math": 0,
                                "Language": 0,
                                "Test_Prep": 0,
                                "Other_Academics": 0}
        try:
            originalCourseTagDict[courseTag] += 1
        except:
            print("Tag does not exist.")

        res.set_cookie(
            "guestSeenTags",
            value=b64encode(json.dumps(originalCourseTagDict).encode("utf-8")),
            expires=datetime.now() + datetime.timedelta(days=90)
        )

    if not request.cookies.get("guestSeenTags") and cookieCreated == False:
        redirectURL = redirectURL + "/no_cookies"
        return redirect(redirectURL) # if the user had disabled cookies
    return res

"""End of Editing Cookie"""

"""User login and logout by Jason"""

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10/second") # to prevent attackers from trying to crack passwords or doing enumeration attacks by sending too many automated requests from their ip address
def userLogin():
    if "userSession" not in session and "adminSession" not in session:
        create_login_form = Forms.CreateLoginForm(request.form)
        if "passwordUpdated" in session:
            passwordUpdated = True
            session.pop("passwordUpdated", None)
        else:
            passwordUpdated = False

        if request.method == "POST" and create_login_form.validate():
            emailInput = sanitise(create_login_form.email.data.lower())
            passwordInput = create_login_form.password.data
            userDict = {}
            try:
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
                userDict = db['Users']
                db.close()
                print("File found.")
            except:
                print("File could not be found.")
                # since the shelve files could not be found, it will create a placeholder/empty shelve files so that user can submit the login form but will still be unable to login
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
                db["Users"] = userDict
                db.close()

            # Declaring the 4 variables below to prevent UnboundLocalError
            email_found = False
            password_matched = False
            passwordShelveData = ""
            emailShelveData = ""

            # Checking the email input and see if it matches with any in the database
            print("Retrieving emails from database.")
            for key in userDict:
                emailShelveData = userDict[key].get_email()
                if emailInput == emailShelveData:
                    email_key = userDict[key]
                    email_found = True
                    print("Email in database:", emailShelveData)
                    print("Email Input:", emailInput)
                    break

            # if the email is found in the shelve database, it will then validate the password input and see if it matches with the one in the database
            if email_found:
                password_matched = email_key.verify_password(passwordInput)

                # printing for debugging purposes
                if password_matched:
                    print("Correct password!")
                else:
                    print("Password incorrect.")
            else:
                print("User email not found.")

            if email_found and password_matched:
                print("User validated...")

                # checking if the user is banned
                accGoodStatus = email_key.get_status()
                if accGoodStatus == "Good":
                    # setting the user session based on the user's user ID
                    userID = email_key.get_user_id()
                    session["userSession"] = userID
                    print("User account not banned, login successful.")
                    return redirect(url_for("home"))
                else:
                    print("User account banned.")
                    return render_template('users/guest/login.html', form=create_login_form, banned=True)
            else:
                return render_template('users/guest/login.html', form=create_login_form, failedAttempt=True)
        else:
            # for notifying if they have verified their email from the link in their email
            if "emailVerified" in session:
                emailVerified = True
                session.pop("emailVerified", None)
            else:
                emailVerified = False
            # for notifying if the email verification link has expired/is invalid
            if "emailTokenInvalid" in session:
                emailTokenInvalid = True
                session.pop("emailTokenInvalid", None)
            else:
                emailTokenInvalid = False
            # for notifying if they have already verified their email (traversal attack)
            if "emailFailed" in session:
                emailAlreadyVerified = True
                session.pop("emailFailed", None)
            else:
                emailAlreadyVerified = False

            return render_template('users/guest/login.html', form=create_login_form, passwordUpdated=passwordUpdated, emailVerified=emailVerified, emailTokenInvalid=emailTokenInvalid, emailAlreadyVerified=emailAlreadyVerified)
    else:
        return redirect(url_for("home"))

@app.route('/logout')
@limiter.limit("30/second") # to prevent ddos attacks
def logout():
    if "userSession" in session or "adminSession" in session:
        session.clear()
    else:
        return redirect(url_for("home"))

    # sending a session data so that when it redirects the user to the homepage, jinja2 will render out a logout alert
    session["recentlyLoggedOut"] = True
    return redirect(url_for("home"))

"""End of User login and logout by Jason"""

"""Reset Password by Jason"""

@app.route('/reset_password', methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def requestPasswordReset():
    if "userSession" not in session and "adminSession" not in session:
        create_request_form = Forms.RequestResetPasswordForm(request.form)
        if "invalidToken" in session:
            invalidToken = True
            session.pop("invalidToken", None)
        else:
            invalidToken = False

        if request.method == "POST" and create_request_form.validate():
            emailInput = sanitise(create_request_form.email.data.lower())
            userDict = {}
            try:
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
                userDict = db['Users']
                db.close()
                print("File found.")
                fileFound = True
            except:
                print("File could not be found.")
                fileFound = False
                # since the shelve files could not be found, it will create a placeholder/empty shelve files so that user can submit the login form but will still be unable to login
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
                db["Users"] = userDict
                db.close()

            if fileFound:
                # Declaring the 2 variables below to prevent UnboundLocalError
                email_found = False
                emailShelveData = ""

                # Checking the email input and see if it matches with any in the database
                print("Retrieving emails from database.")
                for key in userDict:
                    emailShelveData = userDict[key].get_email()
                    if emailInput == emailShelveData:
                        email_key = userDict[key]
                        email_found = True
                        print("Email in database:", emailShelveData)
                        print("Email Input:", emailInput)
                        break
                        
                if email_found:
                    print("User email found...")

                    # checking if the user is banned
                    accGoodStatus = email_key.get_status()
                    if accGoodStatus == "Good":
                        try:
                            send_reset_email(emailInput, email_key)
                        except:
                            print("Email server is down or its port is blocked")
                        print("Email sent")
                        return render_template('users/guest/request_password_reset.html', form=create_request_form, emailSent=True, emailInput=emailInput)
                    else:
                        # email found in database but the user is banned.
                        # However, it will still send an "email sent" alert to throw off enumeration attacks on banned accounts
                        print("User account banned, email not sent.")
                        return render_template('users/guest/request_password_reset.html', form=create_request_form, emailSent=True, emailInput=emailInput)
                else:
                    print("User email not found.")
                    # email not found in database, but will send an "email sent" alert to throw off enumeration attacks
                    return render_template('users/guest/request_password_reset.html', form=create_request_form, emailSent=True, emailInput=emailInput)
            else:
                # email not found in database, but will send an "email sent" alert to throw off enumeration attacks
                print("No user account records found.")
                print("Email Input:", emailInput)
                return render_template('users/guest/request_password_reset.html', form=create_request_form, emailSent=True, emailInput=emailInput)
        else:
            return render_template('users/guest/request_password_reset.html', form=create_request_form, invalidToken=invalidToken)
    else:
        return redirect(url_for("home"))

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def resetPassword(token):
    if "userSession" not in session and "adminSession" not in session:
        validateToken = verify_reset_token(token)
        if validateToken != None:
            create_reset_password_form = Forms.CreateResetPasswordForm(request.form)
            if request.method == "POST" and create_reset_password_form.validate():
                password = create_reset_password_form.resetPassword.data
                confirmPassword = create_reset_password_form.confirmPassword.data

                if password == confirmPassword:
                    userDict = {}
                    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
                    try:
                        if 'Users' in db:
                            userDict = db['Users']
                        else:
                            db.close()
                            print("No user data in user shelve files.")
                            # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the user to the homepage
                            return redirect(url_for("home"))
                    except:
                        db.close()
                        print("Error in retrieving Users from user.db")
                        return redirect(url_for("home"))

                    userKey = userDict.get(validateToken)
                    # checking if the user is banned
                    accGoodStatus = userKey.get_status()
                    if accGoodStatus == "Good":
                        userKey.set_password(password)
                        db["Users"] = userDict
                        db.close()
                        print("Password Reset Successful.")
                        session["passwordUpdated"] = True
                        return redirect(url_for("userLogin"))
                    else:
                        print("User account banned.")
                        return render_template('users/guest/reset_password.html', form=create_reset_password_form, banned=True)
                else:
                    return render_template('users/guest/reset_password.html', form=create_reset_password_form, pwd_were_not_matched=True)
            else:
                return render_template('users/guest/reset_password.html', form=create_reset_password_form)
        else:
            session["invalidToken"] = True
            return redirect(url_for("requestPasswordReset"))
    else:
        return redirect(url_for("userProfile"))

"""End of Reset Password by Jason"""

"""Student signup process by Jason"""

@app.route('/signup', methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def userSignUp():
    if "userSession" not in session and "adminSession" not in session:
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

            emailInput = sanitise(create_signup_form.email.data.lower())
            emailValid = validate_email(emailInput)
            if emailValid:

                usernameInput = sanitise(create_signup_form.username.data)

                # Retrieving data from shelve for duplicate data checking
                userDict = {}
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")  # "c" flag as to create the files if there were no files to retrieve from and also to create the user if the validation conditions are met
                try:
                    if 'Users' in db:
                        userDict = db['Users']
                    else:
                        print("No user data in user shelve files.")
                        db["Users"] = userDict
                except:
                    db.close()
                    print("Error in retrieving Users from user.db")
                    return redirect(url_for("home"))

                # Checking duplicates for email and username
                email_duplicates = check_duplicates(emailInput, userDict, "email")
                username_duplicates = check_duplicates(usernameInput, userDict, "username")

                # If there were no duplicates and passwords entered were the same, create a new user
                if (pwd_were_not_matched == False) and (email_duplicates == False) and (username_duplicates == False):
                    # setting user ID for the user
                    userID = generate_ID(userDict)
                    print("User ID setted: ", userID)

                    user = Student.Student(userID, usernameInput, emailInput, passwordInput)

                    userDict[userID] = user
                    db["Users"] = userDict

                    db.close()
                    print("User added.")
                    try:
                        send_verify_email(emailInput, userID)
                    except:
                        print("Email server is down or its port is blocked")

                    session["userSession"] = userID
                    return redirect(url_for("home"))
                else:
                    # if there were still duplicates or passwords entered were not the same, used Jinja to show the error messages
                    db.close()
                    print("Validation conditions were not met.")
                    return render_template('users/guest/signup.html', form=create_signup_form, email_duplicates=email_duplicates, username_duplicates=username_duplicates, pwd_were_not_matched=pwd_were_not_matched)
            else:
                return render_template('users/guest/signup.html', form=create_signup_form, emailInvalid=True)
        else:
            return render_template('users/guest/signup.html', form=create_signup_form)
    else:
        return redirect(url_for("home"))

"""End of Student signup process by Jason"""

"""Email verification by Jason"""

@app.route("/generate_verify_email_token")
@limiter.limit("30/second") # to prevent ddos attacks
def verifyEmail():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)
        email = userKey.get_email()
        userID = userKey.get_user_id()
        if userFound and accGoodStatus:
            emailVerified = userKey.get_email_verification()
            if emailVerified == "Not Verified":
                session["emailVerifySent"] = True
                try:
                    send_another_verify_email(email, userID)
                except:
                    print("Email server is down or its port is blocked")
            else:
                session["emailFailed"] = False
                print("User's email already verified.")
            return redirect(url_for("userProfile"))
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the login page
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route("/verify_email/<token>")
@limiter.limit("30/second") # to prevent ddos attacks
def verifyEmailToken(token):
    if "adminSession" not in session:
        validateToken = verify_email_token(token)
        if validateToken != None:

            userDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("home"))

            userKey = userDict.get(validateToken)
            # checking if the user is banned
            accGoodStatus = userKey.get_status()
            if accGoodStatus == "Good":
                emailVerification = userKey.get_email_verification()
                if emailVerification == "Not Verified":
                    userKey.set_email_verification("Verified")
                    db["Users"] = userDict
                    db.close()
                    session["emailVerified"] = True
                    if "userSession" in session:
                        return redirect(url_for("userProfile"))
                    else:
                        return redirect(url_for("userLogin"))
                else:
                    db.close()
                    session["emailFailed"] = True
                    if "userSession" in session:
                        return redirect(url_for("userProfile"))
                    else:
                        print("Email already verified")
                        return redirect(url_for("userLogin"))
            else:
                db.close()
                print("User account banned.")
                return redirect(url_for("home"))
        else:
            session["emailTokenInvalid"] = True
            print("Invalid/Expired Token.")
            if "userSession" in session:
                return redirect(url_for("userProfile"))
            else:
                return redirect(url_for("userLogin"))
    else:
        print("Admin is logged in.")
        return redirect(url_for("home"))

"""End of Email verification by Jason"""

"""Teacher's signup process by Jason"""

@app.route('/teacher_signup', methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def teacherSignUp():
    if "userSession" not in session and "adminSession" not in session:
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

            emailInput = sanitise(create_teacher_sign_up_form.email.data.lower())
            emailValid = validate_email(emailInput)

            if emailValid:
                usernameInput = sanitise(create_teacher_sign_up_form.username.data)

                # Retrieving data from shelve for duplicate data checking
                userDict = {}
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")  # "c" flag as to create the files if there were no files to retrieve from and also to create the user if the validation conditions are met
                try:
                    if 'Users' in db:
                        userDict = db['Users']
                    else:
                        print("No user data in user shelve files")
                        db["Users"] = userDict
                except:
                    db.close()
                    print("Error in retrieving Users from user.db")
                    return redirect(url_for("home"))

                # Checking duplicates for email and username
                email_duplicates = check_duplicates(emailInput, userDict, "email")
                username_duplicates = check_duplicates(usernameInput, userDict, "username")

                if (pwd_were_not_matched == False) and (email_duplicates == False) and (username_duplicates == False):
                    print("User info validated.")
                    # setting user ID for the teacher
                    userID = generate_ID(userDict)
                    print("User ID setted: ", userID)

                    user = Teacher.Teacher(userID, usernameInput, emailInput, passwordInput)
                    user.set_teacher_join_date(date.today())

                    userDict[userID] = user
                    db["Users"] = userDict

                    session["teacher"] = userID # to send the user ID under the teacher session for user verification in the sign up payment process

                    print(userDict)
                    print("Teacher added.")

                    db.close()
                    try:
                        send_verify_email(emailInput, userID)
                    except:
                        print("Email server is down or its port is blocked")

                    session["userSession"] = userID
                    return redirect(url_for("signUpPayment"))
                else:
                    # if there were still duplicates or passwords entered were not the same, used Jinja to show the error messages
                    db.close()
                    print("Validation conditions were not met.")
                    return render_template('users/guest/teacher_signup.html', form=create_teacher_sign_up_form, email_duplicates=email_duplicates, username_duplicates=username_duplicates, pwd_were_not_matched=pwd_were_not_matched)
            else:
                return render_template('users/guest/teacher_signup.html', form=create_teacher_sign_up_form, invalidEmail=True)
        else:
            return render_template('users/guest/teacher_signup.html', form=create_teacher_sign_up_form)
    else:
        if "userSession" in session:
            return redirect(url_for("changeAccountType"))
        else:
            return redirect(url_for("home"))

@app.route('/sign_up_payment', methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def signUpPayment():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]
        if "teacher" in session:
            teacherID = session["teacher"]
            if teacherID == userSession:
                # Retrieving data from shelve and to set the teacher's payment method info data
                userDict = {}
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
                try:
                    if 'Users' in db:
                        # there must be user data in the user shelve files as this is the 2nd part of the teacher signup process which would have created the teacher acc and store in the user shelve files previously
                        userDict = db['Users']
                    else:
                        db.close()
                        print("No user data in user shelve files.")
                        # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                        session.clear()
                        return redirect(url_for("home"))
                except:
                    db.close()
                    print("Error in retrieving Users from user.db")
                    return redirect(url_for("home"))

                # retrieving the object from the shelve based on the user's email
                teacherKey, userFound, accGoodStatus, accType = get_key_and_validate(teacherID, userDict)

                create_teacher_payment_form = Forms.CreateAddPaymentForm(request.form)
                if request.method == 'POST' and create_teacher_payment_form.validate():
                    if userFound and accGoodStatus:
                        # further checking to see if the user ID in the session is equal to the teacher ID session from the teacher sign up process

                        cardName = sanitise(create_teacher_payment_form.cardName.data)

                        cardNo = sanitise(create_teacher_payment_form.cardNo.data)
                        cardValid = validate_card_number(cardNo)

                        cardType = get_credit_card_type(cardNo, cardValid)

                        cardExpiry = sanitise(create_teacher_payment_form.cardExpiry.data)
                        cardExpiryValid = validate_expiry_date(cardExpiry)

                        if cardValid and cardExpiryValid:
                            if cardType != False: # checking if the card type is supported
                                # setting the teacher's payment method which in a way editing the teacher's object
                                teacherKey.set_card_name(cardName)
                                teacherKey.set_card_no(cardNo)
                                cardExpiry = cardExpiryStringFormatter(cardExpiry)
                                teacherKey.set_card_expiry(cardExpiry)
                                teacherKey.set_card_type(cardType)
                                teacherKey.display_card_info()
                                db['Users'] = userDict
                                print("Payment added")
                                db.close()

                                session.pop("teacher", None) # deleting data from the session after registering the payment method
                                session["teacherPaymentAdded"] = True
                                return redirect(url_for("home"))
                            else:
                                return render_template('users/guest/teacher_signup_payment.html', form=create_teacher_payment_form, invalidCardType=True, accType=accType)
                        else:
                            db.close()
                            return render_template('users/guest/teacher_signup_payment.html', form=create_teacher_payment_form, cardValid=cardValid, cardExpiryValid=cardExpiryValid, accType=accType)
                    else:
                        db.close()
                        print("User not found or is banned.")
                        # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                        session.clear()
                        return redirect(url_for("home"))
                else:
                    db.close()
                    return render_template('users/guest/teacher_signup_payment.html', form=create_teacher_payment_form, accType=accType)
            else:
                # clear the teacher session if the logged in user somehow have a teacher session, it will then redirect them to the home page
                session.pop("teacher", None)
                return redirect(url_for("home"))
        else:
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))

"""End of Teacher's login/signup process by Jason"""

"""Admin login by Jason"""

@app.route('/admin_login', methods=['GET', 'POST'])
@limiter.limit("5/second") # to prevent attackers from trying to crack passwords or doing enumeration attacks by sending too many automated requests from their ip address
def adminLogin():
    if "adminSession" not in session and "userSession" not in session:
        create_login_form = Forms.CreateLoginForm(request.form)
        if request.method == "POST" and create_login_form.validate():
            emailInput = sanitise(create_login_form.email.data.lower())
            passwordInput = str(create_login_form.password.data)
            try:
                adminDict = {}
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "r")
                adminDict = db['Admins']
                db.close()
                print("File found.")
            except:
                print("File could not be found.")
                # since the shelve files could not be found, it will create a placeholder/empty shelve files so that user can submit the login form but will still be unable to login
                adminDict = {}
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "c")
                db["Admins"] = adminDict
                db.close()

            # Declaring the 4 variables below to prevent UnboundLocalError
            email_found = False
            password_matched = False
            passwordShelveData = ""
            emailShelveData = ""

            # Checking the email input and see if it matches with any in the database
            print("Retrieving admin emails from admin database.")
            for key in adminDict:
                emailShelveData = adminDict[key].get_email()
                if emailInput == emailShelveData:
                    email_key = adminDict[key]
                    email_found = True
                    print("Email in database:", emailShelveData)
                    print("Email Input:", emailInput)
                    break

            # if the email is found in the shelve database, it will then validate the password input and see if it matches with the one in the database
            if email_found:
                password_matched = email_key.verify_password(passwordInput)

                if password_matched:
                    print("Correct password!")
                else:
                    print("Password incorrect.")
            else:
                print("Admin email not found in admin database.")

            if email_found and password_matched:
                print("Admin account validated...")

                # checking if the admin account is active
                accActiveStatus = email_key.get_status()
                if accActiveStatus == "Active":
                    # setting the user session based on the user's user ID
                    userID = email_key.get_user_id()
                    session["adminSession"] = userID
                    print(userID)
                    print("Admin account active, login successful.")
                    return redirect(url_for("home"))
                else:
                    print("Admin account inactive.")
                    return render_template('users/guest/admin_login.html', form=create_login_form, notActive=True)
            else:
                print("Failed to login.")
                return render_template('users/guest/admin_login.html', form=create_login_form, failedAttempt=True)
        else:
            return render_template('users/guest/admin_login.html', form=create_login_form)
    else:
        return redirect(url_for("home"))

"""End of Admin login by Jason"""

"""Admin profile settings by Jason"""

@app.route('/admin_profile', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def adminProfile():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)

        userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)

        if userFound and accActive:
            username = userKey.get_username()
            email = userKey.get_email()
            admin_id = userKey.get_user_id()

            # checking sessions if any of the user's acc info has changed
            if "username_changed" in session:
                usernameChanged = True
                session.pop("username_changed", None)
                print("Username recently changed?:", usernameChanged)
            else:
                usernameChanged = False
                print("Username recently changed?:", usernameChanged)

            if "email_updated" in session:
                emailChanged = True
                session.pop("email_updated", None)
                print("Email recently changed?:", emailChanged)
            else:
                emailChanged = False
                print("Email recently changed?:", emailChanged)

            if "password_changed" in session:
                passwordChanged = True
                session.pop("password_changed", None)
                print("Password recently changed?:", passwordChanged)
            else:
                passwordChanged = False
                print("Password recently changed?:", passwordChanged)

            return render_template('users/admin/admin_profile.html', username=username, email=email, usernameChanged=usernameChanged, emailChanged=emailChanged, passwordChanged=passwordChanged, admin_id=admin_id)
        else:

            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/admin_change_username", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def adminChangeUsername():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        create_update_username_form = Forms.CreateChangeUsername(request.form)
        if request.method == "POST" and create_update_username_form.validate():
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "c")
            try:
                if 'Admins' in db:
                    adminDict = db['Admins']
                else:
                    db.close()
                    print("Admin account data in shelve is empty.")
                    session.clear() # since the file data is empty either due to the admin deleting the admin shelve files or something else, it will clear any session and redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Admins from admin.db")
                return redirect(url_for("home"))

            userKey, userFound, accActive = admin_get_key_and_validate(adminSession, adminDict)

            if userFound and accActive:
                updatedUsername = sanitise(create_update_username_form.updateUsername.data)
                currentUsername = userKey.get_username()

                if updatedUsername != currentUsername:
                    # checking duplicates for username
                    username_duplicates = False
                    print("Retrieving usernames from database.")
                    for key in adminDict:
                        usernameShelveData = adminDict[key].get_username()
                        if updatedUsername == usernameShelveData:
                            print("Verdict: Username already taken.")
                            username_duplicates = True
                            break

                    if username_duplicates == False:
                        print("Verdict: Username is unique.")
                        # updating username of the user
                        userKey.set_username(updatedUsername)
                        db['Admins'] = adminDict
                        print("Username updated")

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of password
                        session["username_changed"] = True

                        db.close()
                        return redirect(url_for("adminProfile"))
                    else:
                        return render_template('users/admin/change_username.html', form=create_update_username_form, username_duplicates=True)
                else:
                    print("Update username input same as user's current username")
                    return render_template('users/admin/change_username.html', form=create_update_username_form, sameUsername=True)
            else:
                db.close()
                print("Admin account is not found or is not active.")
                # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
                session.clear()
                return redirect(url_for("adminLogin"))
        else:
            return render_template('users/admin/change_username.html', form=create_update_username_form)

    else:
        return redirect(url_for("home"))

@app.route("/admin_change_email", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def adminChangeEmail():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        create_update_email_form = Forms.CreateChangeEmail(request.form)
        if request.method == "POST" and create_update_email_form.validate():
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "c")
            try:
                if 'Admins' in db:
                    adminDict = db['Admins']
                else:
                    db.close()
                    print("Admin account data in shelve is empty.")
                    session.clear() # since the file data is empty either due to the admin deleting the admin shelve files or something else, it will clear any session and redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Admins from admin.db")
                return redirect(url_for("home"))

            userKey, userFound, accActive = admin_get_key_and_validate(adminSession, adminDict)

            if userFound and accActive:
                updatedEmail = sanitise(create_update_email_form.updateEmail.data.lower())
                currentEmail = userKey.get_email()

                # Checking duplicates for email
                email_duplicates = False
                if updatedEmail != currentEmail:
                    print("Retrieving emails from database.")
                    for key in adminDict:
                        emailShelveData = adminDict[key].get_email()
                        if updatedEmail == emailShelveData:
                            print("Verdict: User email already exists.")
                            email_duplicates = True
                            break          

                    if email_duplicates == False:
                        print("Verdict: User email is unique.")
                        # updating email of the admin
                        userKey.set_email(updatedEmail)
                        db['Admins'] = adminDict
                        print("Email updated")

                        # sending a session data so that when it redirects the admin to the admin profile page, jinja2 will render out an alert of the change of email
                        session["email_updated"] = True

                        db.close()
                        return redirect(url_for("adminProfile"))
                    else:
                        db.close()
                        return render_template('users/admin/change_email.html', form=create_update_email_form, email_duplicates=True)
                else:
                    db.close()
                    print("User updated email input is the same as their current email")
                    return render_template('users/admin/change_email.html', form=create_update_email_form, sameEmail=True)
            else:
                db.close()
                print("Admin account is not found or is not active.")
                # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
                session.clear()
                return redirect(url_for("adminLogin"))
        else:
            return render_template('users/admin/change_email.html', form=create_update_email_form)
    else:
        return redirect(url_for("home"))

@app.route("/admin_change_password", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def adminChangePassword():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        create_update_password_form = Forms.CreateChangePasswordForm(request.form)
        if request.method == "POST" and create_update_password_form.validate():

            # declaring passwordNotMatched, passwordVerification, and errorMessage variable to initialise and prevent unboundLocalError
            passwordNotMatched = True
            passwordVerification = False

            # for jinja2
            errorMessage = False

            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "c")
            try:
                if 'Admins' in db:
                    adminDict = db['Admins']
                else:
                    db.close()
                    print("Admin account data in shelve is empty.")
                    session.clear() # since the file data is empty either due to the admin deleting the admin shelve files or something else, it will clear any session and redirect the user to the homepage
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Admins from admin.db")
                return redirect(url_for("home"))

            userKey, userFound, accActive = admin_get_key_and_validate(adminSession, adminDict)

            if userFound and accActive:
                currentPassword = create_update_password_form.currentPassword.data
                updatedPassword = create_update_password_form.updatePassword.data
                confirmPassword = create_update_password_form.confirmPassword.data

                # validation starts
                print("Updated password input:", updatedPassword)
                print("Confirm password input", confirmPassword)
                if updatedPassword == confirmPassword:
                    passwordNotMatched = False
                    print("New and confirm password inputs matched")
                else:
                    print("New and confirm password inputs did not match")

                passwordVerification = userKey.verify_password(currentPassword)
                oldPassword = userKey.verify_password(updatedPassword)

                # printing message for debugging purposes
                if passwordVerification:
                    print("User identity verified")
                else:
                    print("Current password input hash did not match with the one in the shelve database")

                # if there any validation error, errorMessage will become True for jinja2 to render the error message
                if passwordVerification == False or passwordNotMatched:
                    db.close()
                    errorMessage = True
                    return render_template('users/admin/change_password.html', form=create_update_password_form, errorMessage=errorMessage)
                else:
                    if oldPassword:
                        db.close()
                        print("User cannot change password to their current password!")
                        return render_template('users/admin/change_password.html', form=create_update_password_form, samePassword=True)
                    else:
                        # updating password of the user once validated
                        userKey.set_password(updatedPassword)
                        db['Admins'] = adminDict
                        print("Password updated")
                        db.close()

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of password
                        session["password_changed"] = True
                        return redirect(url_for("adminProfile"))
            else:
                db.close()
                print("Admin account is not found or is not active.")
                # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
                session.clear()
                return redirect(url_for("adminLogin"))

        else:
            return render_template('users/admin/change_password.html', form=create_update_password_form)
    else:
        return redirect(url_for("home"))

"""Admin profile settings by Jason"""

"""User Management for Admins by Jason"""

@app.route("/user_management/page/<int:pageNum>", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def userManagement(pageNum):
    if "adminSession" in session:
        adminSession = session["adminSession"]

        # removing session created when searching for users
        if "searchedPageRoute" in session:
            session.pop("searchedPageRoute", None)

        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)
        if userFound and accActive:
            userDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                    print("Users found")
                else:
                    db["Users"] = userDict
                    print("No user data in user shelve files.")
            except:
                print("Error in retrieving Users from user.db")

            # for resetting the user's password and updating the user's email for account recovery
            admin_reset_password_form = Forms.AdminResetPasswordForm(request.form)
            if request.method == "POST" and admin_reset_password_form.validate():
                password = generate_password()
                email = sanitise(admin_reset_password_form.email.data)
                validEmail = validate_email(email)

                # for redirecting the admin to the user management page that he/she was in
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

                if validEmail:
                    userID = int(request.form["userID"])
                    userKey = userDict.get(userID)
                    oldEmail = userKey.get_email()
                    duplicateEmail = check_duplicates(email, userDict, "email")
                    if oldEmail != email:
                        if duplicateEmail == False:
                            if userKey != None:
                                # changing the password of the user
                                userKey.set_password(password)
                                userKey.set_email(email)
                                userKey.set_email_verification("Not Verified")
                                db["Users"] = userDict
                                db.close()
                                try:
                                    send_admin_reset_email(email, password) # sending an email to the user to notify them of the change
                                except:
                                    print("Email server is down or its port is blocked")
                                print("User account recovered successfully and email sent.")
                                return redirect(redirectURL)
                            else:
                                db.close()
                                print("Error in retrieving user object.")
                                return redirect(redirectURL)
                        else:
                            db.close()
                            print("Inputted new user's email is not unique.")
                            session["duplicateEmail"] = True
                            return redirect(redirectURL)
                    else:
                        db.close()
                        print("User's new email inputted is the same as the old email.")
                        session["sameEmail"] = True
                        return redirect(redirectURL)
                else:
                    db.close()
                    print("Inputted new user's email is invalid.")
                    session["invalidEmail"] = True
                    return redirect(redirectURL)
            else:
                userList = []
                for users in userDict:
                    user = userDict.get(users)
                    userList.append(user)

                maxItemsPerPage = 10 # declare the number of items that can be seen per pages
                userListLen = len(userList) # get the length of the userList
                maxPages = math.ceil(userListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number

                # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/page/0" or negative numbers, "user_management/page/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/page/999999"
                if pageNum < 0:
                    return redirect("/user_management/page/0")
                elif userListLen > 0 and pageNum == 0:
                    return redirect("/user_management/page/1")
                elif pageNum > maxPages:
                    redirectRoute = "/user_management/page/" + str(maxPages)
                    return redirect(redirectRoute)
                else:
                    # pagination algorithm starts here
                    userList = userList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                    pageNumForPagination = pageNum - 1 # minus for the paginate function
                    paginatedUserList = paginate(userList, pageNumForPagination, maxItemsPerPage)
                    paginationList = get_pagination_button_list(pageNum, maxPages)

                    session["pageNum"] = pageNum # for uxd so that the admin can be on the same page after managing the user such as deleting the user account, etc.

                    previousPage = pageNum - 1
                    nextPage = pageNum + 1

                    # auto fixing user profile image if the user has uploaded but the image is no longer on the web server directory
                    for value in paginatedUserList:
                        userProfileFileName = value.get_profile_image()
                        if (bool(userProfileFileName) == True) and (Path(construct_path(PROFILE_UPLOAD_PATH, userProfileFileName)).is_file() == False):
                            value.set_profile_image("")

                    db["Users"] = userDict
                    db.close()

                    if "invalidEmail" in session:
                        invalidEmail = True
                        session.pop("invalidEmail", None)
                    else:
                        invalidEmail = False

                    if "sameEmail" in session:
                        sameEmail = True
                        session.pop("sameEmail", None)
                    else:
                        sameEmail = False

                    if "duplicateEmail" in session:
                        duplicateEmail = True
                        session.pop("duplicateEmail", None)
                    else:
                        duplicateEmail = False

                    if "duplicateUsername" in session:
                        duplicateUsername = True
                        session.pop("duplicateUsername", None)
                    else:
                        duplicateUsername = False

                    return render_template('users/admin/user_management.html', userList=paginatedUserList, count=userListLen, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, form=admin_reset_password_form, invalidEmail=invalidEmail, sameEmail=sameEmail, duplicateEmail=duplicateEmail, searched=False, duplicateUsername=duplicateUsername, parameter="")
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/user_management/search/<int:pageNum>/", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def userSearchManagement(pageNum):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        userFound, accActive = admin_validate_session_open_file(adminSession)
        if userFound and accActive:
            userDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                    print("Users found")
                else:
                    db["Users"] = userDict
                    print("No user data in user shelve files.")
            except:
                print("Error in retrieving Users from user.db")

            parameter = str(sanitise(request.args.get("user")))
            # if user types in something such as a js script with bad intention or empty value form submission by tempering with the html required attribute via inspect element, it will return "False"
            if parameter == "False":
                # redirect the admin instead so that they know that the inputs are not accepted due to security reasons
                return redirect(url_for("userSearchManagementError"))

            parametersURL = "?user=" + parameter
            # for resetting the user's password and updating the user's email for account recovery
            admin_reset_password_form = Forms.AdminResetPasswordForm(request.form)
            if request.method == "POST" and admin_reset_password_form.validate():
                password = generate_password()
                email = sanitise(admin_reset_password_form.email.data)
                validEmail = validate_email(email)

                # for redirecting the admin to the user management page that he/she was in
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0

                redirectURL = "/user_management/search/" + str(pageNum) +"/" + parametersURL

                if validEmail:
                    userID = int(request.form["userID"])
                    userKey = userDict.get(userID)
                    oldEmail = userKey.get_email()
                    duplicateEmail = check_duplicates(email, userDict, "email")
                    if oldEmail != email:
                        if duplicateEmail == False:
                            if userKey != None:
                                # changing the password of the user
                                userKey.set_password(password)
                                userKey.set_email(email)
                                userKey.set_email_verification("Not Verified")
                                db["Users"] = userDict
                                db.close()
                                try:
                                    send_admin_reset_email(email, password) # sending an email to the user to notify them of the change
                                except:
                                    print("Email server is down or its port is blocked")
                                print("User account recovered successfully and email sent.")
                                return redirect(redirectURL)
                            else:
                                db.close()
                                print("Error in retrieving user object.")
                                return redirect(redirectURL)
                        else:
                            db.close()
                            print("Inputted new user's email is not unique.")
                            session["duplicateEmail"] = True
                            return redirect(redirectURL)
                    else:
                        db.close()
                        print("User's new email inputted is the same as the old email.")
                        session["sameEmail"] = True
                        return redirect(redirectURL)
                else:
                    db.close()
                    print("Inputted new user's email is invalid.")
                    session["invalidEmail"] = True
                    return redirect(redirectURL)
            else:
                query = request.args.get("user")
                print(query)
                userList = []
                if query in userDict: # if admin searches for the user using the user id
                    print("Query is a user's ID.")
                    userList.append(userDict.get(query))
                elif validate_email(query):
                    print("Query is an email.")
                    for key in userDict:
                        userKey = userDict[key]
                        if userKey.get_email() == query:
                            userList.append(userKey)
                            break
                else: # if the admin searches for the user using the user's username
                    print("Query is a username")
                    usernameList = []
                    for users in userDict:
                        user = userDict.get(users)
                        usernameList.append(user.get_username())

                    try:
                        matchedUsernameList = difflib.get_close_matches(query, usernameList, len(usernameList), 0.85) # return a list of closest matched username with a length of the whole list as difflib will only return the 3 closest matches by default. I then set the cutoff to 0.85, i.e. must match to a certain percentage else it will be ignored.
                    except:
                        matchedUsernameList = []

                    print("Matched user (in a list):", matchedUsernameList)
                    for userKey in userDict:
                        userObject = userDict.get(userKey)
                        username = userObject.get_username()
                        for key in matchedUsernameList:
                            if username == key:
                                userList.append(userObject)

                maxItemsPerPage = 10 # declare the number of items that can be seen per pages
                userListLen = len(userList) # get the length of the userList
                maxPages = math.ceil(userListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number

                # redirecting for handling different situation where if the user manually keys in the url
                if pageNum < 0:
                    redirectRoute = "/user_management/search/0/" + parametersURL
                    return redirect(redirectRoute)
                elif userListLen > 0 and pageNum == 0:
                    redirectRoute = "/user_management/search/1" + "/" + parametersURL
                    return redirect(redirectRoute)
                elif pageNum > maxPages:
                    redirectRoute = "/user_management/search/" + str(maxPages) +"/" + parametersURL
                    return redirect(redirectRoute)
                else:
                   # pagination algorithm starts here
                    userList = userList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                    pageNumForPagination = pageNum - 1 # minus for the paginate function
                    paginatedUserList = paginate(userList, pageNumForPagination, maxItemsPerPage)
                    paginationList = get_pagination_button_list(pageNum, maxPages)

                    session["pageNum"] = pageNum # for uxd so that the admin can be on the same page after managing the user such as deleting the user account, etc.

                    previousPage = pageNum - 1
                    nextPage = pageNum + 1

                    # auto fixing user profile image if the user has uploaded but the image is no longer on the web server directory
                    for value in paginatedUserList:
                        userProfileFileName = value.get_profile_image()
                        if (bool(userProfileFileName) == True) and (Path(construct_path(PROFILE_UPLOAD_PATH, userProfileFileName)).is_file() == False):
                            value.set_profile_image("")

                    db["Users"] = userDict
                    db.close()

                    if "invalidEmail" in session:
                        invalidEmail = True
                        session.pop("invalidEmail", None)
                    else:
                        invalidEmail = False

                    if "sameEmail" in session:
                        sameEmail = True
                        session.pop("sameEmail", None)
                    else:
                        sameEmail = False

                    if "duplicateEmail" in session:
                        duplicateEmail = True
                        session.pop("duplicateEmail", None)
                    else:
                        duplicateEmail = False

                    if "duplicateUsername" in session:
                        duplicateUsername = True
                        session.pop("duplicateUsername", None)
                    else:
                        duplicateUsername = False

                    session["searchedPageRoute"] = "/user_management/search/" + str(pageNum) + "/" + parametersURL

                    return render_template('users/admin/user_management.html', userList=paginatedUserList, count=userListLen, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, form=admin_reset_password_form, invalidEmail=invalidEmail, sameEmail=sameEmail, duplicateEmail=duplicateEmail, searched=True, submittedParameters=parametersURL, duplicateUsername=duplicateUsername, parameter=parameter)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

# if the user tempers with the html search input and removed the require attribute or if the user tries to XSS the site.
@app.route("/user_management/search/not_allowed")
@limiter.limit("30/second") # to prevent ddos attacks
def userSearchManagementError():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        userFound, accActive = admin_validate_session_open_file(adminSession)
        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)
            return render_template('users/admin/user_management.html', notAllowed=True, searched=True, redirectURL=redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/delete_user/uid/<userID>", methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def deleteUser(userID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

            userDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the admin to the user management page
                    return redirect(url_for("userManagement"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("userManagement"))

            userKey = userDict.get(userID)

            if userKey != None:
                userImageFileName = userKey.get_profile_image()
                userDict.pop(userID)
                db['Users'] = userDict
                db.close()
                delete_user_profile(userImageFileName)
                print(f"User account with the ID, {userID}, has been deleted.")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/ban/uid/<userID>", methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def banUser(userID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

            userDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the admin to the user management page
                    return redirect(url_for("userManagement"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("userManagement"))

            userKey = userDict.get(userID)

            if userKey != None:
                userKey.set_status("Banned")
                db['Users'] = userDict
                db.close()
                print(f"User account with the ID, {userID}, has been banned.")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/unban/uid/<userID>", methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def unbanUser(userID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

            userDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the admin to the user management page
                    return redirect(url_for("userManagement"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("userManagement"))

            userKey = userDict.get(userID)

            if userKey != None:
                userKey.set_status("Good")
                db['Users'] = userDict
                db.close()
                print(f"User account with the ID, {userID}, has been unbanned.")
                try:
                    send_admin_unban_email(userKey.get_email()) # sending an email to the user to notify that his/her account has been unbanned
                except:
                    print("Email server is down or its port is blocked")
                print("Successfully sent an email.")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/change_username/uid/<userID>", methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def changeUserUsername(userID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

            userDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the admin to the user management page
                    return redirect(url_for("userManagement"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("userManagement"))

            userKey = userDict.get(userID)

            if userKey != None:
                username = sanitise(request.form["username"])
                duplicate_username = check_duplicates(username, userDict, "username")
                if duplicate_username == False:
                    userKey.set_username(username)
                    db['Users'] = userDict
                    db.close()
                    print("Username successfully changed.")
                    return redirect(redirectURL)
                else:
                    db.close()
                    print("Duplicate username.")
                    session["duplicateUsername"] = True
                    return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/reset_profile_image/uid/<userID>", methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def resetProfileImage(userID):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:
            # for redirecting the admin to the user management page that he/she was in
            if "searchedPageRoute" in session:
                redirectURL = session["searchedPageRoute"]
            else:
                if "pageNum" in session:
                    pageNum = session["pageNum"]
                else:
                    pageNum = 0
                redirectURL = "/user_management/page/" + str(pageNum)

            userDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                else:
                    db.close()
                    print("No user data in user shelve files.")
                    # since the file data is empty either due to the admin deleting the shelve files or something else, it will redirect the admin to the user management page
                    return redirect(url_for("userManagement"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("userManagement"))

            userKey = userDict.get(userID)

            if userKey != None:
                userKey.set_profile_image("")
                userImageFileName = userKey.get_profile_image()
                db['Users'] = userDict
                db.close()
                delete_user_profile(userImageFileName)
                print(f"User account with the ID, {userID}, has its profile picture reset.")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""End of User Management for Admins by Jason"""

"""Admin Data Visualisation (Total user per day) by Jason"""

@app.route("/admin_dashboard")
@limiter.limit("30/second") # to prevent ddos attacks
def dashboard():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)
        # if there's a need to retrieve admin account details, use the function below instead of the one above
        # userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)

        if userFound and accActive:
            saveNoOfUserPerDay() # refreshes the graph data every time an admin visits the dashboard page
            graphList = []
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'userGraphData' in db and "Users" in db:
                    graphList = db['userGraphData']
                else:
                    print("No data in user shelve files")
                    db["userGraphData"] = graphList
            except:
                print("Error in retrieving userGraphData from user.db")
            finally:
                db.close()

            print("Retrieved graph data:", graphList)
            try:
                lastUpdated = graphList[-1].get_lastUpdate() # retrieve latest object
            except:
                lastUpdated = str(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))

            selectedGraphDataList = graphList[-15:] # get last 15 elements from the list to show the total number of user per day for the last 15 days
            print("Selected graph data:", selectedGraphDataList)

            # for matplotlib and chartjs graphs
            xAxisData = [] # dates
            yAxisData = [] # number of users
            for objects in selectedGraphDataList:
                xAxisData.append(str(objects.get_date()))
                yAxisData.append(objects.get_noOfUser())

            # for csv
            graphDict = {}
            for objects in graphList:
                graphDict[objects.get_date()] = objects.get_noOfUser()

            # try and except as matplotlib may fail since it is outside of main thread
            try:
                fig = plt.figure(figsize=(20, 10)) # configure ratio of the graph image saved # configure ratio of the graph image saved
                plt.style.use("fivethirtyeight") # use fivethirtyeight style for the graph

                x = xAxisData # date labels for x-axis
                y = yAxisData # data for y-axis

                plt.plot(x, y, color="#009DF8", linewidth=3)

                # graph configurations
                plt.ylabel('Total Numbers of Users')
                plt.title("Total Userbase by Day")
                plt.ylim(bottom=0) # set graph to start from 0 (y-axis)
                fig.autofmt_xdate() # auto formats the date label to be tilted
                fig.tight_layout() # eliminates padding

                figureFilename = "static/data/user_base/graphs/user_base_" + str(datetime.now().strftime("%d-%m-%Y")) + ".png"
                plt.savefig(figureFilename)
            except:
                print("Error in saving graph image...")

            csvFileName = "static/data/user_base/csv/user_base.csv"

            # # below code for simulation purposes
            # xAxisData = [str(date.today()), str(date.today() + timedelta(days=1)), str(date.today() + timedelta(days=2))] # dates
            # yAxisData = [12, 240, 500] # number of users
            # graphDict = {
            #     "21/1/2022": 4,
            #     "22/1/2022": 20,
            #     "23/1/2022": 25,
            #     "24/1/2022": 100
            # }

            # for generating the csv data to collate all data as the visualisation on the web app only can show the last 15 days
            with open(csvFileName, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Dates", "Number Of Users"])
                for key, value in graphDict.items():
                    writer.writerow([key, value])

            print("X-axis data:", xAxisData)
            print("Y-axis data:", yAxisData)

            return render_template('users/admin/admin_dashboard.html', lastUpdated=lastUpdated, xAxisData=xAxisData, yAxisData=yAxisData, figureFilename=figureFilename, csvFileName=csvFileName)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""End of Admin Data Visualisation (Total user per day) by Jason"""

"""User Profile Settings by Jason"""

@app.route('/user_profile', methods=["GET","POST"])
@limiter.limit("150/second") # to prevent ddos attacks
def userProfile():
    if "userSession" in session and "adminSession" not in session:
        session.pop("teacher", None) # deleting data from the session if the user chooses to skip adding a payment method from the teacher signup process

        userSession = session["userSession"]

        # Retrieving data from shelve and to set the teacher's payment method info data
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("No user data in user shelve files.")
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            emailVerified = userKey.get_email_verification()
            if emailVerified == "Not Verified":
                emailVerification = False
            else:
                emailVerification = True
            if request.method == "POST":
                typeOfFormSubmitted = request.form.get("submittedForm")
                if typeOfFormSubmitted == "bio":
                    teacherBioInput = sanitise(request.form.get("teacherBio"))
                    if teacherBioInput == False:
                        teacherBioInput = ""
                    userKey.set_bio(teacherBioInput)
                    db['Users'] = userDict
                    db.close()
                    print("Teacher bio saved.")
                    return redirect(url_for("userProfile"))
                elif typeOfFormSubmitted == "image":
                    if "profileImage" not in request.files:
                        print("No file sent.")
                        return redirect(url_for("userProfile"))

                    file = request.files["profileImage"]

                    totalChunks = int(request.form["dztotalchunkcount"])
                    currentChunk = int(request.form['dzchunkindex'])
                    
                    extensionType = get_extension(file.filename)
                    if extensionType != False:
                        file.filename = userSession + extensionType # renaming the file name of the submitted image data payload
                        filename = file.filename
                    else:
                        filename = "invalid"

                    if file and allowed_image_file(filename):
                        # will only accept .png, .jpg, .jpeg
                        print("File extension accepted and is within size limit.")

                        userImageFileName = file.filename
                        newFilePath = construct_path(PROFILE_UPLOAD_PATH, userImageFileName)

                        if Path(newFilePath).is_file() and currentChunk == 0:
                            os.remove(newFilePath)

                        print("Total file size:", int(request.form['dztotalfilesize']))

                        try:
                            with open(newFilePath, "ab") as imageData: # ab flag for opening a file for appending data in binary format
                                imageData.seek(int(request.form['dzchunkbyteoffset']))
                                print("dzchunkbyteoffset:", int(request.form['dzchunkbyteoffset']))
                                imageData.write(file.stream.read())
                                imageData.close()
                        except OSError:
                            print('Could not write to file')
                            return make_response("Error writing to file", 500)
                        except:
                            print("Unexpected error.")
                            return make_response("Unexpected error", 500)

                        if currentChunk + 1 == totalChunks:
                            # This was the last chunk, the file should be complete and the size we expect
                            if os.path.getsize(newFilePath) != int(request.form['dztotalfilesize']):
                                print(f"File {file.filename} was completed, but there is a size mismatch. Received {os.path.getsize(newFilePath)} but had expected {request.form['dztotalfilesize']}")
                                return make_response("Image was not successfully uploaded! Please try again!", 500)
                            else:
                                print(f'File {file.filename} has been uploaded successfully')
                                # constructing a file path to see if the user has already uploaded an image and if the file exists
                                userOldImageFilePath = construct_path(PROFILE_UPLOAD_PATH, userKey.get_profile_image())

                                # using Path from pathlib to check if the file path of userID.png (e.g. 0.png) already exist.
                                # since dropzone will actually send multiple requests, 
                                if Path(userOldImageFilePath).is_file() and userOldImageFilePath != newFilePath:
                                    print("User has already uploaded a profile image before.")
                                    os.remove(userOldImageFilePath)
                                    print("Old Image file has been deleted.")

                                # resizing the image to a 1:1 ratio and compresses it
                                imageResized = resize_image(newFilePath, (250, 250))
                                
                                if imageResized:
                                    # if file was successfully resized, it means the image is a valid image
                                    userKey.set_profile_image(userImageFileName)
                                    db['Users'] = userDict
                                    db.close()

                                    return make_response(("Profile Image Uploaded!", 200))
                                else:
                                    # else this means that the image is not an image since Pillow is unable to open the image due to it being an unsupported image file or due to corrupted image in which the code below will reset the user's profile image
                                    userKey.set_profile_image("")
                                    db['Users'] = userDict
                                    db.close()
                                    os.remove(newFilePath) # removes corrupted image file
                                    return make_response(("Error in uploading image file!", 500))
                        else:
                            db.close()
                            print(f"Chunk {currentChunk + 1} of {totalChunks} for file {file.filename} complete")
                            return make_response((f"Chunk {currentChunk} out of {totalChunks} Uploaded", 200))
                    else:
                        db.close()
                        return make_response("Image extension not supported!", 500)
                elif typeOfFormSubmitted == "resetUserIcon":
                    print("Deleting user's profile image...")
                    userImageFileName = userKey.get_profile_image()
                    profileFilePath = construct_path(PROFILE_UPLOAD_PATH, userImageFileName)
                    # check if the user has already uploaded an image and checks if the image file path exists on the web server before deleting it
                    if bool(userImageFileName) != False and Path(profileFilePath).is_file():
                        os.remove(profileFilePath)
                    userKey.set_profile_image("")
                    db['Users'] = userDict
                    db.close()
                    print("User profile image deleted.")
                    return redirect(url_for("userProfile"))
                else:
                    db.close()
                    print("Form value tampered or POST request sent without form value...")
                    return redirect(url_for("userProfile"))
            else:
                db.close()
                userUsername = userKey.get_username()
                userEmail = userKey.get_email()

                if accType == "Teacher":
                    teacherBio = userKey.get_bio()
                else:
                    teacherBio = ""

                
                # checking if the user have uploaded a profile image before and if the image file exists
                userProfileFilenameSaved = bool(userKey.get_profile_image())
                imagesrcPath, profileReset = get_user_profile_pic(userSession)
                if profileReset:
                    userProfileFilenameSaved = False

                # checking sessions if any of the user's acc info has changed
                if "username_changed" in session:
                    usernameChanged = True
                    session.pop("username_changed", None)
                    print("Username recently changed?:", usernameChanged)
                else:
                    usernameChanged = False
                    print("Username recently changed?:", usernameChanged)

                if "email_updated" in session:
                    emailChanged = True
                    session.pop("email_updated", None)
                    print("Email recently changed?:", emailChanged)
                else:
                    emailChanged = False
                    print("Email recently changed?:", emailChanged)

                if "password_changed" in session:
                    passwordChanged = True
                    session.pop("password_changed", None)
                    print("Password recently changed?:", passwordChanged)
                else:
                    passwordChanged = False
                    print("Password recently changed?:", passwordChanged)

                if "recentChangeAccType" in session:
                    recentChangeAccType = True
                    session.pop("recentChangeAccType", None)
                    print("Recently changed account type to teacher?:", recentChangeAccType)
                else:
                    recentChangeAccType = False
                    print("Recently changed account type to teacher?:", recentChangeAccType)

                # email verification notifications checking
                # for notifying if the token has been sent to their email
                if "emailVerifySent" in session:
                    emailSent = True
                    session.pop("emailVerifySent", None)
                else:
                    emailSent = False

                # for notifying if they have already verified their email (traversal attack)
                if "emailFailed" in session:
                    emailAlreadyVerified = True
                    session.pop("emailFailed", None)
                else:
                    emailAlreadyVerified = False

                # for notifying if they have verified their email from the link in their email
                if "emailVerified" in session:
                    emailVerified = True
                    session.pop("emailVerified", None)
                else:
                    emailVerified = False

                # for notifying if the email verification link has expired/is invalid
                if "emailTokenInvalid" in session:
                    emailTokenInvalid = True
                    session.pop("emailTokenInvalid", None)
                else:
                    emailTokenInvalid = False

                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""

                return render_template('users/loggedin/user_profile.html', username=userUsername, email=userEmail, accType = accType, teacherBio=teacherBio, emailChanged=emailChanged, usernameChanged=usernameChanged, passwordChanged=passwordChanged, imagesrcPath=imagesrcPath, recentChangeAccType=recentChangeAccType, emailVerification=emailVerification, emailSent=emailSent, emailAlreadyVerified=emailAlreadyVerified, emailVerified=emailVerified, emailTokenInvalid=emailTokenInvalid, teacherUID=teacherUID, userProfileFilenameSaved=userProfileFilenameSaved)
        else:
            db.close()
            print("User not found or is banned.")
            # if user is not found for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route("/change_username", methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def updateUsername():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]
        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear()
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object from the shelve based on the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            imagesrcPath = retrieve_user_profile_pic(userKey)
            create_update_username_form = Forms.CreateChangeUsername(request.form)
            if request.method == "POST" and create_update_username_form.validate():
                updatedUsername = sanitise(create_update_username_form.updateUsername.data)
                currentUsername = userKey.get_username()

                if updatedUsername != currentUsername:
                    # checking duplicates for username
                    username_duplicates = False
                    for key in userDict:
                        print("retrieving")
                        usernameShelveData = userDict[key].get_username()
                        if updatedUsername == usernameShelveData:
                            print("Verdict: Username already taken.")
                            username_duplicates = True
                            break

                    if username_duplicates == False:
                        print("Verdict: Username is unique.")
                        # updating username of the user
                        userKey.set_username(updatedUsername)
                        db['Users'] = userDict
                        print("Username updated")

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of password
                        session["username_changed"] = True

                        db.close()
                        return redirect(url_for("userProfile"))
                    else:
                        db.close()

                        return render_template('users/loggedin/change_username.html', form=create_update_username_form, username_duplicates=True, accType=accType, imagesrcPath=imagesrcPath, teacherUID = teacherUID)
                else:
                    db.close()
                    print("Update username input same as user's current username")
                    return render_template('users/loggedin/change_username.html', form=create_update_username_form, sameUsername=True, accType=accType, imagesrcPath=imagesrcPath, teacherUID = teacherUID)
            else:
                db.close()
                return render_template('users/loggedin/change_username.html', form=create_update_username_form, accType=accType, imagesrcPath=imagesrcPath, teacherUID = teacherUID)
        else:
            db.close()
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route("/change_email", methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def updateEmail():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]
        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear()
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)
        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            imagesrcPath = retrieve_user_profile_pic(userKey)
            create_update_email_form = Forms.CreateChangeEmail(request.form)
            if request.method == "POST" and create_update_email_form.validate():

                updatedEmail = sanitise(create_update_email_form.updateEmail.data.lower())
                currentEmail = userKey.get_email()
                if updatedEmail != currentEmail:
                    # Checking duplicates for email
                    email_duplicates = False
                    for key in userDict:
                        print("retrieving")
                        emailShelveData = userDict[key].get_email()
                        if updatedEmail == emailShelveData:
                            print("Verdict: User email already exists.")
                            email_duplicates = True
                            break
                            
                    if email_duplicates == False:
                        print("Verdict: Email is unique.")
                        # updating email of the user
                        userKey.set_email(updatedEmail)
                        userKey.set_email_verification("Not Verified")
                        try:
                            send_verify_changed_email(updatedEmail, currentEmail, userSession)
                        except:
                            print("Email server is down or its port is blocked")
                        db['Users'] = userDict
                        db.close()
                        print("Email updated")

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of email
                        session["email_updated"] = True

                        try:
                            send_email_change_notification(currentEmail, updatedEmail) # sending an email to alert the user of the change of email so that the user will know about it and if his/her account was compromised, he/she will be able to react promptly by contacting CourseFinity support team
                        except:
                            print("Email server down or email server port is blocked.")
                        return redirect(url_for("userProfile"))
                    else:
                        db.close()
                        return render_template('users/loggedin/change_email.html', form=create_update_email_form, email_duplicates=True, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
                else:
                    db.close()
                    print("User updated email input is the same as their current email")
                    return render_template('users/loggedin/change_email.html', form=create_update_email_form, sameEmail=True, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
            else:
                db.close()
                return render_template('users/loggedin/change_email.html', form=create_update_email_form, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            db.close()
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route("/change_password", methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def updatePassword():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]
        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear()
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)
        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            imagesrcPath = retrieve_user_profile_pic(userKey)
            create_update_password_form = Forms.CreateChangePasswordForm(request.form)
            if request.method == "POST" and create_update_password_form.validate():
                # declaring passwordNotMatched, passwordVerification, and errorMessage variable to initialise and prevent unboundLocalError
                passwordNotMatched = True
                passwordVerification = False

                # for jinja2
                errorMessage = False

                currentPassword = create_update_password_form.currentPassword.data
                updatedPassword = create_update_password_form.updatePassword.data
                confirmPassword = create_update_password_form.confirmPassword.data

                # validation starts
                print("Updated password input:", updatedPassword)
                print("Confirm password input", confirmPassword)
                if updatedPassword == confirmPassword:
                    passwordNotMatched = False
                    print("New and confirm password inputs matched")
                else:
                    print("New and confirm password inputs did not match")

                passwordVerification = userKey.verify_password(currentPassword)
                oldPassword = userKey.verify_password(updatedPassword)

                # printing message for debugging purposes
                if passwordVerification:
                    print("User identity verified")
                else:
                    print("Current password input hash did not match with the one in the shelve database")

                # if there any validation error, errorMessage will become True for jinja2 to render the error message
                if passwordVerification == False or passwordNotMatched:
                    db.close()
                    errorMessage = True
                    return render_template('users/loggedin/change_password.html', form=create_update_password_form, errorMessage=errorMessage, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
                else:
                    if oldPassword:
                        db.close()
                        print("User cannot change password to their current password!")
                        return render_template('users/loggedin/change_password.html', form=create_update_password_form, samePassword=True, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
                    else:
                        # updating password of the user once validated
                        userKey.set_password(updatedPassword)
                        userEmail = userKey.get_email()
                        db['Users'] = userDict
                        print("Password updated")
                        db.close()

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of password
                        session["password_changed"] = True

                        try:
                            send_password_change_notification(userEmail) # sending an email to alert the user of the change of password so that the user will know about it and if his/her account was compromised, he/she will be able to react promptly by contacting CourseFinity support team or if the email was not changed, he/she can reset his/her password in the reset password page
                        except:
                            print("Email server is down or its port is blocked")

                        return redirect(url_for("userProfile"))
            else:
                db.close()
                return render_template('users/loggedin/change_password.html', form=create_update_password_form, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            db.close()
            print("User not found is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route('/change_account_type', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def changeAccountType():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        accType = userKey.get_acc_type()
        print("Account type:", accType)

        if userFound and accGoodStatus:
            if accType == "Student":
                if request.method == "POST" and request.form["changeAccountType"] == "changeToTeacher":
                    # changing the user's account type to teacher by deleting the student object and creating a new teacher object, and hence, changing the user ID as a whole.
                    username = userKey.get_username()
                    password = userKey.get_password()
                    email = userKey.get_email()
                    userID = userSession

                    # retrieving the user's payment info if the user has saved one
                    cardExists = bool(userKey.get_card_name())
                    if cardExists:
                        cardName = userKey.get_card_name()
                        cardNumber = userKey.get_card_no()
                        cardExpiry = userKey.get_card_expiry()
                        cardType = userKey.get_card_type()

                    # retrieving the user's profile image filename if the user has uploaded one
                    profileImageExists = bool(userKey.get_profile_image())
                    print("Does user have profile image:", profileImageExists)
                    if profileImageExists:
                        profileImageFilename = userKey.get_profile_image()
                        imagePath = construct_path(PROFILE_UPLOAD_PATH, profileImageFilename)
                        if Path(imagePath).is_file():
                            profileImagePathExists = True
                            print("Profile image exists:", profileImagePathExists)
                        else:
                            profileImagePathExists = False

                    userDict.pop(userID)
                    user = Teacher.Teacher(userID, username, email, password)
                    user.set_teacher_join_date(date.today())
                    userDict[userID] = user

                    # setting the user's payment method if the user has saved their payment method before
                    if cardExists:
                        user.set_card_name(cardName)
                        user.set_card_no(cardNumber)
                        user.set_card_expiry(cardExpiry)
                        user.set_card_type(cardType)

                    # saving the user's profile image if the user has uploaded their profile image
                    if profileImageExists and profileImagePathExists:
                        user.set_profile_image(profileImageFilename)

                    # add in other saved attributes of the student object

                    # checking if the user has already became a teacher
                    # Not needed but for scability as if there's a feature that allows teachers to revert back to a student in the future, the free three months 0% commission system can be abused.
                    if bool(user.get_teacher_join_date) == False:
                        user.set_teacher_join_date(date.today())
                        print("User has not been a teacher, setting today's date as joined date.")

                    db["Users"] = userDict
                    db.close()
                    print("Account type updated to teacher.")
                    session["recentChangeAccType"] = True # making a session so that jinja2 can render a notification of the account type change
                    return redirect(url_for("userProfile"))
                else:
                    print("Not POST request or did not have relevant hidden field.")
                    db.close()
                    return redirect(url_for("userProfile"))
            else:
                db.close()
                print("User is not a student.")
                # if the user is not a student but visits this webpage, it will redirect the user to the user profile page
                return redirect(url_for("userProfile"))
        else:
            db.close()
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("teacherSignUp"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("teacherSignUp"))

"""End of User Profile Settings by Jason"""

"""User payment method settings by Jason"""

@app.route('/payment_method', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def userPayment():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            imagesrcPath = retrieve_user_profile_pic(userKey)
            cardExist = bool(userKey.get_card_name())
            print("Card exist?:", cardExist)

            if cardExist == False:
                create_add_payment_form = Forms.CreateAddPaymentForm(request.form)
                if request.method == "POST" and create_add_payment_form.validate():
                    print("POST request sent and form entries validated")
                    cardName = sanitise(create_add_payment_form.cardName.data)

                    cardNo = sanitise(create_add_payment_form.cardNo.data)
                    cardValid = validate_card_number(cardNo)

                    cardType = get_credit_card_type(cardNo, cardValid) # get type of the credit card for specific warning so that the user would know that only Mastercard and Visa cards are only accepted

                    cardExpiry = sanitise(create_add_payment_form.cardExpiry.data)
                    cardExpiryValid = validate_expiry_date(cardExpiry)

                    if cardValid and cardExpiryValid:
                        if cardType != False:
                            # setting the user's payment method
                            userKey.set_card_name(cardName)
                            userKey.set_card_no(cardNo)
                            cardExpiry = cardExpiryStringFormatter(cardExpiry)
                            userKey.set_card_expiry(cardExpiry)
                            userKey.set_card_type(cardType)
                            db['Users'] = userDict
                            print("Payment added")

                            # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of adding the payment method
                            session["payment_added"] = True

                            db.close()
                            return redirect(url_for("userPayment"))
                        else:
                            return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form, invalidCardType=True, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
                    else:
                        return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form, cardValid=cardValid, cardExpiryValid=cardExpiryValid, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
                else:
                    print("POST request sent but form not validated")
                    db.close()

                    # checking sessions if any of the user's payment method has been deleted
                    if "card_deleted" in session:
                        cardDeleted = True
                        session.pop("card_deleted", None)
                        print("Card recently added?:", cardDeleted)
                    else:
                        cardDeleted = False
                        print("Card recently added?:", cardDeleted)

                    return render_template('users/loggedin/user_add_payment.html', form=create_add_payment_form, cardDeleted=cardDeleted, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
            else:
                db.close()
                cardName = userKey.get_card_name()
                cardNo = str(userKey.get_card_no())
                print("Original card number:", cardNo)
                cardNo = cardNo[-5:-1] # string slicing to get the last 4 digits of the credit card number
                print("Sliced card number:", cardNo)
                cardExpiry = userKey.get_card_expiry()
                print("Card expiry date:", cardExpiry)
                cardType = userKey.get_card_type()

                # checking sessions if any of the user's payment method details has changed
                if "card_updated" in session:
                    cardUpdated = True
                    session.pop("card_updated", None)
                    print("Card recently updated?:", cardUpdated)
                else:
                    cardUpdated = False
                    print("Card recently updated?:", cardUpdated)

                if "payment_added" in session:
                    cardAdded = True
                    session.pop("payment_added", None)
                    print("Card recently added?:", cardAdded)
                else:
                    cardAdded = False
                    print("Card recently added?:", cardAdded)

                return render_template('users/loggedin/user_existing_payment.html', cardName=cardName, cardNo=cardNo, cardExpiry=cardExpiry, cardType=cardType, cardUpdated=cardUpdated, cardAdded=cardAdded, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            db.close()
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route('/edit_payment', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def userEditPayment():
    if "userSession" in session and "adminSession" not in session:
        # checking if the user has a credit card in the shelve database to prevent directory traversal which may break the web app

        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear()
                # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            imagesrcPath = retrieve_user_profile_pic(userKey)
            cardExist = bool(userKey.get_card_name())
            print("Card exist?:", cardExist)
            cardName = userKey.get_card_name()

            cardNo = str(userKey.get_card_no())
            print("Original card number:", cardNo)
            cardNo = cardNo[-5:-1] # string slicing to get the last 4 digits of the credit card number
            print("Sliced card number:", cardNo)

            cardType = userKey.get_card_type().capitalize()
            if cardExist:
                create_edit_payment_form = Forms.CreateEditPaymentForm(request.form)
                if request.method == "POST" and create_edit_payment_form.validate():
                    cardExpiry = sanitise(create_edit_payment_form.cardExpiry.data)
                    cardExpiryValid = validate_expiry_date(cardExpiry)
                    if cardExpiryValid:
                        # changing the user's payment info
                        cardExpiry = cardExpiryStringFormatter(cardExpiry)
                        userKey.set_card_expiry(cardExpiry)
                        db['Users'] = userDict
                        print("Payment edited")
                        db.close()

                        # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of the card details
                        session["card_updated"] = True

                        return redirect(url_for("userPayment"))
                    else:
                        db.close()
                        return render_template('users/loggedin/user_edit_payment.html', form=create_edit_payment_form, cardName=cardName, cardNo=cardNo, cardType=cardType, accType=accType, cardExpiryValid=cardExpiryValid, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
                else:
                    db.close()
                    return render_template('users/loggedin/user_edit_payment.html', form=create_edit_payment_form, cardName=cardName, cardNo=cardNo, cardType=cardType, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
            else:
                db.close()
                return redirect(url_for("userProfile"))
        else:
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route('/delete_card', methods=['POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def deleteCard():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            # checking if the user has a credit card in the shelve database to prevent directory traversal if the logged in attackers send a POST request to the web app server
            cardExist = bool(userKey.get_card_name())
            print("Card exist?:", cardExist)

            if cardExist:
                # deleting user's payment info, specifically changing their payment info to empty strings
                userKey.set_card_name("")
                userKey.set_card_no("")
                userKey.set_card_expiry("")
                userKey.set_card_type("")

                db['Users'] = userDict
                print("Payment added")
                db.close()

                # sending a session data so that when it redirects the user to the user profile page, jinja2 will render out an alert of the change of the card details
                session["card_deleted"] = True
                return redirect(url_for("userPayment"))

            else:
                db.close()
                return redirect(url_for("userProfile"))
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

"""End of User payment method settings by Jason"""

"""Teacher Cashout System by Jason"""

@app.route("/teacher_cashout", methods=['GET', 'POST'])
@limiter.limit("30/second") # to prevent ddos attacks
def teacherCashOut():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            if "cashedOut" in session:
                cashedOut = True
                session.pop("cashedOut", None)
            else:
                cashedOut = False

            if "failedToCashOut" in session:
                failedToCashOut = True
                session.pop("failedToCashOut", None)
            else:
                failedToCashOut = False

            if "noPayment" in session:
                noPayment = True
                session.pop("noPayment", None)
            else:
                noPayment = False

            imagesrcPath = retrieve_user_profile_pic(userKey)
            joinedDate = userKey.get_teacher_join_date()
            zeroCommissionEndDate = joinedDate + timedelta(days=90)
            currentDate = date.today()

            # if it's the first day of the month
            resetMonth = check_first_day_of_month(currentDate)
            initialEarnings = round(userKey.get_earnings(), 2)
            accumulatedEarnings = userKey.get_accumulated_earnings()
            if resetMonth:
                accumulatedEarnings += initialEarnings
                userKey.set_accumulated_earnings(accumulatedEarnings)
                userKey.set_earnings(0)

            lastDayOfMonth = check_last_day_of_month(currentDate)

            if request.method == "POST":
                typeOfCollection = request.form.get("typeOfCollection")
                if ((accumulatedEarnings + initialEarnings) > 0):
                    # simple resetting of teacher's income
                    doesCardExist = bool(userKey.get_card_name())
                    if doesCardExist != False:
                        # calculating how much the teacher has earned
                        if currentDate <= zeroCommissionEndDate:
                            commission = "0%"
                            totalEarned = round((initialEarnings + accumulatedEarnings), 2)
                        else:
                            commission = "25%"
                            totalEarned = round(((initialEarnings + accumulatedEarnings) - ((initialEarnings + accumulatedEarnings) * 0.25)), 2)

                        # deducting from the teacher object
                        if typeOfCollection == "collectingAll" and lastDayOfMonth:
                            session["cashedOut"] = True
                            userKey.set_earnings(0)
                            userKey.set_accumulated_earnings(0)
                            db["Users"] = userDict
                            db.close()
                            return redirect(url_for("teacherCashOut"))
                        elif typeOfCollection == "collectingAccumulated":
                            session["cashedOut"] = True
                            userKey.set_accumulated_earnings(0)
                            db["Users"] = userDict
                            db.close()
                            return redirect(url_for("teacherCashOut"))
                        else:
                            db.close()
                            print("POST request sent but it is not the last day of the month or post request sent but had tampered values in hidden input.")
                            session["failedToCashOut"] = True
                            return redirect(url_for("teacherCashOut"))
                    else:
                        db.close()
                        session["noPayment"] = True
                        print("POST request sent but user does not have a valid payment method to cash out to.")
                        return redirect(url_for("teacherCashOut"))
                else:
                    db.close()
                    print("POST request sent but user have already collected their revenue or user did not earn any this month.")
                    session["failedToCashOut"] = True
                    return redirect(url_for("teacherCashOut"))
            else:
                db.close()
                monthTuple = ("January ", "February ", "March ", "April ", "May ", "June ", "July ", "August ", "September ", "October ", "November ", "December ")
                month = monthTuple[(int(date.today().month) - 1)] # retrieves the month in a word format from the tuple instead of 1 for January.
                monthYear = month + str(date.today().year)
                remainingDays = int(str(zeroCommissionEndDate - currentDate)[0:2]) # to get the remaining days left to alert the user to make full use of it, since without string slicing, it will return a value such as "86 days, 0:00:00".

                if accumulatedEarnings > 0:
                    accumulatedCollect = True
                else:
                    accumulatedCollect = False

                if currentDate <= zeroCommissionEndDate:
                    commission = "0%"
                    totalEarned = round((initialEarnings + accumulatedEarnings), 2)

                    # converting the number of remaining days till the free 0% commission is over in a readable format as compared to "you have until 60 days till it is over" for an example.
                    if remainingDays > 60 and remainingDays <= 90:
                        remainingDays = "3 months"
                    elif remainingDays > 30 and remainingDays <= 60:
                        remainingDays = "2 months"
                    elif remainingDays == 30:
                        remainingDays = "1 month"
                    elif remainingDays > 7 and remainingDays < 30:
                        remainingDays = "less than a month"
                    elif remainingDays <= 7:
                        remainingDays = "less than a week"
                    elif remainingDays < 0:
                        remainingDays = 0
                        print("User's free 0% three months commission is over.")
                    else:
                        remainingDays = "Unexpected error, please contact CourseFinity support."
                else:
                    commission = "25%"
                    totalEarned = round(((initialEarnings + accumulatedEarnings) - ((initialEarnings + accumulatedEarnings) * 0.25)), 2)

                totalEarnedInt = totalEarned
                # converting the numbers into strings of 2 decimal place for the earnings
                initialEarnings = get_two_decimal_pt(initialEarnings)
                totalEarned = get_two_decimal_pt(totalEarned)
                accumulatedEarnings = get_two_decimal_pt(accumulatedEarnings)

                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""

                return render_template('users/teacher/teacher_cashout.html', accType=accType, imagesrcPath=imagesrcPath, monthYear=monthYear, lastDayOfMonth=lastDayOfMonth, commission=commission, totalEarned=totalEarned, initialEarnings=initialEarnings, accumulatedEarnings=accumulatedEarnings, remainingDays=remainingDays, totalEarnedInt=totalEarnedInt, failedToCashOut=failedToCashOut, cashedOut=cashedOut, accumulatedCollect=accumulatedCollect, noPayment=noPayment, teacherUID=teacherUID)
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

"""End of Teacher Cashout System by Jason"""

"""Search Function by Royston"""

@app.route('/search/<int:pageNum>/', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
@limiter.limit("30/second") # to prevent ddos attacks
def search(pageNum):
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            # add in your CRUD or other code
            imagesrcPath = retrieve_user_profile_pic(userKey)
            # add in your code here (if any)
            checker = ""
            courseDict = {}
            courseTitleList = []
            try:
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
                courseDict = db["Courses"]

            except:
                print("Error in obtaining course.db data")
                return redirect(url_for("home"))

            searchInput = str(request.args.get("q"))

            searchURL = "?searchq=" + searchInput

            searchfound = []
            for courseID in courseDict:
                courseTitle = courseDict.get(courseID).get_title()
                courseTitleList.append(courseTitle)

            try:
                matchedCourseTitleList = difflib.get_close_matches(searchInput, courseTitleList, len(courseTitleList), 0.1) # return a list of closest matched search with a length of the whole list as difflib will only return the 3 closest matches by default. I then set the cutoff to 0.80, i.e. must match to a certain percentage else it will be ignored.
            except:
                matchedCourseTitleList = []

            print("What searches are matched? " , matchedCourseTitleList)
            for courseID in courseDict:
                courseObject = courseDict.get(courseID)
                titleCourse = courseObject.get_title()
                print(titleCourse)
                for key in matchedCourseTitleList:
                    print("what is inside the key?", key)
                    if titleCourse == key:
                        course = courseDict[courseID]

                        searchInformation = {"Title":course.get_title(),
                            "Description":course.get_description(),
                            "Thumbnail":course.get_thumbnail(),
                            "Owner":course.get_userID()}

                        searchfound.append(searchInformation)

            print(searchfound)
            if bool(searchfound): #If there is something inside the list
                checker = True
            else:
                checker = False

            db.close()

            maxItemsPerPage = 5 # declare the number of items that can be seen per pages
            courseListLen = len(searchfound) # get the length of the userList
            maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
            pageNum = int(pageNum)
            # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
            if pageNum < 0:
                return redirect("/search/0/" + searchURL)
            elif courseListLen > 0 and pageNum == 0:
                return redirect("/search/1" + "/" + searchURL)
            elif pageNum > maxPages:
                redirectRoute = "/search/" + str(maxPages) + "/" + searchURL
                return redirect(redirectRoute)
            else:
                # pagination algorithm starts here
                courseList = searchfound[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                pageNumForPagination = pageNum - 1 # minus for the paginate function
                paginatedCourseList = paginate(courseList, pageNumForPagination, maxItemsPerPage)
                searchInformation = paginate(searchfound[::-1], pageNumForPagination, maxItemsPerPage)

                paginationList = get_pagination_button_list(pageNum, maxPages)

                previousPage = pageNum - 1
                nextPage = pageNum + 1

                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""

                db.close()
                return render_template('users/general/search.html', accType=accType , courseDict=courseDict, matchedCourseTitleList=matchedCourseTitleList,searchInput=searchInput, pageNum=pageNum, previousPage = previousPage, nextPage = nextPage, paginationList = paginationList, maxPages=maxPages, imagesrcPath=imagesrcPath, checker=checker, searchfound=paginatedCourseList, teacherUID=teacherUID,submittedParameters=searchURL)
        else:
            print("Admin/User account is not found or is not active/banned.")
            checker = ""
            courseDict = {}
            courseTitleList = []
            try:
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
                courseDict = db["Courses"]

            except:
                print("Error in obtaining course.db data")
                return redirect(url_for("home"))

            searchInput = str(request.args.get("q"))

            searchURL = "?searchq=" + searchInput

            searchfound = []
            for courseID in courseDict:
                courseTitle = courseDict.get(courseID).get_title()
                courseTitleList.append(courseTitle)

            try:
                matchedCourseTitleList = difflib.get_close_matches(searchInput, courseTitleList, len(courseTitleList), 0.1) # return a list of closest matched search with a length of the whole list as difflib will only return the 3 closest matches by default. I then set the cutoff to 0.80, i.e. must match to a certain percentage else it will be ignored.
            except:
                matchedCourseTitleList = []

            print("What searches are matched? " , matchedCourseTitleList)
            for courseID in courseDict:
                courseObject = courseDict.get(courseID)
                titleCourse = courseObject.get_title()
                print(titleCourse)
                for key in matchedCourseTitleList:
                    print("what is inside the key?", key)
                    if titleCourse == key:
                        course = courseDict[courseID]

                        searchInformation = {"Title":course.get_title(),
                            "Description":course.get_description(),
                            "Thumbnail":course.get_thumbnail(),
                            "Owner":course.get_userID()}

                        searchfound.append(searchInformation)

            print(searchfound)
            if bool(searchfound): #If there is something inside the list
                checker = True
            else:
                checker = False

            db.close()

            maxItemsPerPage = 5 # declare the number of items that can be seen per pages
            courseListLen = len(searchfound) # get the length of the userList
            maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
            pageNum = int(pageNum)
            # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
            if pageNum < 0:
                return redirect("/search/0/" + searchURL)
            elif courseListLen > 0 and pageNum == 0:
                return redirect("/search/1" + "/" + searchURL)
            elif pageNum > maxPages:
                redirectRoute = "/search/" + str(maxPages) + "/" + searchURL
                return redirect(redirectRoute)
            else:
                # pagination algorithm starts here
                courseList = searchfound[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                pageNumForPagination = pageNum - 1 # minus for the paginate function
                paginatedCourseList = paginate(courseList, pageNumForPagination, maxItemsPerPage)
                searchInformation = paginate(searchfound[::-1], pageNumForPagination, maxItemsPerPage)

                paginationList = get_pagination_button_list(pageNum, maxPages)

                previousPage = pageNum - 1
                nextPage = pageNum + 1

                db.close()
                return render_template('users/general/search.html', courseDict=courseDict, matchedCourseTitleList=matchedCourseTitleList,searchInput=searchInput, pageNum=pageNum, previousPage = previousPage, nextPage = nextPage, paginationList = paginationList, maxPages=maxPages, checker=checker, searchfound=paginatedCourseList,searchURL=searchURL,submittedParameters=searchURL, accType="Guest")
    else:
        checker = ""
        courseDict = {}
        courseTitleList = []
        try:
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
            courseDict = db["Courses"]

        except:
            print("Error in obtaining course.db data")
            return redirect(url_for("home"))

        searchInput = str(request.args.get("q"))

        searchURL = "?searchq=" + searchInput

        searchfound = []
        for courseID in courseDict:
            courseTitle = courseDict.get(courseID).get_title()
            courseTitleList.append(courseTitle)

        try:
            matchedCourseTitleList = difflib.get_close_matches(searchInput, courseTitleList, len(courseTitleList), 0.1) # return a list of closest matched search with a length of the whole list as difflib will only return the 3 closest matches by default. I then set the cutoff to 0.80, i.e. must match to a certain percentage else it will be ignored.
        except:
            matchedCourseTitleList = []

        print("What searches are matched? " , matchedCourseTitleList)
        for courseID in courseDict:
            courseObject = courseDict.get(courseID)
            titleCourse = courseObject.get_title()
            print(titleCourse)
            for key in matchedCourseTitleList:
                print("what is inside the key?", key)
                if titleCourse == key:
                    course = courseDict[courseID]

                    searchInformation = {"Title":course.get_title(),
                        "Description":course.get_description(),
                        "Thumbnail":course.get_thumbnail(),
                        "Owner":course.get_userID()}

                    searchfound.append(searchInformation)

        print(searchfound)
        if bool(searchfound): #If there is something inside the list
            checker = True
        else:
            checker = False
        
        session["getSearchInput"] = "/search/" + str(pageNum) + "/" + searchURL

        db.close()

        maxItemsPerPage = 5 # declare the number of items that can be seen per pages
        courseListLen = len(searchfound) # get the length of the userList
        maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
        pageNum = int(pageNum)
        # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
        if pageNum < 0:
            return redirect("/search/0/" + searchURL)
        elif courseListLen > 0 and pageNum == 0:
            return redirect("/search/1" + "/" + searchURL)
        elif pageNum > maxPages:
            redirectRoute = "/search/" + str(maxPages) + "/" + searchURL
            return redirect(redirectRoute)
        else:
            # pagination algorithm starts here
            courseList = searchfound[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
            pageNumForPagination = pageNum - 1 # minus for the paginate function
            paginatedCourseList = paginate(courseList, pageNumForPagination, maxItemsPerPage)
            searchInformation = paginate(searchfound[::-1], pageNumForPagination, maxItemsPerPage)

            paginationList = get_pagination_button_list(pageNum, maxPages)

            previousPage = pageNum - 1
            nextPage = pageNum + 1

            db.close()
            return render_template('users/general/search.html', courseDict=courseDict, matchedCourseTitleList=matchedCourseTitleList,searchInput=searchInput, pageNum=pageNum, previousPage = previousPage, nextPage = nextPage, paginationList = paginationList, maxPages=maxPages, checker=checker, searchfound=paginatedCourseList,searchURL=searchURL,submittedParameters=searchURL, accType="Guest")

"""End of Search Function by Royston"""

"""Purchase History by Royston"""

@app.route("/purchasehistory/<int:pageNum>")
@limiter.limit("30/second") # to prevent ddos attacks
def purchaseHistory(pageNum):
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            imagesrcPath = retrieve_user_profile_pic(userKey)
            # insert your C,R,U,D operation here to deal with the user shelve data files
            courseID = ""
            courseType = ""
            historyCheck = True
            historyList = []
            # Get purchased courses
            purchasedCourses = userKey.get_purchases()
            print("PurchaseID exists?: ", purchasedCourses)

            if purchasedCourses != {}:
                try:
                    courseDict = {}
                    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
                    courseDict = db["Courses"]
                except:
                    print("Unable to open up course shelve")
                    db.close()

                # Get specific course with course ID
                for courseID in list(purchasedCourses.keys()):
                    print(courseID)

                    # Find the correct course
                    course = courseDict[courseID]
                    courseType = purchasedCourses.get(courseID).get("Course Type")

                    courseInformation = {"CourseID":course,
                        "Title":course.get_title(),
                        "Description":course.get_description(),
                        "Thumbnail":course.get_thumbnail(),
                        "CourseTypeCheck":userKey.get_purchasesCourseType(courseID),
                        "Price":course.get_price(),
                        "Owner":course.get_userID()}
                    historyList.append(courseInformation)
                print(historyList)

                db.close()
            else:
                print("Purchase History is Empty")
                historyCheck = False

            maxItemsPerPage = 5 # declare the number of items that can be seen per pages
            courseListLen = len(purchasedCourses) # get the length of the userList
            maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
            pageNum = int(pageNum)
            # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
            if pageNum < 0:
                return redirect("/purchasehistory/0")
            elif courseListLen > 0 and pageNum == 0:
                return redirect("/purchasehistory/1")
            elif pageNum > maxPages:
                redirectRoute = "/purchasehistory/" + str(maxPages)
                return redirect(redirectRoute)
            else:
                # pagination algorithm starts here
                courseList = historyList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                pageNumForPagination = pageNum - 1 # minus for the paginate function
                paginatedCourseList = paginate(courseList, pageNumForPagination, maxItemsPerPage)
                purchasedCourses = paginate(historyList[::-1], pageNumForPagination, maxItemsPerPage)

                paginationList = get_pagination_button_list(pageNum, maxPages)

                previousPage = pageNum - 1
                nextPage = pageNum + 1

                db.close() # remember to close your shelve files!
                return render_template('users/loggedin/purchasehistory.html', courseID=courseID, courseType=courseType,historyList=paginatedCourseList, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, accType=accType, imagesrcPath=imagesrcPath,historyCheck=historyCheck, teacherUID=teacherUID)
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Purchase History by Royston"""

"""Purchase Review by Royston"""

# THIS APP ROUTE HAS POTENTIAL BUGS, PLEASE FIX
@app.route("/purchasereview/<courseID>", methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def createPurchaseReview(courseID):
    createReview = Forms.CreateReviewText(request.form)
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # userFound, accGoodStatus = validate_session_open_file(userSession)
        # if there's a need to retrieve the userKey for reading the user's account details, use the function below instead of the one above
        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)

        if userFound and accGoodStatus:
            # add in your own code here for your C,R,U,D operation and remember to close() it after manipulating the data
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            imagesrcPath = retrieve_user_profile_pic(userKey)

            purchasedCourses = userKey.get_purchases()
            user = userSession
            print("Purchased course exists?: ", purchasedCourses)
            courseDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            print(courseID)

            try:
                courseDict = db["Courses"]
            except:
                print("Error in retrieving review from review.db")
                db.close()
                return redirect(url_for("purchasehistory"))

            if courseID in purchasedCourses:
                if request.method == 'POST' and createReview.validate():
                    review = createReview.review.data
                    print("What is the review?: ",review)
                    reviewDict = {"Review": review, "UserID": user}
                    courseDict["Courses"] = db

                    session["reviewAdded"] = True

                    db.close() # remember to close your shelve files!
                    return render_template('users/loggedin/purchasereview.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID, reviewDict = reviewDict)
                else:
                    db.close()
                    return render_template('users/loggedin/purchasereview.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID, form=createReview)

            else:
                # else clause to be removed or indent the lines below and REMOVE the render template with NO variables that are being passed into jinja2
                print("User has not purchased the course.")
                db.close()
                return redirect(url_for("home"))
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Purchase Review by Royston"""

"""Purchase View by Royston"""

@app.route("/purchaseview")
@limiter.limit("30/second") # to prevent ddos attacks
def purchaseView(pageNum):
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            imagesrcPath = retrieve_user_profile_pic(userKey)
            # insert your C,R,U,D operation here to deal with the user shelve data files
            historyList = session.get("getHistoryList")
            videoList = []
            courseID = ""
            courseType = ""
            historyCheck = True
            # Get purchased courses
            purchasedCourses = userKey.get_purchases()
            print("PurchaseID exists?: ", purchasedCourses)

            if purchasedCourses != {}:
                try:
                    courseDict = {}
                    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
                    courseDict = db["Courses"]
                except:
                    print("Unable to open up course shelve")
                    db.close()

                # Get specific course with course ID
                for courseID in list(purchasedCourses.keys()):
                    print(courseID)

                    # Find the correct course
                    course = courseDict[courseID]
                    courseType = purchasedCourses.get(courseID).get("Course Type")

                    courseInformation = {"Title":course.get_title(),
                        "Description":course.get_description(),
                        "Thumbnail":course.get_thumbnail(),
                        "CourseTypeCheck":userKey.get_purchasesCourseType(courseID),
                        "Price":course.get_price(),
                        "Owner":course.get_userID()}
                    videoList.append(courseInformation)
                print(videoList)
                db.close()
            else:
                print("Purchase view is Empty")
                historyCheck = False

            maxItemsPerPage = 5 # declare the number of items that can be seen per pages
            courseListLen = len(purchasedCourses) # get the length of the userList
            maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
            pageNum = int(pageNum)
            # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
            if pageNum < 0:
                return redirect("/purchaseview/0")
            elif courseListLen > 0 and pageNum == 0:
                return redirect("/purchaseview/1")
            elif pageNum > maxPages:
                redirectRoute = "/purchaseview/" + str(maxPages)
                return redirect(redirectRoute)
            else:
                # pagination algorithm starts here
                courseList = historyList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                pageNumForPagination = pageNum - 1 # minus for the paginate function
                paginatedCourseList = paginate(courseList, pageNumForPagination, maxItemsPerPage)
                purchasedCourses = paginate(historyList[::-1], pageNumForPagination, maxItemsPerPage)

                paginationList = get_pagination_button_list(pageNum, maxPages)

                previousPage = pageNum - 1
                nextPage = pageNum + 1

                db.close() # remember to close your shelve files!
                return render_template('users/loggedin/purchaseview.html', courseID=courseID, courseType=courseType,historyList=paginatedCourseList, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, accType=accType, imagesrcPath=imagesrcPath,historyCheck=historyCheck, teacherUID=teacherUID)
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Purchase View by Royston"""


"""Template Redirect Shopping Cart by Jason because Opera is bad"""

@app.route("/shopping_cart", methods = ["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def shoppingCartDefault():
    return redirect("/shopping_cart/1")

"""End of Redirect Shopping Cart by Jason because Opera is bad"""


"""Template Shopping Cart by Wei Ren"""

@app.route("/shopping_cart/<int:pageNum>", methods = ["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def shoppingCart(pageNum):
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        # userKey is the object (e.g. Student() or Teacher())
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            imagesrcPath = retrieve_user_profile_pic(userKey)

            # insert your C,R,U,D operation here to deal with the user shelve data files
            removeCourseForm = Forms.RemoveShoppingCartCourse(request.form)
            checkoutCompleteForm = Forms.CheckoutComplete(request.form)
            shoppingCart = userKey.get_shoppingCart()
            print("Shopping Cart:", userKey.get_shoppingCart())

            # Remember to validate
            try:
                if "Courses" in db:
                    courseDict = db['Courses']
                else:
                    print("user.db has no course entries.")
                    courseDict = {}
            except:
                print("Error in retrieving Course from user.db")

            if request.method == "POST":
                if bool(checkoutCompleteForm.checkoutComplete.data) and checkoutCompleteForm.validate():
                    print(checkoutCompleteForm.checkoutComplete.data)

                    # Remove courses from cart into purchases

                    timing = checkoutCompleteForm.checkoutTiming.data.upper()               # U for Update
                    date = timing.split("T")[0]
                    time = timing.split("T")[1]

                    for courseID in list(shoppingCart.keys()):
                        courseType = shoppingCart[courseID]

                        cost = 0

                        orderID = checkoutCompleteForm.checkoutOrderID.data
                        payerID = checkoutCompleteForm.checkoutPayerID.data

                        userKey.addCartToPurchases(courseID, courseType, date, time,cost, orderID, payerID)

                    print("Shopping Cart:", userKey.get_shoppingCart())
                    print("Purchases:", userKey.get_purchases())

                    userDict[userKey.get_user_id()] = userKey
                    db['Users'] = userDict

                    session["paymentComplete"] = True

                    return redirect(url_for('home'))

                elif removeCourseForm.validate():
                    courseID =  removeCourseForm.courseID.data

                    print("Removing course with Course ID:", courseID)      # D for Delete

                    for course in list(shoppingCart.keys()):
                        print(course)
                        if course == courseID:
                            userKey.remove_from_cart(courseID)
                            print(userKey.get_shoppingCart)
                            userDict[userKey.get_user_id] = userKey
                            db["Users"] = userDict
                            db.close()
                            break

                    return redirect("/shopping_cart/"+str(pageNum))

                else:
                    print("Error with form.")
                    return redirect(url_for('home'))

            # Render the page
            else:                                                                               # R for Read
                print(userKey.get_purchases())
                # Initialise lists for jinja2 tags
                courseList = []
                subtotal = 0

                try:
                    courseIDs = list(shoppingCart.keys())
                except:
                    courseIDs = []
                    print("Shopping Cart is Empty.")

                print(shoppingCart)
                for courseID in courseIDs:
                    # Getting course info
                    print("Course Info [ID, Type]:", [courseID, shoppingCart[courseID]])

                    course = courseDict[courseID]

                    # Getting course type chosen
                    courseType = shoppingCart[courseID]

                    # Getting subtototal
                    subtotal += float(course.get_price())

                    # Getting course owner username
                    courseOwnerUsername = userDict[course.get_userID()].get_username()

                    # Getting course owner profile pic
                    courseOwnerProfile = None

                    # Add additional info to list
                    courseList.append({"courseID" : courseID,
                                       "courseType" : courseType,
                                       "courseTitle" : course.get_shortTitle(),
                                       "courseDescription" : course.get_shortDescription(),
                                       "coursePricePaying" : course.get_price(),
                                       "courseZoomCondition" : course.get_course_type(),
                                       "courseVideoCondition":course.get_course_type(),
                                       "courseOwnerUsername" : courseOwnerUsername,
                                       "courseOwnerProfile" : courseOwnerProfile,
                                       "courseOwnerLink" : None,
                                       "courseThumbnail" : None})


                maxItemsPerPage = 5 # declare the number of items that can be seen per pages
                courseListLen = len(courseList) # get the length of the userList
                maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
                # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
                if pageNum < 0:
                    return redirect("/shopping_cart/0")
                elif courseListLen > 0 and pageNum == 0:
                    return redirect("/shopping_cart/1")
                elif pageNum > maxPages:
                    redirectRoute = "/shopping_cart/" + str(maxPages)
                    return redirect(redirectRoute)
                else:
                    # pagination algorithm starts here
                    courseList = courseList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                    pageNumForPagination = pageNum - 1 # minus for the paginate function
                    paginatedCourseList = paginate(courseList, pageNumForPagination, maxItemsPerPage)

                    previousPage = pageNum - 1
                    nextPage = pageNum + 1

                    paginationList = get_pagination_button_list(pageNum, maxPages)

                    if accType == "Teacher":
                        teacherUID = userSession
                    else:
                        teacherUID = ""

                    db.close() # remember to close your shelve files!
                    return render_template('users/student/shopping_cart.html', nextPage = nextPage, previousPage = previousPage, courseList=paginatedCourseList, count=courseListLen, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, form = removeCourseForm, checkoutForm = checkoutCompleteForm, subtotal = "{:,.2f}".format(subtotal), accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)

        else:
            db["Users"] = userDict  # Save changes
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # user is redirected to the home page, as they are not/no longer logged in
            return redirect(url_for("home"))

"""End of Template Shopping Cart by Wei Ren"""

"""Contact Us by Wei Ren"""

@app.route("/contact_us", methods = ["GET", "POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def contactUs():
    contactForm = Forms.ContactUs(request.form)

    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            # add in your CRUD or other code
            if accType != "Admin": # Registered user in database, not banned

                success = False

                if request.method == "POST" and contactForm.validate(): # Teacher or student submitting form

                    dbAdmin = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "c")
                    # Remember to validate
                    try:
                        if "Tickets" in dbAdmin:
                            ticketDict = dbAdmin['Tickets']
                        else:
                            print("admin.db has no contact entries.")
                            ticketDict = {}
                    except:
                        print("Error in retrieving Tickets from admin.db")

                    name = contactForm.name.data
                    email = contactForm.email.data
                    subject = contactForm.subject.data

                    ticketID = generate_6_char_id(list(ticketDict.keys()))

                    ticket = {"User ID" : userKey.get_user_id(),
                              "Account Type" : accType,
                              "Name" : name,
                              "Email" : email,
                              "Subject" : subject,
                              "Enquiry" : contactForm.enquiry.data,
                              "Status" : "Open"}

                    print(ticket)

                    ticketDict[ticketID] = ticket
                    dbAdmin['Tickets'] = ticketDict

                    success = True

                    try:
                        send_contact_us_email(ticketID, subject, name, email)
                    except:
                        print("Email server is down, please try again later.")

                    dbAdmin.close()

                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""

                return render_template('users/general/contact_us.html', accType=accType, imagesrcPath=imagesrcPath, form = contactForm, success=success, teacherUID=teacherUID)
            else:
                # Admin user
                return redirect("/support_ticket_management/0")
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear() # As Guest Account
            return redirect(url_for("contactUs"))
    else:
        # Guests
        print("Admin/User account is not found or is not active/banned.")
        session.clear()

        success = False

        if request.method == "POST" and contactForm.validate():

            dbAdmin = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "c")
            # Remember to validate
            try:
                if "Tickets" in dbAdmin:
                    ticketDict = dbAdmin['Tickets']
                else:
                    print("admin.db has no contact entries.")
                    ticketDict = {}
            except:
                print("Error in retrieving Tickets from admin.db")

            name = contactForm.name.data
            email = contactForm.email.data
            subject = contactForm.subject.data

            ticketID = generate_6_char_id(ticketDict)

            ticket = {"Ticket ID" : ticketID,
                      "User ID" : None,
                      "Account Type" : "Guest",
                      "Name" : name,
                      "Email" : email,
                      "Subject" : subject,
                      "Enquiry" : contactForm.enquiry.data,
                      "Status" : "Open"}

            ticketDict[ticketID] = ticket
            dbAdmin['Tickets'] = ticketDict

            success = True

            try:
                send_contact_us_email(ticketID, subject, name, email)
            except:
                print("Email server is down, please try again later")

            dbAdmin.close()

        return render_template("users/general/contact_us.html", accType="Guest", form = contactForm, success=success)

"""End of Contact Us by Wei Ren"""

"""Support Ticket Management by Wei Ren"""

@app.route("/support_ticket_management/<int:pageNum>", methods = ["GET", "POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def supportTicketManagement(pageNum):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)
        # if there's a need to retrieve admin account details, use the function below instead of the one above
        # userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)

        if userFound and accActive:

            ticketSearch = Forms.TicketSearchForm(request.form)
            ticketAction = Forms.TicketAction(request.form)

            dbAdmin = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "c")
            # Remember to validate
            try:
                if "Tickets" in dbAdmin:
                    ticketDict = dbAdmin['Tickets']
                else:
                    print("admin.db has no contact entries.")
                    ticketDict = {}
            except:
                print("Error in retrieving Tickets from admin.db")

            # add in your code here

            ticketList = []
            search = False

            # Initialise filtration system
            if "Checked Filters" not in session:
                session['Checked Filters'] = ["Open", "Closed", "Guest", "Student", "Teacher", "General", "Account", "Business", "Bugs", "Jobs", "News", "Others"]
                session['Query'] = ""
            # GET is a client request for data from the web server,
            # while POST and PUT are used to send messages that upload data to the web server

            # Only if there are entries
            if request.method == "POST" and ticketDict != {}:

                # Change Filter Parameters; only if form submitted
                print(ticketSearch.data)
                print(ticketAction.data)
                if not(ticketSearch.checkedFilters.data == None and ticketSearch.query.data == None):
                    print(ticketSearch.checkedFilters.data)
                    session["Checked Filters"] = json.loads(ticketSearch.checkedFilters.data)
                    print(ticketSearch.query.data)
                    if ticketSearch.query.data == None:
                        session["Query"] = ""
                    else:
                        session["Query"] = ticketSearch.query.data.lower()
                    search = True

                # Ticket Toggling
                if ticketAction.ticketAction.data == "Toggle":
                    print("Toggling")
                    print(ticketAction.ticketID.data)
                    ticket = ticketDict[ticketAction.ticketID.data]
                    if ticket["Status"] == "Open":
                        ticket["Status"] = "Closed"
                    else:
                        ticket["Status"] = "Open"
                    ticketDict[ticketAction.ticketID.data] = ticket
                    print(ticketDict)

                # Ticket Deleting
                elif ticketAction.ticketAction.data == "Delete":
                    print("Deleting")
                    if ticketAction.ticketID.data in ticketDict:
                        ticketID = ticketAction.ticketID.data
                        ticket = ticketDict(ticketID)
                        issueTitle = ticket["Subject"]
                        name = ticket["Name"]
                        email = ticket["Email"]
                        try:
                            send_ticket_closed_email(ticketID, issueTitle, name, email)
                        except:
                            print("Email server is down, please try again later.")
                        ticketDict.pop(ticketID)


            print(ticketDict)

            # Preparing filtration system
            query = session["Query"]
            filters = ["Open", "Closed", "Guest", "Student", "Teacher", "General", "Account", "Business", "Bugs", "Jobs", "News", "Others"]
            for filter in session["Checked Filters"]:
                if filter in filters:
                    filters.remove(filter)

            # Checking tickets
            for ticketID in list(ticketDict.keys()):
                ticket = ticketDict[ticketID]

                # Checking filters
                filtered = False
                for filter in filters:
                    if filtered == True:
                        continue
                    if filter == "Open" or filter == "Closed":
                        if ticket["Status"] == filter:
                            filtered = True
                    elif filter == "Guest" or filter == "Student" or filter == "Teacher":
                        if ticket["Account Type"] == filter:
                            filtered = True
                    else:
                        if ticket["Subject"] == filter:
                            filtered = True


                if not filtered and (query in ticket['Name'].lower() or query in ticket['Email'].lower() or query in ticketID.lower()):
                    ticketList.append(ticket)

            renderedFilters = session['Checked Filters']

            dbAdmin['Tickets'] = ticketDict
            dbAdmin.close() # remember to close your shelve files!

            maxItemsPerPage = 10 # declare the number of items that can be seen per pages
            ticketListLen = len(ticketList) # get the length of the userList
            maxPages = math.ceil(ticketListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
            # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
            if pageNum < 0:
                return redirect("/support_ticket_management/0")
            elif ticketListLen > 0 and pageNum == 0:
                return redirect("/support_ticket_management/1")
            elif pageNum > maxPages:
                redirectRoute = "/support_ticket_management/" + str(maxPages)
                return redirect(redirectRoute)
            else:
                # pagination algorithm starts here
                ticketList = ticketList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                pageNumForPagination = pageNum - 1 # minus for the paginate function
                paginatedTicketList = paginate(ticketList, pageNumForPagination, maxItemsPerPage)

                previousPage = pageNum - 1
                nextPage = pageNum + 1

                paginationList = get_pagination_button_list(pageNum, maxPages)
                return render_template('users/admin/support_ticket_management.html', nextPage = nextPage, previousPage = previousPage, ticketList=paginatedTicketList, count=ticketListLen, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, ticketSearch = ticketSearch, ticketAction=ticketAction, renderedFilters=json.dumps(renderedFilters), query=query, search=search)

        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("contactUs"))
    else:
        return redirect(url_for("contactUs"))

"""End of Support Ticket Management by Wei Ren"""

"""Admin Statistics by Wei Ren"""
@app.route("/admin_statistics/<string:statistic>/<int:year>/<int:month>/<int:day>")
@limiter.limit("30/second") # to prevent ddos attacks

def adminStatistics(statistic, year, month, day):
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)

        if userFound and accActive:

            # Remember to validate
            try:
                if "Statistics" in dbAdmin:
                    statisticDict = dbAdmin['Statistics']
                else:
                    print("admin.db has no statistic entries.")
                    statisticDict = create_statistic_dict('Courses Created','Courses Purchased','User Sign Ups','Teacher Sign Ups','Tickets Created','Tickets Open','Users Banned','Users Deleted')
            except:
                print("Error in retrieving statistics from admin.db")

            # add in your code here
            


            # print(statisticDict)

            dbAdmin.close() # remember to close the admin shelve file!
            return render_template('users/admin/admin_statistics.html')
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""

            graphList = []
            db = shelve.open("user", "c")
            try:
                if 'userGraphData' in db and "Users" in db:
                    graphList = db['userGraphData']
                else:
                    print("No data in user shelve files")
                    db["userGraphData"] = graphList
            except:
                print("Error in retrieving userGraphData from user.db")
            finally:
                db.close()

            print("Retrieved graph data:", graphList)
            try:
                lastUpdated = graphList[-1].get_lastUpdate() # retrieve latest object
            except:
                lastUpdated = str(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))

            selectedGraphDataList = graphList[-15:] # get last 15 elements from the list to show the total number of user per day for the last 15 days
            print("Selected graph data:", selectedGraphDataList)

            # for matplotlib and chartjs graphs
            xAxisData = [] # dates
            yAxisData = [] # number of users
            for objects in selectedGraphDataList:
                xAxisData.append(str(objects.get_date()))
                yAxisData.append(objects.get_noOfUser())

            # for csv
            graphDict = {}
            for objects in graphList:
                graphDict[objects.get_date()] = objects.get_noOfUser()

            # try and except as matplotlib may fail since it is outside of main thread
            try:
                fig = plt.figure(figsize=(20, 10)) # configure ratio of the graph image saved # configure ratio of the graph image saved
                plt.style.use("fivethirtyeight") # use fivethirtyeight style for the graph

                x = xAxisData # date labels for x-axis
                y = yAxisData # data for y-axis

                plt.plot(x, y, color="#009DF8", linewidth=3)

                # graph configurations
                plt.ylabel('Total Numbers of Users')
                plt.title("Total Userbase by Day")
                plt.ylim(bottom=0) # set graph to start from 0 (y-axis)
                fig.autofmt_xdate() # auto formats the date label to be tilted
                fig.tight_layout() # eliminates padding

                figureFilename = "static/data/user_base/graphs/user_base_" + str(datetime.now().strftime("%d-%m-%Y")) + ".png"
                plt.savefig(figureFilename)
            except:
                print("Error in saving graph image...")

            csvFileName = "static/data/user_base/csv/user_base.csv"

            # # below code for simulation purposes
            # xAxisData = [str(date.today()), str(date.today() + timedelta(days=1)), str(date.today() + timedelta(days=2))] # dates
            # yAxisData = [12, 240, 500] # number of users
            # graphDict = {
            #     "21/1/2022": 4,
            #     "22/1/2022": 20,
            #     "23/1/2022": 25,
            #     "24/1/2022": 100
            # }

            # for generating the csv data to collate all data as the visualisation on the web app only can show the last 15 days
            with open(csvFileName, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Dates", "Number Of Users"])
                for key, value in graphDict.items():
                    writer.writerow([key, value])

            print("X-axis data:", xAxisData)
            print("Y-axis data:", yAxisData)"""
"""
x-axis:
 - Time (Over 24 hours)
 - Time (Days)
 - Time (Weeks)
 - Time (Months)
 - Time (Quarterly)
 - Time (Year)

y-axis:
 - Courses Created
 - Courses Purchased
 - User Sign Ups
 - Teacher Sign Ups
 - Tickets Opened
 - Tickets Active (and then closed)
 - Users Banned (and then unbanned)
 - Users Deleted

Previous Next



"""


"""End of Admin Statistics by Wei Ren"""


"""Teacher's Channel Page(General view) by Clarence"""

@app.route('/teacher_page/<teacherPageUID>', methods=["GET", "POST"])
@limiter.limit("30/second")  # to prevent ddos attacks
def teacherPage(teacherPageUID):
    if "adminSession" in session or "userSession" in session:
    #checks if session is admin or user
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStanding, accType = validate_session_get_userKey_open_file(userSession)

        if userFound and accGoodStanding:
            print("Hello jason")
        #checks if user account is available
            userDict = {}
            courseDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                    courseDict = db['Courses']
                    db.close()
                else:
                    db.close()
                    print("User data in shelve is empty.")
                    session.clear()  # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("home"))

            teacherObject = userDict.get(teacherPageUID)
            teacherCourseList = []
            print("teacher course list is defined")
            for value in courseDict.values():
                if value.get_userID() == teacherPageUID:
                    teacherCourseList.append(value)
            try:
                # Get last 3 elements from the list
                lastThreeCourseList = teacherCourseList[-3:]
            except:
                lastThreeCourseList = teacherCourseList[::-1]
                print("Teacher has not enough courses")

            # Popular courses are highest rated courses
            popularCourseList = []
            if len(teacherCourseList) >= 3:
                for i in range(3):
                    popularCourseList.append(
                        max(teacherCourseList, key=lambda x: x.get_rating()))

            lastThreeCourseLen = len(teacherCourseList)
            popularCourseLen = len(popularCourseList)

            imagesrcPath = retrieve_user_profile_pic(userKey)
            bio = teacherObject.get_bio()
            return render_template('users/general/teacher_page.html', accType=accType, imagesrcPath=imagesrcPath, teacherPageUID=teacherPageUID, bio=bio, teacherCourseList=teacherCourseList, lastThreeCourseList=lastThreeCourseList, lastThreeCourseLen=lastThreeCourseLen, popularCourseLen=popularCourseLen, popularCourseListLen=popularCourseList)

        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/teacher_page.html", accType="Guest")
    else:
        return render_template("users/general/teacher_page.html", accType="Guest")

"""End of Teacher's Channel Page by Clarence"""

"""Teacher's Courses Page by Clarence"""

@app.route('/teacher_courses/<teacherCoursesUID>', methods=["GET", "POST"])
@limiter.limit("30/second")  # to prevent ddos attacks
def teacherCourses(teacherCoursesUID):
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStanding, accType, imagesrcPath = validate_session_get_userKey_open_file(userSession)

        if userFound and accGoodStanding:
            imagesrcPath = retrieve_user_profile_pic(userKey)
            return render_template('users/general/teacher_courses.html', accType=accType, imagesrcPath=imagesrcPath, teacherCoursesUID=teacherCoursesUID)

        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/teacher_courses.html", accType="Guest")
    else:
        return render_template("users/general/teacher_courses.html", accType="Guest")

"""End of Teacher's Courses Page by Clarence"""

"""Course Creation by Clarence"""

@app.route("/create_course/<teacherUID>", methods=["GET", "POST"])
@limiter.limit("30/second")  # to prevent ddos attacks
def course_thumbnail_upload(teacherUID):
    createCourseForm = Forms.CreateCourse(request.form)
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        courseDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
                if "Courses" in db:
                    courseDict = db['Courses']
                else:
                    db["Courses"] = courseDict
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear()  # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            imagesrcPath = retrieve_user_profile_pic(userKey)
            if accType == "Teacher":
                teacherUID = userSession
                if request.method == "POST":
                    if createCourseForm.validate():
                        #add course object to courseDict then save to user shelve
                        db["Courses"] = courseDict
                        db.close()
                else:
                    teacherUID = ""
                db.close()  # remember to close your shelve files!
                return render_template('users/teacher/create_course.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID, form=createCourseForm)
            else:
                db.close()
                print("User not found or is banned")
                # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
                session.clear()
                return redirect(url_for("home"))
        else:
            if "adminSession" in session:
                return redirect(url_for("home"))
            else:
                # determine if it make sense to redirect the user to the home page or the login page
                # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
                return redirect(url_for("home"))
                # return redirect(url_for("userLogin"))

"""Course Creation by Clarence"""

"""User's Own Channel Page(Teacher) by Clarence"""

@app.route('/my_channel/<teacherUID>')
@limiter.limit("30/second")  # to prevent ddos attacks
def teacherOwnPage(teacherUID):
    if "adminSession" in session or "userSession" in session:
    #checks if session is admin or user
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStanding, accType = validate_session_get_userKey_open_file(userSession)

        if userFound and accGoodStanding:
        #checks if user account is available
            userDict = {}
            courseDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            print("hello 1")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                    courseDict = db['Courses']
                    db.close()
                else:
                    db.close()
                    print("User data in shelve is empty.")
                    session.clear()  # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                    return redirect(url_for("home"))
            except:
                print("Hello 2")
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("home"))

            print("Hello 3")
            teacherObject = userDict.get(teacherUID)
            teacherCourseList = []

            for value in courseDict.values():
                if value.get_userID() == teacherUID:
                    teacherCourseList.append(value)
            try:
                # Get last 3 elements from the list
                lastThreeCourseList = teacherCourseList[-3:]
            except:
                lastThreeCourseList = teacherCourseList[::-1]
                print("Teacher has not enough courses")

            # Popular courses are highest rated courses
            popularCourseList = []
            teacherCourseListCopy = []
            popularCourseLen = len(popularCourseList)


            if popularCourseLen >= 3:
                for i in range(3):
                    popularCourseList.append(max(teacherCourseListCopy, key=lambda x: x.get_rating()))
                    teacherCourseListCopy.pop(popularCourseList)
            else:
                for i in range(popularCourseLen):
                    popularCourseList.append(max(teacherCourseListCopy, key=lambda x: x.get_rating()))
                    teacherCourseListCopy.pop(popularCourseList)
            lastThreeCourseLen = len(teacherCourseList)
            print("iwd", popularCourseList)

            imagesrcPath = retrieve_user_profile_pic(userKey)
            bio = teacherObject.get_bio()

            return render_template('users/teacher/my_channel.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID, bio=bio, teacherCourseList=teacherCourseList, lastThreeCourseList=lastThreeCourseList, lastThreeCourseLen=lastThreeCourseLen, popularCourseLen=popularCourseLen, popularCourseList=popularCourseList)

        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/teacher/my_channel.html", accType="Guest")
    else:
        return render_template("users/teacher/my_channel.html", accType="Guest")

"""End of Teacher's Channel Page(Teacher view) by Clarence"""

"""General Pages"""

@app.route('/cookie_policy')
@limiter.limit("30/second") # to prevent ddos attacks
def cookiePolicy():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)

        if userFound and accGoodStanding:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            return render_template('users/general/cookie_policy.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/cookie_policy.html", accType="Guest")
    else:
        return render_template("users/general/cookie_policy.html", accType="Guest")

@app.route('/terms_and_conditions')
@limiter.limit("30/second") # to prevent ddos attacks
def termsAndConditions():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)

        if userFound and accGoodStanding:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            return render_template('users/general/terms_and_conditions.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/terms_and_conditions.html", accType="Guest")
    else:
        return render_template("users/general/terms_and_conditions.html", accType="Guest")

@app.route('/privacy_policy')
@limiter.limit("30/second") # to prevent ddos attacks
def privacyPolicy():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)

        if userFound and accGoodStanding:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            return render_template('users/general/privacy_policy.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/privacy_policy.html", accType="Guest")
    else:
        return render_template("users/general/privacy_policy.html", accType="Guest")

@app.route("/faq")
@limiter.limit("30/second") # to prevent ddos attacks
def faq():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)

        if userFound and accGoodStanding:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            return render_template('users/general/faq.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/faq.html", accType="Guest")
    else:
        return render_template("users/general/faq.html", accType="Guest")

"""End of Genral Pages"""

# 8 template app.route("") for you guys :prayge:
# Please REMEMBER to CHANGE the def function() function name to something relevant and unique (will have runtime error if the function name is not unique)
'''
# Template for your app.route("") if
  - User session validity check needed (Logged in?)
  - User banned?

  - Using user shelve files --> shelve.open("user", "C") ONLY
  - Webpage will not have admin view
  - Use case: User features such as change_password.html, etc.
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
@limiter.limit("30/second") # to prevent ddos attacks
def function():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            imagesrcPath = retrieve_user_profile_pic(userKey)
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            db.close() # remember to close your shelve files!
            return render_template('users/loggedin/page.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - User session validity check needed (Logged in?)
  - User banned?

  - Using CUSTOM shelve files --> shelve.open("<name of shelve here>", "C") ONLY
  - If your feature might need to retrieve the user's account details
  - Webpage will not have admin view
  - Use case: User features/pages that deals with other shelve files
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
@limiter.limit("30/second") # to prevent ddos attacks
def function():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)


        if userFound and accGoodStatus:
            # add in your own code here for your C,R,U,D operation and remember to close() it after manipulating the data
            imagesrcPath = retrieve_user_profile_pic(userKey)
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            return render_template('users/loggedin/page.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if [Note that this is similar to one above]
  - User session validity check needed (Logged in?)
  - User banned?

  - Only READING from shelve (user data)

  - Webpage will not have admin view
  - Use case: User pages (user_profile.html, etc)
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route('', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
@limiter.limit("30/second") # to prevent ddos attacks
def insertName():
    if "userSession" in session and "adminSession" not in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)


        if userFound and accGoodStatus:
            # add in your code below
            imagesrcPath = retrieve_user_profile_pic(userKey)
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            return render_template('users/loggedin/page.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - User session validity check needed (Logged in?)
  - User banned?
  - Is user admin?

  - NOT using shelve

  - Webpage will have admin and user view
  e.g. General pages (about_us.html, etc) that check whether user/admin is logged in.
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route('', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
@limiter.limit("30/second") # to prevent ddos attacks
def insertName():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userFound, accGoodStanding, accType, imagesrcPath = general_page_open_file(userSession)

        if userFound and accGoodStanding:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            return render_template('users/general/page.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/page.html", accType="Guest")
            # return redirect(url_for("insertName"))
    else:
        return render_template("users/general/page.html", accType="Guest")

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - User session validity check needed (Logged in?)
  - User banned?
  - Is user admin?

  - Using CUSTOM shelve or reading user info

  - Webpage will have admin and user view
  e.g. General pages (home page) that check whether user/admin is logged in.
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route('', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
@limiter.limit("30/second") # to prevent ddos attacks
def insertName():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            # add in your CRUD or other code
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""
            return render_template('users/general/page.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/page.html", accType="Guest")
            # return redirect(url_for("insertName"))
    else:
        return render_template("users/general/page.html", accType="Guest")

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - Admin session validity check needed (Logged in?)
  - Admin account active?

  - Using CUSTOM shelve files --> shelve.open("<name of shelve here>", "C") ONLY

  - Webpage will not have user view
  e.g. Admin pages
  - Use case: Admim pages
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
@limiter.limit("30/second") # to prevent ddos attacks
def function():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)
        userFound, accActive = admin_validate_session_open_file(adminSession)
        # if there's a need to retrieve admin account details, use the function below instead of the one above
        # userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)

        if userFound and accActive:
            # add in your code here
            xDict = {}
            db = shelve.open("", "c") # change the flag accordingly
            # implement your try and except here to handle the shelve files

            return render_template('users/admin/page.html')
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - Admin session validity check needed (Logged in?)
  - Admin account active?

  - Using admin shelve files --> shelve.open("admin", "C") ONLY

  - Webpage will not have user view
  e.g. Admin pages
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
@limiter.limit("30/second") # to prevent ddos attacks
def function():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)

        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "c")
        try:
            if 'Admins' in db:
                adminDict = db['Admins']
            else:
                db.close()
                print("Admin account data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the admin shelve files or something else, it will clear any session and redirect the user to the homepage
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Admins from admin.db")
            return redirect(url_for("home"))

        userKey, userFound, accActive = admin_get_key_and_validate(adminSession, adminDict)

        if userFound and accActive:
            # add in your code here

            db.close() # remember to close the admin shelve file!
            return render_template('users/admin/page.html')
        else:
            db.close()
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

'''
# Template for your app.route("") if
  - Admin session validity check needed (Logged in?)
  - Admin account active?

  - Only READING from shelve (admin data)

  - Webpage will not have user view
  - Use case: Admin pages
"""Template app.route(") (use this when adding a new app route) by INSERT_YOUR_NAME"""

@app.route("/")
@limiter.limit("30/second") # to prevent ddos attacks
def function():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)

        userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)

        if userFound and accActive:
            # add in your code here

            return render_template('users/admin/page.html')
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

"""End of Template app.route by INSERT_YOUR_NAME"""
'''

"""Custom Error Pages"""

# Bad Request
@app.errorhandler(400)
def error400(e):
    return render_template("errors/401.html"), 400

# Unauthorised
@app.errorhandler(401)
def error401(e):
    return render_template("errors/401.html"), 401

# Forbidden
@app.errorhandler(403)
def error403(e):
    return render_template("errors/403.html"), 403

# Not Found
@app.errorhandler(404)
def error404(e):
    return render_template("errors/404.html"), 404

# Method Not Allowed
@app.errorhandler(405)
def error405(e):
    return render_template("errors/405.html"), 405

# Payload Too Large
@app.errorhandler(413)
def error413(e):
    return render_template("errors/413.html"), 413

# Too Many Requests
@app.errorhandler(429)
def error429(e):
    return render_template("errors/429.html"), 429

# Internal Server Error
@app.errorhandler(500)
def error500(e):
    return render_template("errors/500.html"), 500

# Not Implemented
@app.errorhandler(501)
def error501(e):
    return render_template("errors/501.html"), 501

# Bad Gateway
@app.errorhandler(502)
def error502(e):
    return render_template("errors/502.html"), 502

# Service Temporarily Unavailable
@app.errorhandler(503)
def error503(e):
    return render_template("errors/503.html"), 503

"""End of Custom Error Pages"""

if __name__ == '__main__':
    # uncomment the below part when the web app is ready to be deployed for testing
    """ scheduler.configure(timezone="Asia/Singapore") # configure timezone to always follow Singapore's timezone
    # adding a scheduled job to save data for the graph everyday at 11.59 p.m. below
    scheduler.add_job(saveNoOfUserPerDay, trigger="cron", hour="23", minute="59", second="0", id="collectUserbaseData")
    scheduler.start()
    app.run(debug=True, use_reloader=False) """
    app.run(debug=True)

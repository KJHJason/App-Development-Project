from flask import Flask, render_template, request, redirect, url_for, session, make_response, flash, Markup, abort, send_from_directory
from werkzeug.utils import secure_filename
import shelve, math, paypalrestsdk, difflib, json, csv, phonenumbers, pyotp, qrcode
from os import environ
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
from requests import post as pyPost
from flask_mailman import Mail
from datetime import date, timedelta, datetime
from base64 import b64encode, b64decode
from apscheduler.schedulers.background import BackgroundScheduler
from matplotlib import pyplot as plt
from dicebear import DOptions
from python_files import Student, Teacher, Forms, Course
from python_files.Ticket import Ticket
from python_files.Cashout import Cashout
from python_files.Common import checkUniqueElements
from python_files.Security import sanitise, sanitise_quote
from python_files.IntegratedFunctions import *

"""Web app configurations"""
# general Flask configurations
app = Flask(__name__)
app.config["SECRET_KEY"] = "a secret key" # for demonstration purposes, if deployed, change it to something more secure
scheduler = BackgroundScheduler()

# Maximum file size for uploading anything to the web app's server
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024 # 200MiB

# Configurations for dicebear api for user profile image options
app.config["DICEBEAR_OPTIONS"] = DOptions(
    size=250
)

# creating an absolute path for storing the shelve files
app.config["DATABASE_FOLDER"] = str(app.root_path) + "\\databases"

# for image uploads file path
app.config["PROFILE_UPLOAD_PATH"] = "static/images/user"
app.config["THUMBNAIL_UPLOAD_PATH"] = "static/images/courses/thumbnails"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ("png", "jpg", "jpeg")

# for course video uploads file path
app.config["COURSE_VIDEO_FOLDER"] = "static/course_videos"
app.config["ALLOWED_VIDEO_EXTENSIONS"] = (
    ".mp4, .mov, .avi, .3gpp, .flv, .mpeg4, .flv, .webm, .mpegs, .wmv")

# configuration for email
# Make sure to enable access for less secure apps
app.config["MAIL_SERVER"] = "smtp.gmail.com" # using gmail
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "CourseFinity123@gmail.com" # using gmail
app.config["MAIL_PASSWORD"] = environ.get("EMAIL_PASS") # setting password but hiding the password for the CourseFinity123@gmail.com password using system environment variables
mail = Mail(app)

# paypal sdk configuration
paypalrestsdk.configure({
  "mode": "sandbox",
  "client_id": "AUTh83JMz8mLNGNzpzJRJSbSLUAEp7oe1ieGGqYCmVXpq427DeSVElkHnc0tt70b8gHlWg4yETnLLu1s",
  "client_secret": environ.get("PAYPAL_SECRET") })

# Flask limiter configuration
limiter = Limiter(app, key_func=get_remote_address, default_limits=["30 per second"])

"""End of Web app configurations"""

"""Home page by Jason"""

@app.route('/')
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
        courseDictCopy = courseDict.copy()
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
        for course in courseDict.values():
            if userDict.get(course.get_userID()).get_status() == "Good":
                trendingCourseList.append(course)

    # for retrieving the teacher's username
    trendingDict = {}
    for courses in trendingCourseList:
        teacherObject = userDict.get(courses.get_userID())
        teacherUsername = teacherObject.get_username()
        trendingDict[courses] = teacherUsername

    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            if accType != "Admin":
                # for recommendation algorithm
                recommendCourseList = []

                # removing purchased courses from being recommended since it has already been bought by the user
                userPurchasedCourses = userKey.get_purchases() # to be edited once the attribute in the class has been updated
                for courseID in list(courseDict.keys()):
                    if courseID in userPurchasedCourses:
                        print("User has purchased the course,", courseDict[courseID].get_title())
                        courseDict.pop(courseID)

                if len(courseDict) > 3:
                    userTagDict = userKey.get_tags_viewed()
                    numberOfUniqueViews = checkUniqueElements(userTagDict)
                    if numberOfUniqueViews > 1:
                        highestWatchedByTag = max(userTagDict, key=userTagDict.get)
                        userTagDict.pop(highestWatchedByTag)
                        numberOfUnqiueViews = checkUniqueElements(userTagDict)
                        if numberOfUnqiueViews > 1:
                            secondHighestWatchedByTag = max(userTagDict, key=userTagDict.get)
                        else:
                            print("User has watched some tags but only one tag is the highest while the rest of tags are the same (assuming the dictionary has not popped its highest tag yet)")
                            try:
                                # hence choosing one other random course objects
                                while True:
                                    randomisedCourse = random.choice(list(courseDict.values()))
                                    if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                                        recommendCourseList.append(randomisedCourse)
                                        courseDict.pop(randomisedCourse.get_courseID())
                                        break
                                    else:
                                        # if the teacher of the course has been banned
                                        courseDict.pop(randomisedCourse.get_courseID())
                            except:
                                print("No course found.")
                    else:
                        # choosing three random course objects
                        print("User has not watched any tags or has watched an equal balance of various tags.")
                        try:
                            while len(recommendCourseList) != 3:
                                randomisedCourse = random.choice(list(courseDict.values()))
                                if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                                    recommendCourseList.append(randomisedCourse)
                                    courseDict.pop(randomisedCourse.get_courseID())
                                else:
                                    # if the teacher of the course has been banned
                                    courseDict.pop(randomisedCourse.get_courseID())
                        except:
                            print("No courses found.")

                    print(courseDict)

                    recommendedCourseListByHighestTag = []

                    # checking current length of the recommendCourseList if the length is less than 3, then adding courses to make it a length of 3
                    courseListLen = len(recommendCourseList)
                    if courseListLen == 0: # condition will be true when the user has two unique highest tags
                        recommendedCourseListBySecondHighestTag = []
                        for courseObject in list(courseDict.values()):
                            courseTag = courseObject.get_tag()
                            if courseTag == highestWatchedByTag:
                                if userDict.get(courseObject.get_userID()).get_status() == "Good":
                                    recommendedCourseListByHighestTag.append(courseObject)
                                else:
                                    # if the teacher of the course has been banned
                                    courseDict.pop(courseObject.get_courseID())
                            elif courseTag == secondHighestWatchedByTag:
                                if userDict.get(courseObject.get_userID()).get_status() == "Good":
                                    recommendedCourseListBySecondHighestTag.append(courseObject)
                                else:
                                    # if the teacher of the course has been banned
                                    courseDict.pop(courseObject.get_courseID())

                        # appending course object for recommendations
                        count = 0
                        HighestTagCoursesAvailable = len(recommendedCourseListByHighestTag)
                        print("Courses available: ", HighestTagCoursesAvailable)

                        if HighestTagCoursesAvailable >= 2:
                            courseOne, courseTwo = random.sample(recommendedCourseListByHighestTag, 2)
                            recommendCourseList.append(courseOne)
                            recommendCourseList.append(courseTwo)
                            print("Two courses picked accordingly to user's highly watched tag.")

                            # picks one course for recommendations according to the user's second highly watched tag
                            SecondHighestTagCoursesAvailable = len(recommendedCourseListBySecondHighestTag)
                            print("Courses available: ", SecondHighestTagCoursesAvailable)
                            if SecondHighestTagCoursesAvailable >= 1:
                                randomisedCourse = random.choice(recommendedCourseListBySecondHighestTag)
                                recommendCourseList.append(randomisedCourse)
                                print("One course picked accordingly to user's second highly watched tag.")

                        elif HighestTagCoursesAvailable == 1:
                            # if there is only one course according to the user's highly watched tag (possibly due to a lack of courses, the teacher deleting the course, or the teacher being banned)
                            # recommends 1 courses according to the user's highly watched tag
                            course = recommendedCourseListByHighestTag[0]
                            recommendCourseList.append(course)
                            print("One course picked accordingly to user's highly watched tag.")

                            SecondHighestTagCoursesAvailable = len(recommendedCourseListBySecondHighestTag)
                            print("Courses available: ", SecondHighestTagCoursesAvailable)
                            if SecondHighestTagCoursesAvailable >= 2:

                                randomisedCourseOne, randomisedCourseTwo = random.sample(recommendedCourseListBySecondHighestTag, 2)

                                recommendCourseList.append(randomisedCourseOne)
                                recommendCourseList.append(randomisedCourseTwo)

                                print("Two courses picked accordingly to user's second highly watched tag.")
                            elif SecondHighestTagCoursesAvailable == 1:
                                course = recommendedCourseListBySecondHighestTag[0]
                                recommendCourseList.append(course)
                                print("One course picked accordingly to user's second highly watched tag.")
                        else:
                            # if there is only no courses according to the user's highly watched tag (possibly due to a lack of courses, the teacher deleting the course, or the teacher being banned)
                            # recommends 2 courses according to the user's second highly watched tag
                            SecondHighestTagCoursesAvailable = len(recommendedCourseListBySecondHighestTag)
                            print("Courses available: ", SecondHighestTagCoursesAvailable)
                            if SecondHighestTagCoursesAvailable >= 2:

                                randomisedCourseOne, randomisedCourseTwo = random.sample(recommendedCourseListBySecondHighestTag, 2)

                                recommendCourseList.append(randomisedCourseOne)
                                recommendCourseList.append(randomisedCourseTwo)
                                print("Two courses picked accordingly to user's second highly watched tag.")
                            elif SecondHighestTagCoursesAvailable == 1:
                                course = recommendedCourseListBySecondHighestTag[0]
                                recommendCourseList.append(course)
                                print("One course picked accordingly to user's second highly watched tag.")

                    elif courseListLen == 1: # condition will be true when the user has only one unique highest tag
                        for courseObject in list(courseDict.values()):
                            courseTag = courseObject.get_tag()
                            if courseTag == highestWatchedByTag:
                                if (userDict.get(courseObject.get_userID()).get_status() == "Good") and (courseObject not in recommendCourseList):
                                    recommendedCourseListByHighestTag.append(courseObject)
                                else:
                                    # if the teacher of the course has been banned or has already been recommended
                                    courseDict.pop(courseObject.get_courseID())

                        # appending course object for recommendations
                        HighestTagCoursesAvailable = len(recommendedCourseListByHighestTag)
                        print("Courses available: ", HighestTagCoursesAvailable)

                        if HighestTagCoursesAvailable >= 2:
                            courseOne, courseTwo = random.sample(recommendedCourseListByHighestTag, 2)
                            recommendCourseList.append(courseOne)
                            recommendCourseList.append(courseTwo)
                            print("Two courses picked accordingly to user's highly watched tag.")
                        elif HighestTagCoursesAvailable == 1:
                            # if there is only one course according to the user's highly watched tag (possibly due to a lack of courses, the teacher deleting the course, or the teacher being banned)
                            # recommends 1 courses according to the user's highly watched tag
                            course = recommendedCourseListByHighestTag[0]
                            recommendCourseList.append(course)
                            print("One course picked accordingly to user's highly watched tag.")

                    # in the event where there is insufficient courses to recommend, it will randomly choose another course object
                    recommendLen = len(recommendCourseList)
                    if recommendLen != 3:
                        print("Retrieving random courses as recommendations...")
                        while recommendLen != 3:
                            try:
                                randomisedCourse = random.choice(list(courseDict.values()))
                            except:
                                break
                            if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                                if randomisedCourse not in recommendCourseList:
                                    recommendCourseList.append(randomisedCourse)
                                    recommendLen = len(recommendCourseList)
                                else:
                                    courseDict.pop(randomisedCourse.get_courseID())
                            else:
                                courseDict.pop(randomisedCourse.get_courseID())
                else:
                    print("Not enough courses to personalise the recommendations...")
                    for value in courseDict.values():
                        if userDict.get(value.get_userID()).get_status() == "Good":
                            recommendCourseList.append(value)

                # retrieving course teacher's username
                recommedationDict = {}
                for courses in recommendCourseList:
                    teacherObject = userDict.get(courses.get_userID())
                    teacherUsername = teacherObject.get_username()
                    recommedationDict[courses] = teacherUsername

                # logged in users
                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""

                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())

                return render_template('users/general/home.html', shoppingCartLen=shoppingCartLen, accType=accType, imagesrcPath=imagesrcPath, trendingCourseDict=trendingDict, recommendCourseDict=recommedationDict, trendingCourseLen=len(trendingCourseList), recommendCourseLen=len(recommendCourseList), teacherUID=teacherUID, userPurchasedCourses=userPurchasedCourses)
            else:
                # admins
                recommendCourseList = get_random_courses(courseDict)

                # retrieving course teacher's username
                recommedationDict = {}
                for courses in recommendCourseList:
                    teacherObject = userDict.get(courses.get_userID())
                    teacherUsername = teacherObject.get_username()
                    recommedationDict[courses] = teacherUsername

                return render_template('users/general/home.html', accType=accType, imagesrcPath=imagesrcPath, trendingCourseDict=trendingDict, recommendCourseDict=recommedationDict, trendingCourseLen=len(trendingCourseList), recommendCourseLen=len(recommendCourseList))
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
                        print("User has watched some tags but only one tag is the highest while the rest of tags are the same (assuming the dictionary has not popped its highest tag yet)")
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
                    # choosing three random course objects
                    print("User has not watched any tags or has watched an equal balance of various tags.")
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
                    for courseObject in list(courseDict.values()):
                        courseTag = courseObject.get_tag()
                        if courseTag == highestWatchedByTag:
                            if userDict.get(courseObject.get_userID()).get_status() == "Good":
                                recommendedCourseListByHighestTag.append(courseObject)
                            else:
                                # if the teacher of the course has been banned
                                courseDict.pop(courseObject.get_courseID())
                        elif courseTag == secondHighestWatchedByTag:
                            if userDict.get(courseObject.get_userID()).get_status() == "Good":
                                recommendedCourseListBySecondHighestTag.append(courseObject)
                            else:
                                # if the teacher of the course has been banned
                                courseDict.pop(courseObject.get_courseID())

                    # appending course object for recommendations
                    count = 0
                    print("Courses available: ", len(recommendedCourseListByHighestTag))
                    HighestTagCoursesAvailable = len(recommendedCourseListByHighestTag)
                    if HighestTagCoursesAvailable >= 2:
                        courseOne, courseTwo = random.sample(recommendedCourseListByHighestTag, 2)
                        recommendCourseList.append(courseOne)
                        recommendCourseList.append(courseTwo)
                        print("Two courses picked accordingly to user's highly watched tag.")

                        # picks one course for recommendations according to the user's second highly watched tag
                        SecondHighestTagCoursesAvailable = len(recommendedCourseListBySecondHighestTag)
                        print("Courses available: ", SecondHighestTagCoursesAvailable)
                        if SecondHighestTagCoursesAvailable >= 1:

                            randomisedCourse = random.choice(recommendedCourseListBySecondHighestTag)
                            recommendCourseList.append(randomisedCourse)
                            print("One course picked accordingly to user's second highly watched tag.")

                    elif HighestTagCoursesAvailable == 1:
                        # if there is only one course according to the user's highly watched tag (possibly due to a lack of courses, the teacher deleting the course, or the teacher being banned)
                        # recommends 1 course according to the user's highly watched tag
                        course = recommendedCourseListByHighestTag[0]
                        recommendCourseList.append(course)
                        print("One course picked accordingly to user's highly watched tag.")

                        SecondHighestTagCoursesAvailable = len(recommendedCourseListBySecondHighestTag)
                        print("Courses available: ", SecondHighestTagCoursesAvailable)
                        if SecondHighestTagCoursesAvailable >= 2:

                            randomisedCourseOne, randomisedCourseTwo = random.sample(recommendedCourseListBySecondHighestTag, 2)

                            recommendCourseList.append(randomisedCourseOne)
                            recommendCourseList.append(randomisedCourseTwo)

                            print("Two courses picked accordingly to user's second highly watched tag.")
                        elif SecondHighestTagCoursesAvailable == 1:
                            course = recommendedCourseListBySecondHighestTag[0]
                            recommendCourseList.append(course)
                            print("One course picked accordingly to user's second highly watched tag.")
                    else:
                        # if there is only no courses according to the user's highly watched tag (possibly due to a lack of courses, the teacher deleting the course, or the teacher being banned)
                        # recommends 2 courses according to the user's second highly watched tag
                        SecondHighestTagCoursesAvailable = len(recommendedCourseListBySecondHighestTag)
                        print("Courses available: ", SecondHighestTagCoursesAvailable)
                        if SecondHighestTagCoursesAvailable >= 2:

                            randomisedCourseOne, randomisedCourseTwo = random.sample(recommendedCourseListBySecondHighestTag, 2)

                            recommendCourseList.append(randomisedCourseOne)
                            recommendCourseList.append(randomisedCourseTwo)

                            print("Two courses picked accordingly to user's second highly watched tag.")
                        elif SecondHighestTagCoursesAvailable == 1:
                            course = recommendedCourseListBySecondHighestTag[0]
                            recommendCourseList.append(course)
                            print("One course picked accordingly to user's second highly watched tag.")

                elif courseListLen == 1: # condition will be true when the user has one unique highest tag
                    for courseObject in list(courseDict.values()):
                        courseTag = courseObject.get_tag()
                        if courseTag == highestWatchedByTag:
                            if (userDict.get(courseObject.get_userID()).get_status() == "Good") and (courseObject not in recommendCourseList):
                                recommendedCourseListByHighestTag.append(courseObject)
                            else:
                                # if the teacher of the course has been banned or has already been recommended
                                courseDict.pop(courseObject.get_courseID())

                    print("Courses available: ", len(recommendedCourseListByHighestTag))
                    HighestTagCoursesAvailable = len(recommendedCourseListByHighestTag)
                    if HighestTagCoursesAvailable >= 2:
                        courseOne, courseTwo = random.sample(recommendedCourseListByHighestTag, 2)
                        recommendCourseList.append(courseOne)
                        recommendCourseList.append(courseTwo)
                        print("Two courses picked accordingly to user's highly watched tag.")
                    elif HighestTagCoursesAvailable == 1:
                        # if there is only one course according to the user's highly watched tag (possibly due to a lack of courses, the teacher deleting the course, or the teacher being banned)
                        # recommends 1 course according to the user's highly watched tag
                        course = recommendedCourseListByHighestTag[0]
                        recommendCourseList.append(course)
                        print("One course picked accordingly to user's highly watched tag.")

                # in the event where there is insufficient tags to recommend, it will randomly choose another course object
                recommendLen = len(recommendCourseList)
                if recommendLen != 3:
                    print("Retrieving random courses as recommendations...")
                    while recommendLen != 3:
                        try:
                            randomisedCourse = random.choice(list(courseDict.values()))
                        except:
                            break
                        if userDict.get(randomisedCourse.get_userID()).get_status() == "Good":
                            if randomisedCourse not in recommendCourseList:
                                recommendCourseList.append(randomisedCourse)
                                recommendLen = len(recommendCourseList)
                            else:
                                # if course has been recommended already
                                courseDict.pop(randomisedCourse.get_courseID())
                        else:
                            # if the teacher of the course has been banned
                            courseDict.pop(randomisedCourse.get_courseID())
            else:
                print("Not enough courses to personalise the recommendations...")
                for value in courseDict.values():
                    if userDict.get(value.get_userID()).get_status() == "Good":
                        recommendCourseList.append(value)

        # retrieving course teacher's username
        recommedationDict = {}
        for courses in recommendCourseList:
            teacherObject = userDict.get(courses.get_userID())
            teacherUsername = teacherObject.get_username()
            recommedationDict[courses] = teacherUsername

        return render_template("users/general/home.html", accType="Guest", trendingCourseDict=trendingDict, recommendCourseDict=recommedationDict, trendingCourseLen=len(trendingCourseList), recommendCourseLen=len(recommendCourseList))

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
            courseDictCopy = courseDict.copy()
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

        # for retrieving the teacher's username
        trendingDict = {}
        for courses in trendingCourseList:
            teacherObject = userDict.get(courses.get_userID())
            teacherUsername = teacherObject.get_username()
            trendingDict[courses] = teacherUsername

        recommendCourseDict = get_random_courses(courseDict)

        return render_template("users/general/home.html", accType="Guest", trendingCourseDict=trendingDict, recommendCourseDict=recommendCourseDict, trendingCourseLen=len(trendingCourseList), recommendCourseLen=len(recommendCourseDict))
    else:
        return redirect(url_for("home"))

"""End of Home pages by Jason"""

"""User login and logout by Jason"""

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10/second") # to prevent attackers from trying to crack passwords or doing enumeration attacks by sending too many automated requests from their ip address
def userLogin():
    if "userSession" not in session and "adminSession" not in session:
        create_login_form = Forms.CreateLoginForm(request.form)
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
            emailShelveData = ""

            # Checking the email input and see if it matches with any in the database
            print("Retrieving emails from database.")
            for key in userDict:
                emailShelveData = userDict[key].get_email()
                if emailInput == emailShelveData:
                    emailKey = userDict[key]
                    email_found = True
                    print("Email in database:", emailShelveData)
                    print("Email Input:", emailInput)
                    break

            # if the email is found in the shelve database, it will then validate the password input and see if it matches with the one in the database
            if email_found:
                password_matched = emailKey.verify_password(passwordInput)

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
                accGoodStatus = emailKey.get_status()
                if accGoodStatus == "Good":
                    # setting the user session based on the user's user ID
                    userID = emailKey.get_user_id()
                    if bool(emailKey.get_otp_setup_key()):
                        session["2FAUserSession"] = (userID, "login")
                        return redirect(url_for("twoFactorAuthentication"))
                    else:
                        session["userSession"] = userID
                        print("User account not banned, login successful.")
                        return redirect(url_for("home"))
                else:
                    flash("Your account have been banned. Please contact us if you think that this was a mistake.", "Danger")
                    print("User account banned.")
                    return render_template('users/guest/login.html', form=create_login_form)
            else:
                flash("Please check your entries and try again.", "Danger")
                return render_template('users/guest/login.html', form=create_login_form)
        else:
            return render_template('users/guest/login.html', form=create_login_form)
    else:
        return redirect(url_for("home"))

@app.route('/logout')
def logout():
    if "userSession" in session or "adminSession" in session:
        session.clear()
    else:
        return redirect(url_for("home"))
    flash("You have successfully logged out.", "You have logged out!")
    return redirect(url_for("home"))

"""End of User login and logout by Jason"""

"""2FA by Jason"""

@app.route('/2FA', methods=['GET', 'POST'])
@limiter.limit("10/second") # to prevent attackers from trying to crack passwords or doing enumeration attacks by sending too many automated requests from their ip address
def twoFactorAuthenticationSetup():
    if "userSession" in session:
        userSession = session["userSession"]
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear()
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            create_2fa_form = Forms.twoFAForm(request.form)
            qrCodePath = "".join(["static/images/qrcode/", userSession, ".png"])
            qrCodeFullPath = Path(app.root_path).joinpath(qrCodePath)
            if request.method == "POST" and create_2fa_form.validate():
                secret = request.form.get("secret")
                otpInput = sanitise(create_2fa_form.twoFAOTP.data)
                isValid = pyotp.TOTP(secret).verify(otpInput)
                print(pyotp.TOTP(secret).now())
                if isValid:
                    userKey.set_otp_setup_key(secret)
                    flash(Markup("2FA setup was successful!<br>You will now be prompted to enter your Google Authenticator's time-based OTP every time you login."), "2FA setup successful!")
                    db["Users"] = userDict
                    db.close()
                    qrCodeFullPath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)
                    return redirect(url_for("userProfile"))
                else:
                    db.close()
                    flash("Invalid OTP Entered! Please try again!")
                    return redirect(url_for("twoFactorAuthenticationSetup"))
            else:
                db.close()
                secret = pyotp.random_base32() # for google authenticator setup key

                imagesrcPath = retrieve_user_profile_pic(userKey)

                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""

                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())

                qrCodeForOTP = pyotp.totp.TOTP(s=secret, digits=6).provisioning_uri(name=userKey.get_username(), issuer_name='CourseFinity')
                img = qrcode.make(qrCodeForOTP)
                qrCodeFullPath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)
                img.save(qrCodeFullPath)
                return render_template('users/loggedin/2fa.html', shoppingCartLen=shoppingCartLen, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID, form=create_2fa_form, secret=secret, qrCodePath=qrCodePath)
        else:
            db.close()
            print("User not found or is banned")
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route('/2FA_disable')
@limiter.limit("10/second") # to prevent attackers from trying to crack passwords or doing enumeration attacks by sending too many automated requests from their ip address
def removeTwoFactorAuthentication():
    if "userSession" in session:
        userSession = session["userSession"]
        userDict = {}
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if 'Users' in db:
                userDict = db['Users']
            else:
                db.close()
                print("User data in shelve is empty.")
                session.clear()
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user.db")
            return redirect(url_for("home"))

        # retrieving the object based on the shelve files using the user's user ID
        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus:
            userKey.set_otp_setup_key("")
            flash(Markup("2FA has been disabled.<br>You will no longer be prompted to enter your Google Authenticator's time-based OTP upon loggin in."), "2FA disabled!")
            db["Users"] = userDict
            db.close()
            return redirect(url_for("userProfile"))
        else:
            db.close()
            print("User not found or is banned")
            session.clear()
            return redirect(url_for("userLogin"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

@app.route('/2FA_required', methods=['GET', 'POST'])
@limiter.limit("10/second") # to prevent attackers from trying to bruteforce the 2FA
def twoFactorAuthentication():
    # checks if the user is not logged in
    if "userSession" not in session and "adminSession" not in session:
        # for admin login
        if "adminOTPSession" in session:
            userID, originFeature = session["adminOTPSession"]
            adminDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\admin", "c")
            try:
                if 'Admins' in db:
                    adminDict = db['Admins']
                    db.close()
                else:
                    db.close()
                    print("User data in shelve is empty.")
                    session.clear()
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("home"))

            userKey, userFound, accActive = admin_get_key_and_validate(userID, adminDict)

            if userFound and accActive:
                if bool(userKey.get_otp_setup_key()):
                    create_2fa_form = Forms.twoFAForm(request.form)
                    if request.method == "POST" and create_2fa_form.validate():
                        otpInput = sanitise(create_2fa_form.twoFAOTP.data)
                        secret = userKey.get_otp_setup_key()
                        isValid = pyotp.TOTP(secret).verify(otpInput)
                        if isValid:
                            # requires 2FA time-based OTP to be entered when user is logging in
                            if originFeature == "adminLogin":
                                session.pop("2FAUserSession", None)
                                session["adminSession"] = userID
                                return redirect(url_for("home"))
                            else:
                                session.clear()
                                return redirect(url_for("home"))
                        else:
                            flash("Invalid OTP Entered! Please try again!")
                            return render_template("users/guest/enter_2fa.html", form=create_2fa_form)
                    else:
                        return render_template("users/guest/enter_2fa.html", form=create_2fa_form)
                else:
                    print("Unexpected Error: User had disabled 2FA.")
                    return redirect(url_for("userLogin"))
            else:
                print("User not found or is inactive")
                session.clear()
                return redirect(url_for("adminLogin"))

        # for user login
        elif "2FAUserSession" in session:
            userID, originFeature = session["2FAUserSession"]
            userDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'Users' in db:
                    userDict = db['Users']
                    db.close()
                else:
                    db.close()
                    print("User data in shelve is empty.")
                    session.clear()
                    return redirect(url_for("home"))
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                return redirect(url_for("home"))

            userKey, userFound, accGoodStatus, accType = get_key_and_validate(userID, userDict)

            if userFound and accGoodStatus:
                if bool(userKey.get_otp_setup_key()):
                    create_2fa_form = Forms.twoFAForm(request.form)
                    if request.method == "POST" and create_2fa_form.validate():
                        otpInput = sanitise(create_2fa_form.twoFAOTP.data)
                        secret = userKey.get_otp_setup_key()
                        isValid = pyotp.TOTP(secret).verify(otpInput)
                        if isValid:
                            # requires 2FA time-based OTP to be entered when user is logging in
                            if originFeature == "login":
                                session.pop("2FAUserSession", None)
                                session["userSession"] = userID
                                return redirect(url_for("home"))
                            else:
                                session.clear()
                                return redirect(url_for("home"))
                        else:
                            flash("Invalid OTP Entered! Please try again!")
                            return render_template("users/guest/enter_2fa.html", form=create_2fa_form)
                    else:
                        return render_template("users/guest/enter_2fa.html", form=create_2fa_form)
                else:
                    print("Unexpected Error: User had disabled 2FA.")
                    return redirect(url_for("userLogin"))
            else:
                print("User not found or is banned")
                session.clear()
                return redirect(url_for("userLogin"))
        else:
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))

"""End of 2FA by Jason"""

"""Reset Password by Jason"""

@app.route('/reset_password', methods=['GET', 'POST'])
def requestPasswordReset():
    if "userSession" not in session and "adminSession" not in session:
        create_request_form = Forms.RequestResetPasswordForm(request.form)

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
                        emailKey = userDict[key]
                        email_found = True
                        print("Email in database:", emailShelveData)
                        print("Email Input:", emailInput)
                        break

                if email_found:
                    print("User email found...")

                    # checking if the user is banned
                    accGoodStatus = emailKey.get_status()
                    if accGoodStatus == "Good":
                        try:
                            send_reset_email(emailInput, emailKey)
                            flash(Markup(f"An email has been sent to {emailInput} with instructions to reset your password.<br>Please check your email and your spam folder."), "Info")
                        except:
                            print("Email server is down or its port is blocked")
                            flash(Markup(f"An email with instructions has not been sent to {emailInput} due to email server downtime.<br>Please wait and try again or contact us!"), "Danger")
                        print("Email sent")
                        return render_template('users/guest/request_password_reset.html', form=create_request_form)
                    else:
                        # email found in database but the user is banned.
                        # However, it will still send an "email sent" alert to throw off enumeration attacks on banned accounts
                        print("User account banned, email not sent.")
                        flash(Markup(f"An email has been sent to {emailInput} with instructions to reset your password.<br>Please check your email and your spam folder."), "Info")
                        return render_template('users/guest/request_password_reset.html', form=create_request_form)
                else:
                    print("User email not found.")
                    # email not found in database, but will send an "email sent" alert to throw off enumeration attacks
                    flash(Markup(f"An email has been sent to {emailInput} with instructions to reset your password.<br>Please check your email and your spam folder."), "Info")
                    return render_template('users/guest/request_password_reset.html', form=create_request_form)
            else:
                # email not found in database, but will send an "email sent" alert to throw off enumeration attacks
                print("No user account records found.")
                print("Email Input:", emailInput)
                flash(Markup(f"An email has been sent to {emailInput} with instructions to reset your password.<br>Please check your email and your spam folder."), "Info")
                return render_template('users/guest/request_password_reset.html', form=create_request_form)
        else:
            return render_template('users/guest/request_password_reset.html', form=create_request_form)
    else:
        return redirect(url_for("home"))

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def resetPassword(token):
    if "userSession" not in session and "adminSession" not in session:
        validateToken = verify_reset_token(token)
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
            if userKey != None:
                twoFAEnabled = bool(userKey.get_otp_setup_key())

                create_reset_password_form = Forms.CreateResetPasswordForm(request.form)
                if request.method == "POST" and create_reset_password_form.validate():
                    password = create_reset_password_form.resetPassword.data
                    confirmPassword = create_reset_password_form.confirmPassword.data

                    if password == confirmPassword:
                        # checking if the user is banned
                        accGoodStatus = userKey.get_status()
                        if accGoodStatus == "Good":
                            if twoFAEnabled:
                                otpInput = sanitise_quote(request.form.get("otpInput"))
                                secret = userKey.get_otp_setup_key()
                                isValid = pyotp.TOTP(secret).verify(otpInput)
                            else:
                                isValid = True
                            if isValid:
                                userKey.set_password(password)
                                db["Users"] = userDict
                                db.close()
                                print("Password Reset Successful.")
                                flash("Your password has been updated! You can now login with your updated password.", "Success")
                                return redirect(url_for("userLogin"))
                            else:
                                flash("Invalid OTP!")
                                return render_template('users/guest/reset_password.html', form=create_reset_password_form, twoFAEnabled=twoFAEnabled)
                        else:
                            print("User account banned.")
                            flash("Your account has been banned, please contact us if you think that this is a mistake.")
                            return render_template('users/guest/reset_password.html', form=create_reset_password_form, twoFAEnabled=twoFAEnabled)
                    else:
                        flash("Passwords entered did not match!")
                        return render_template('users/guest/reset_password.html', form=create_reset_password_form, twoFAEnabled=twoFAEnabled)
                else:
                    db.close()
                    return render_template('users/guest/reset_password.html', form=create_reset_password_form, twoFAEnabled=twoFAEnabled)
            else:
                db.close()
                print("User not in database.")
                return redirect(url_for("userSignUp"))
        else:
            flash("Token is invalid or has expired.", "Danger")
            return redirect(url_for("requestPasswordReset"))
    else:
        return redirect(url_for("userProfile"))

"""End of Reset Password by Jason"""

"""Student signup process by Jason"""

@app.route('/signup', methods=['GET', 'POST'])
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
def verifyEmail():
    if "userSession" in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)

        if userFound and accGoodStatus:
            email = userKey.get_email()
            userID = userKey.get_user_id()
            emailVerified = userKey.get_email_verification()
            if emailVerified == "Not Verified":
                try:
                    send_another_verify_email(email, userID)
                    flash(Markup("We have sent you a verification link to verify your email.<br>Please make sure to check your email spam folder as well.<br>Do note that the link will expire in 1 day."), "Verification Email Sent")
                except:
                    print("Email server is down or its port is blocked")
                    flash("We have tried to send you a verification link to verify your email but it seems like the email server is down. Please try again later!", "Verification Email Sent")
            else:
                flash("Your email is already verified, there is no need to verify it again.", "Email Already Verified")
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
            if userKey != None:
                # checking if the user is banned
                accGoodStatus = userKey.get_status()
                if accGoodStatus == "Good":
                    emailVerification = userKey.get_email_verification()
                    if emailVerification == "Not Verified":
                        userKey.set_email_verification("Verified")
                        db["Users"] = userDict
                        db.close()

                        if "userSession" in session:
                            flash("Your email has been successfully verified!", "Email Verified")
                            return redirect(url_for("userProfile"))
                        else:
                            flash("Your email has been successfully verified!", "Email Verified")
                            return redirect(url_for("userLogin"))
                    else:
                        db.close()
                        if "userSession" in session:
                            flash("You have already verified your email.", "Email Already Verified")
                            return redirect(url_for("userProfile"))
                        else:
                            print("Email already verified")
                            flash("You have already verified your email.", "Email Already Verified")
                            return redirect(url_for("userLogin"))
                else:
                    db.close()
                    print("User account banned.")
                    return redirect(url_for("home"))
            else:
                db.close()
                print("User not found in database.")
                return redirect(url_for("userLogin"))
        else:
            print("Invalid/Expired Token.")
            if "userSession" in session:
                flash("Sorry! The link has been expired, please request for a new email verification link.", "Email Verification Expired")
                return redirect(url_for("userProfile"))
            else:
                flash("Sorry! The link has been expired, please request for a new email verification link.", "Email Verification Expired")
                return redirect(url_for("userLogin"))
    else:
        print("Admin is logged in.")
        return redirect(url_for("home"))

"""End of Email verification by Jason"""

"""Teacher's signup process by Jason"""

@app.route('/teacher_signup', methods=['GET', 'POST'])
def teacherSignUp():
    if "userSession" not in session and "adminSession" not in session:
        create_teacher_sign_up_form = Forms.CreateSignUpForm(request.form)

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
                    user.update_teacher_join_date_to_today()

                    userDict[userID] = user
                    db['Users'] = userDict

                    session["teacher"] = userID # to send the user ID under the teacher session for user verification in the sign up payment process

                    print("Teacher added.")

                    db.close()
                    try:
                        send_verify_email(emailInput, userID)
                    except:
                        print("Email server is down or its port is blocked")

                    session["userSession"] = userID

                    flash("Here you can update your Cashout Preferences. The default value will be your own email. Happy Teaching!","Teacher Sign Up Successful")
                    return redirect(url_for("cashoutPreference"))
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
            emailShelveData = ""

            # Checking the email input and see if it matches with any in the database
            print("Retrieving admin emails from admin database.")
            for key in adminDict:
                emailShelveData = adminDict[key].get_email()
                if emailInput == emailShelveData:
                    emailKey = adminDict[key]
                    email_found = True
                    print("Email in database:", emailShelveData)
                    print("Email Input:", emailInput)
                    break

            # if the email is found in the shelve database, it will then validate the password input and see if it matches with the one in the database
            if email_found:
                password_matched = emailKey.verify_password(passwordInput)

                if password_matched:
                    print("Correct password!")
                else:
                    print("Password incorrect.")
            else:
                print("Admin email not found in admin database.")

            if email_found and password_matched:
                print("Admin account validated...")

                # checking if the admin account is active
                accActiveStatus = emailKey.get_status()
                if accActiveStatus == "Active":
                    # setting the user session based on the user's user ID
                    userID = emailKey.get_user_id()
                    if bool(emailKey.get_otp_setup_key()):
                        print("Admin has 2FA enabled.")
                        session["adminOTPSession"] = (userID, "adminLogin")
                        return redirect(url_for("twoFactorAuthentication"))
                    else:
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
def adminProfile():
    if "adminSession" in session:
        adminSession = session["adminSession"]
        print(adminSession)

        userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)

        if userFound and accActive:
            username = userKey.get_username()
            email = userKey.get_email()
            admin_id = userKey.get_user_id()
            twoFAEnabled = bool(userKey.get_otp_setup_key())
            return render_template('users/admin/admin_profile.html', username=username, email=email, admin_id=admin_id, twoFAEnabled=twoFAEnabled)
        else:

            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/admin_change_username", methods=['GET', 'POST'])
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
                        flash(f"Username has been successfully changed from {currentUsername} to {updatedUsername}.", "Username Updated!")

                        db.close()
                        return redirect(url_for("adminProfile"))
                    else:
                        flash("Sorry, Username has already been taken!")
                        return render_template('users/admin/change_username.html', form=create_update_username_form)
                else:
                    print("Update username input same as user's current username")
                    flash("Sorry, you cannot change your username to your current username!")
                    return render_template('users/admin/change_username.html', form=create_update_username_form)
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
                        flash("Email has been successfully changed!", "Email Updated!")
                        db.close()
                        return redirect(url_for("adminProfile"))
                    else:
                        db.close()
                        flash("Sorry, the email you have entered is already taken by another user!")
                        return render_template('users/admin/change_email.html', form=create_update_email_form)
                else:
                    db.close()
                    print("User updated email input is the same as their current email")
                    flash("Sorry, you cannot change your email to your current email!")
                    return render_template('users/admin/change_email.html', form=create_update_email_form)
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
                if passwordVerification == False:
                    db.close()
                    flash("Entered current password is incorrect!")
                    return render_template('users/admin/change_password.html', form=create_update_password_form)
                else:
                    if passwordNotMatched:
                        db.close()
                        flash("New password and confirm password inputs did not match!")
                        return render_template('users/admin/change_password.html', form=create_update_password_form)
                    else:
                        if oldPassword:
                            db.close()
                            print("User cannot change password to their current password!")
                            flash("Sorry, you cannot change your password to your current password!")
                            return render_template('users/admin/change_password.html', form=create_update_password_form)
                        else:
                            # updating password of the user once validated
                            userKey.set_password(updatedPassword)
                            db['Admins'] = adminDict
                            print("Password updated")
                            db.close()
                            flash("Your password has been successfully updated!", "Password Updated")
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

@app.route("/admin_setup_2FA", methods=['GET', 'POST'])
def adminSetup2FA():
    if "adminSession" in session:
        adminSession = session["adminSession"]
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
            create_2fa_form = Forms.twoFAForm(request.form)
            qrCodePath = "".join(["static/images/qrcode/", adminSession, ".png"])
            qrCodeFullPath = Path(app.root_path).joinpath(qrCodePath)
            if request.method == "POST" and create_2fa_form.validate():
                secret = request.form.get("secret")
                otpInput = sanitise(create_2fa_form.twoFAOTP.data)
                isValid = pyotp.TOTP(secret).verify(otpInput)
                print(pyotp.TOTP(secret).now())
                if isValid:
                    userKey.set_otp_setup_key(secret)
                    flash(Markup("2FA setup was successful!<br>You will now be prompted to enter your Google Authenticator's time-based OTP every time you login."), "2FA setup successful!")
                    db["Admins"] = adminDict
                    db.close()
                    qrCodeFullPath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)
                    return redirect(url_for("adminProfile"))
                else:
                    db.close()
                    flash("Invalid OTP Entered! Please try again!")
                    return redirect(url_for("adminSetup2FA"))
            else:
                db.close()
                secret = pyotp.random_base32() # for google authenticator setup key

                qrCodeForOTP = pyotp.totp.TOTP(s=secret, digits=6).provisioning_uri(name=userKey.get_username(), issuer_name='CourseFinity')
                img = qrcode.make(qrCodeForOTP)
                qrCodeFullPath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)
                img.save(qrCodeFullPath)
                return render_template('users/admin/2fa.html', form=create_2fa_form, secret=secret, qrCodePath=qrCodePath)
        else:
            db.close()
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.route("/admin_disable_2FA")
def adminDisable2FA():
    if "adminSession" in session:
        adminSession = session["adminSession"]
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
            if bool(userKey.get_otp_setup_key()):
                userKey.set_otp_setup_key("")
                db["Admins"] = adminDict
                db.close()
                flash(Markup("2FA is enabled!<br>You will now no longer be prompted to enter your Google Authenticator's time-based OTP every time you login."), "2FA Disabled!")
                return redirect(url_for("adminProfile"))
            else:
                db.close()
                flash("Failed to remove 2FA as it is already disabled!", "2FA already disabled!")
                return redirect(url_for("adminProfile"))
        else:
            db.close()
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))


"""Admin profile settings by Jason"""

"""User Management for Admins by Jason"""

@app.route("/user_management/page/<int:pageNum>", methods=['GET', 'POST'])
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
                    userID = request.form["userID"]
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
                                    flash(Markup(f"User account has been recovered successfully for {userKey.get_username()}.<br>Additionally, an email has been sent to {userKey.get_email()}"), "User account recovered successfully!")
                                except:
                                    print("Email server is down or its port is blocked")
                                    flash(Markup(f"User account has been recovered successfully for {userKey.get_username()}.<br>However, the follow up email has not been sent due to possible email sever downtime.<br>Please manually send an update to {userKey.get_email()} with the updated password!"), "User account recovered successfully but email not sent!")
                                print("User account recovered successfully and email sent.")
                                return redirect(redirectURL)
                            else:
                                db.close()
                                print("Error in retrieving user object.")
                                return redirect(redirectURL)
                        else:
                            db.close()
                            print("Inputted new user's email is not unique.")
                            flash("Error: Inputted user's new email has been taken by another user, please enter a new and unique email and try again.", "User Account Recovery Failed")
                            return redirect(redirectURL)
                    else:
                        db.close()
                        print("User's new email inputted is the same as the old email.")
                        flash("Error: Inputted user's new email is the same as user's old email, please enter a new user email and try again.", "User Account Recovery Failed")
                        return redirect(redirectURL)
                else:
                    db.close()
                    print("Inputted new user's email is invalid.")
                    flash("Error: Inputted user's new email is invalid, please try again.", "User Account Recovery Failed")
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
                    session["pageNum"] = 0
                    return redirect("/user_management/page/0")
                elif userListLen > 0 and pageNum == 0:
                    session["pageNum"] = 1
                    return redirect("/user_management/page/1")
                elif pageNum > maxPages:
                    session["pageNum"] = maxPages
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
                        if (bool(userProfileFileName) == True) and (construct_path(app.config["PROFILE_UPLOAD_PATH"], userProfileFileName).is_file() == False):
                            value.set_profile_image("")

                    db["Users"] = userDict
                    db.close()

                    return render_template('users/admin/user_management.html', userList=paginatedUserList, count=userListLen, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, form=admin_reset_password_form, searched=False, parameter="")
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
                    userID = request.form["userID"]
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
                                    flash(Markup(f"User account has been recovered successfully for {userKey.get_username()}.<br>Additionally, an email has been sent to {userKey.get_email()}"), "User account recovered successfully!")
                                except:
                                    print("Email server is down or its port is blocked")
                                    flash(Markup(f"User account has been recovered successfully for {userKey.get_username()}.<br>However, the follow up email has not been sent due to possible email sever downtime.<br>Please manually send an update to {userKey.get_email()} with the updated password!"), "User account recovered successfully but email not sent!")
                                print("User account recovered successfully and email sent.")
                                return redirect(redirectURL)
                            else:
                                db.close()
                                print("Error in retrieving user object.")
                                return redirect(redirectURL)
                        else:
                            db.close()
                            print("Inputted new user's email is not unique.")
                            flash("Error: Inputted user's new email has been taken by another user, please enter a new and unique email and try again.", "User Account Recovery Failed")
                            return redirect(redirectURL)
                    else:
                        db.close()
                        print("User's new email inputted is the same as the old email.")
                        flash("Error: Inputted user's new email is the same as user's old email, please enter a new user email and try again.", "User Account Recovery Failed")
                        return redirect(redirectURL)
                else:
                    db.close()
                    print("Inputted new user's email is invalid.")
                    flash("Error: Inputted user's new email is invalid, please try again.", "User Account Recovery Failed")
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
                    session["pageNum"] = 0
                    redirectRoute = "/user_management/search/0/" + parametersURL
                    return redirect(redirectRoute)
                elif userListLen > 0 and pageNum == 0:
                    session["pageNum"] = 1
                    redirectRoute = "/user_management/search/1" + "/" + parametersURL
                    return redirect(redirectRoute)
                elif pageNum > maxPages:
                    session["pageNum"] = maxPages
                    redirectRoute = "/user_management/search/" + str(maxPages) +"/" + parametersURL
                    return redirect(redirectRoute)
                else:
                   # pagination algorithm starts here
                    userList = userList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                    pageNumForPagination = pageNum - 1 # minus for the paginate function
                    paginatedUserList = paginate(userList, pageNumForPagination, maxItemsPerPage)
                    paginationList = get_pagination_button_list(pageNum, maxPages)

                    session["pageNum"] = pageNum

                    previousPage = pageNum - 1
                    nextPage = pageNum + 1

                    # auto fixing user profile image if the user has uploaded but the image is no longer on the web server directory
                    for value in paginatedUserList:
                        userProfileFileName = value.get_profile_image()
                        if (bool(userProfileFileName) == True) and (construct_path(app.config["PROFILE_UPLOAD_PATH"], userProfileFileName).is_file() == False):
                            value.set_profile_image("")

                    db["Users"] = userDict
                    db.close()

                    session["searchedPageRoute"] = "/user_management/search/" + str(pageNum) + "/" + parametersURL

                    return render_template('users/admin/user_management.html', userList=paginatedUserList, count=userListLen, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, form=admin_reset_password_form, searched=True, parameter=parameter)
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

@app.post("/delete_user/uid/<userID>")
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
                    if "Courses" in db:
                        courseDict = db['Courses']
                    else:
                        courseDict = {}
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

                # deletes any courses if the teacher has uploaded any courses previously
                if userKey.get_acc_type() == "Teacher":
                    numOfCoursesTeaching = len(userKey.get_coursesTeaching())
                    if numOfCoursesTeaching >= 1:
                        courseDictCopy = courseDict.copy()
                        for courseID, course in courseDictCopy.items():
                            if course.get_userID() == userID:
                                courseDict.pop(courseID)

                userDict.pop(userID)
                db["Courses"] = courseDict
                db['Users'] = userDict
                db.close()

                if bool(userImageFileName):
                    delete_user_profile(userImageFileName)

                print(f"User account with the ID, {userID}, has been deleted.")
                flash(f"User with user ID, {userID}, has been successfully deleted.", "User has been deleted")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                flash(f"User with user ID, {userID}, was not found in the database.", "Failed to delete user")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.post("/ban/uid/<userID>")
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
                flash(f"User with user ID, {userID}, has been successfully banned.", "User has been banned")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                flash(f"User with user ID, {userID}, was not found in the database.", "Failed to ban user")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.post("/unban/uid/<userID>")
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
                    flash(Markup(f"{userKey.get_username()} has been unbanned.<br>Additionally, an email has been sent to {userKey.get_email()}"), "User account has been unbanned!")
                except:
                    print("Email server is down or its port is blocked")
                    flash(Markup(f"{userKey.get_username()} has been unbanned.<br>However, the follow up email has not been sent due to possible email sever downtime.<br>Please manually send an update to {userKey.get_email()} to alert the user of the unban!"), "User account has been unbanned but email not sent!")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                flash(f"User with user ID, {userID}, was not found in the database.", "Failed to unban user")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.post("/change_username/uid/<userID>")
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
                    flash(f"User with user ID, {userID}, has its username changed to {username} from {userKey.get_username()}.", "User's username changed")
                    return redirect(redirectURL)
                else:
                    db.close()
                    print("Duplicate username.")
                    flash(f"Failed to change user's username with user ID, {userID}, as the username, {username} has already been taken", "Failed to change user's username")
                    return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                flash(f"User with user ID, {userID}, was not found in the database.", "Failed to change user's username")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.post("/reset_profile_image/uid/<userID>")
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
                if bool(userImageFileName):
                    delete_user_profile(userImageFileName)
                print(f"User account with the ID, {userID}, has its profile picture reset.")
                flash(f"User account with the ID, {userID}, profile picture has been reset and deleted from the web server successfully.", "User's profile picture has been reset!")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                flash(f"User with user ID, {userID}, was not found in the database.", "Failed to delete user's profile picture")
                return redirect(redirectURL)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the admin login page
            session.clear()
            return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

@app.post('/2FA_disable/uid/<userID>')
@limiter.limit("10/second") # to prevent attackers from trying to crack passwords or doing enumeration attacks by sending too many automated requests from their ip address
def adminRemoveTwoFactorAuthentication(userID):
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
                userKey.set_otp_setup_key("")
                db['Users'] = userDict
                db.close()
                print(f"User account with the ID, {userID}, 2FA has been removed.")
                flash(f"User with user ID, {userID}, has its 2FA removed.", "User's 2FA Removed'")
                return redirect(redirectURL)
            else:
                db.close()
                print("Error in retrieving user object.")
                flash(f"User with user ID, {userID}, was not found in the database.", "Failed to remove user's 2FA")
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
            userDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if 'userGraphData' in db and "Users" in db:
                    graphList = db['userGraphData']
                    userDict = db['Users']
                else:
                    print("No data in user shelve files")
                    db["userGraphData"] = graphList
                    db['Users'] = userDict
            except:
                print("Error in retrieving userGraphData from user.db")
            finally:
                db.close()

            try:
                lastUpdated = graphList[-1].get_lastUpdate() # retrieve latest object
            except:
                lastUpdated = str(datetime.now().strftime("%d/%m/%Y, %H:%M:%S (UTC +8)"))

            selectedGraphDataList = graphList[-30:] # get last 30 elements from the list to show the total number of user per day for the last 30 days
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

            csvFilePath = "static/data/user_base/csv/user_base.csv"

            # for generating the csv data to collate all data as the visualisation on the web app only can show the last 30 days
            with open(csvFilePath, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Dates", "Number Of Users"])
                for key, value in graphDict.items():
                    writer.writerow([key, value])

            userDataCSVFilePath = "static/data/users/csv/user_database.csv"
            # for generating the csv data to collate all user data for other purposes such as marketing, etc.
            with open(userDataCSVFilePath, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["UserID","Username", "Email", "Email Verification", "2FA Enabled", "Account Type", "Teacher Joined Date", "Account Status", "Number of Courses Teaching","Highly Watched Tag", "No. of Purchases"])
                for key, value in userDict.items():
                    # get number of courses teaching
                    try:
                        numOfCourseTeaching = len(value.get_coursesTeaching())
                    except:
                        # if the user is a student
                        numOfCourseTeaching = "N/A"

                    # getting the date when the user joined as a teacher in CourseFinity
                    teacherJoinedDate = value.get_teacher_join_date()
                    if bool(teacherJoinedDate) != True:
                        # by default, it will be an empty string hence, show "N/A" in the csv file if the user is a student
                        teacherJoinedDate = "N/A"

                    # check if the user has enabled 2FA
                    if bool(value.get_otp_setup_key()):
                        twoFAEnabled = "Yes"
                    else:
                        twoFAEnabled = "No"
                    writer.writerow([key, value.get_username(), value.get_email(), value.get_email_verification(), twoFAEnabled, value.get_acc_type(), teacherJoinedDate, value.get_status(), numOfCourseTeaching, value.get_highest_tag(), len(value.get_purchases())])

            return render_template('users/admin/admin_dashboard.html', lastUpdated=lastUpdated, xAxisData=xAxisData, yAxisData=yAxisData, figureFilename=figureFilename, csvFilePath=csvFilePath, userDataCSVFilePath=userDataCSVFilePath)
        else:
            print("Admin account is not found or is not active.")
            # if the admin is not found/inactive for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            # determine if it make sense to redirect the admin to the home page or the admin login page
            return redirect(url_for("home"))
            # return redirect(url_for("adminLogin"))
    else:
        return redirect(url_for("home"))

# block users that are not admins from accessing the files
@app.route("/static/data/<folder>/<childFolder>/<filename>")
def blockAccessToData(folder, childFolder, filename):
    if "adminSession" in session:
        adminSession = session["adminSession"]

        userKey, userFound, accActive = admin_get_key_and_validate_open_file(adminSession)

        if userFound and accActive:
            directoryPath = "".join([str(app.root_path), "\\static\\data\\", folder, "\\", childFolder])
            return send_from_directory(directoryPath, filename, as_attachment=True)
        else:
            abort(403)
    else:
        abort(403)

"""End of Admin Data Visualisation (Total user per day) by Jason"""

"""User Profile Settings by Jason"""

@app.route('/user_profile', methods=["GET","POST"])
@limiter.limit("80/second") # to prevent ddos attacks
def userProfile():
    if "userSession" in session:
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
                    defaultMessage = "Enter a bio to tell students of CourseFinity about you and what you are teaching! (You can also resize the text box by dragging on the bottom right of this text box)"
                    if teacherBioInput == False or teacherBioInput == defaultMessage:
                        teacherBioInput = ""
                    userKey.set_bio(teacherBioInput)
                    db['Users'] = userDict
                    db.close()
                    print("Teacher bio saved.")
                    flash("Your bio has been successfully saved.", "Bio Updated!")
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
                        newFilePath = construct_path(app.config["PROFILE_UPLOAD_PATH"], userImageFileName)

                        if currentChunk == 0:
                            newFilePath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)

                        print("Total file size:", int(request.form['dztotalfilesize']))

                        try:
                            with open(newFilePath, "ab") as imageData: # ab flag for opening a file for appending data in binary format
                                imageData.seek(int(request.form['dzchunkbyteoffset']))
                                print("dzchunkbyteoffset:", int(request.form['dzchunkbyteoffset']))
                                imageData.write(file.stream.read())
                        except OSError:
                            print('Could not write to file')
                            return make_response("Error writing to file", 500)
                        except:
                            print("Unexpected error.")
                            return make_response("Unexpected error", 500)

                        if currentChunk + 1 == totalChunks:
                            # This was the last chunk, the file should be complete and the size we expect
                            if newFilePath.stat().st_size != int(request.form['dztotalfilesize']):
                                print(f"File {file.filename} was completed, but there is a size mismatch. Received {newFilePath.stat().st_size} but had expected {request.form['dztotalfilesize']}")
                                # remove corrupted image
                                newFilePath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)
                                return make_response("Uploaded image is corrupted! Please try again!", 500)
                            else:
                                print(f'File {file.filename} has been uploaded successfully')
                                # constructing a file path to see if the user has already uploaded an image and if the file exists
                                userOldImageFilename = userKey.get_profile_image()
                                if bool(userOldImageFilename):
                                    userOldImageFilePath = construct_path(app.config["PROFILE_UPLOAD_PATH"], userOldImageFilename)

                                    # using Path from pathlib to check if the file path of userID.png (e.g. 0.png) already exist.
                                    # since dropzone will actually send multiple requests,
                                    if userOldImageFilePath != newFilePath:
                                        print("User has already uploaded a profile image before.")
                                        userOldImageFilePath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)
                                        print("Old Image file has been deleted.")

                                # resizing the image to a 1:1 ratio and compresses it and converts to a webp
                                imageResized, newImageFilePath = resize_image(newFilePath, (250, 250))

                                if imageResized:
                                    # if file was successfully resized, it means the image is a valid image
                                    userKey.set_profile_image(newImageFilePath.name) # saves the filename with its extension only instead of the full file path
                                    db['Users'] = userDict
                                    db.close()
                                    flash("Your profile image has been successfully saved.", "Profile Image Updated")
                                    return make_response(("Profile Image Uploaded!", 200))
                                else:
                                    # else this means that the image is not an image since Pillow is unable to open the image due to it being an unsupported image file or due to corrupted image in which the code below will reset the user's profile image
                                    userKey.set_profile_image("")
                                    db['Users'] = userDict
                                    db.close()
                                    newFilePath.unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)
                                    return make_response("Uploaded image is corrupted! Please try again!", 500)
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
                    profileFilePath = construct_path(app.config["PROFILE_UPLOAD_PATH"], userImageFileName)
                    # check if the user has already uploaded an image and checks if the image file path exists on the web server before deleting it
                    if bool(userImageFileName) != False:
                        Path(profileFilePath).unlink(missing_ok=True) # missing_ok argument is set to True as the file might not exist (>= Python 3.8)
                    userKey.set_profile_image("")
                    db['Users'] = userDict
                    db.close()
                    print("User profile image deleted.")
                    flash("Your profile image has been successfully deleted.", "Profile Image Deleted")
                    return redirect(url_for("userProfile"))
                else:
                    db.close()
                    print("Form value tampered or POST request sent without form value...")
                    return redirect(url_for("userProfile"))
            else:
                db.close()
                userUsername = userKey.get_username()
                userEmail = userKey.get_email()

                # checking if the user have uploaded a profile image before and if the image file exists
                userProfileFilenameSaved = bool(userKey.get_profile_image())
                imagesrcPath, profileReset = get_user_profile_pic(userSession)
                if profileReset:
                    userProfileFilenameSaved = False

                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""

                if accType == "Teacher":
                    teacherBio = userKey.get_bio()
                else:
                    teacherBio = ""

                twoFAEnabled = bool(userKey.get_otp_setup_key())

                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())

                return render_template('users/loggedin/user_profile.html', shoppingCartLen=shoppingCartLen, username=userUsername, email=userEmail, accType = accType, teacherBio=teacherBio, imagesrcPath=imagesrcPath, emailVerification=emailVerification, emailVerified=emailVerified, teacherUID=teacherUID, userProfileFilenameSaved=userProfileFilenameSaved, twoFAEnabled=twoFAEnabled)
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
def updateUsername():
    if "userSession" in session:
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

            # Get shopping cart len
            shoppingCartLen = len(userKey.get_shoppingCart())

            if request.method == "POST" and create_update_username_form.validate():
                updatedUsername = sanitise(create_update_username_form.updateUsername.data)
                currentUsername = userKey.get_username()

                if updatedUsername != currentUsername:
                    # checking duplicates for username
                    username_duplicates = False
                    for key in userDict:
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
                        flash(f"Username has been successfully changed from {currentUsername} to {updatedUsername}.", "Username Updated!")
                        db.close()
                        return redirect(url_for("userProfile"))
                    else:
                        db.close()
                        flash("Sorry, Username has already been taken!")
                        return render_template('users/loggedin/change_username.html', form=create_update_username_form, accType=accType, imagesrcPath=imagesrcPath, teacherUID = teacherUID, shoppingCartLen=shoppingCartLen)
                else:
                    db.close()
                    print("Update username input same as user's current username")
                    flash("Sorry, you cannot change your username to your current username!")
                    return render_template('users/loggedin/change_username.html', form=create_update_username_form, accType=accType, imagesrcPath=imagesrcPath, teacherUID = teacherUID, shoppingCartLen=shoppingCartLen)
            else:
                db.close()
                return render_template('users/loggedin/change_username.html', form=create_update_username_form, accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID = teacherUID)
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
def updateEmail():
    if "userSession" in session:
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

            # Get shopping cart len
            shoppingCartLen = len(userKey.get_shoppingCart())

            if request.method == "POST" and create_update_email_form.validate():

                updatedEmail = sanitise(create_update_email_form.updateEmail.data.lower())
                currentEmail = userKey.get_email()
                if updatedEmail != currentEmail:
                    # Checking duplicates for email
                    email_duplicates = False
                    for key in userDict:
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
                        try:
                            send_email_change_notification(currentEmail, updatedEmail) # sending an email to alert the user of the change of email so that the user will know about it and if his/her account was compromised, he/she will be able to react promptly by contacting CourseFinity support team
                            flash(Markup("Email has been successfully changed!<br>An email has been sent with a link to verify your updated email."), "Email Updated!")
                        except:
                            print("Email server down or email server port is blocked.")
                            flash(Markup("Your email has been successfully changed!<br>However, we are unable to send an email to your updated email with a link for email verification.<br>Please wait and try again later."), "Email Updated!")
                        return redirect(url_for("userProfile"))
                    else:
                        db.close()
                        flash("Sorry, the email you have entered is already taken by another user!")
                        return render_template('users/loggedin/change_email.html', form=create_update_email_form, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID, shoppingCartLen=shoppingCartLen)
                else:
                    db.close()
                    print("User updated email input is the same as their current email")
                    flash("Sorry, you cannot change your email to your current email!")
                    return render_template('users/loggedin/change_email.html', form=create_update_email_form, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID, shoppingCartLen=shoppingCartLen)
            else:
                db.close()
                return render_template('users/loggedin/change_email.html', form=create_update_email_form, accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
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
def updatePassword():
    if "userSession" in session:
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

            # Get shopping cart len
            shoppingCartLen = len(userKey.get_shoppingCart())

            if request.method == "POST" and create_update_password_form.validate():
                # declaring passwordNotMatched, passwordVerification, and errorMessage variable to initialise and prevent unboundLocalError
                passwordNotMatched = True
                passwordVerification = False

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
                if passwordVerification == False:
                    db.close()
                    flash("Entered current password is incorrect!")
                    return render_template('users/loggedin/change_password.html', shoppingCartLen=shoppingCartLen, form=create_update_password_form, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
                else:
                    if passwordNotMatched:
                        db.close()
                        flash("New password and confirm password inputs did not match!")
                        return render_template('users/loggedin/change_password.html', shoppingCartLen=shoppingCartLen, form=create_update_password_form, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
                    else:
                        if oldPassword:
                            db.close()
                            print("User cannot change password to their current password!")
                            flash("Sorry, you cannot change your password to your current password!")
                            return render_template('users/loggedin/change_password.html', shoppingCartLen=shoppingCartLen, form=create_update_password_form, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
                        else:
                            # updating password of the user once validated
                            userKey.set_password(updatedPassword)
                            userEmail = userKey.get_email()
                            db['Users'] = userDict
                            print("Password updated")
                            db.close()

                            try:
                                send_password_change_notification(userEmail) # sending an email to alert the user of the change of password so that the user will know about it and if his/her account was compromised, he/she will be able to react promptly by contacting CourseFinity support team or if the email was not changed, he/she can reset his/her password in the reset password page
                            except:
                                print("Email server is down or its port is blocked")

                            flash("Your password has been successfully updated!", "Password Updated")
                            return redirect(url_for("userProfile"))
            else:
                db.close()
                return render_template('users/loggedin/change_password.html', form=create_update_password_form, accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
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
def changeAccountType():
    if "userSession" in session:
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

                    # retrieving the user's profile image filename if the user has uploaded one
                    profileImageExists = bool(userKey.get_profile_image())
                    print("Does user have profile image:", profileImageExists)
                    if profileImageExists:
                        profileImageFilename = userKey.get_profile_image()
                        imagePath = construct_path(app.config["PROFILE_UPLOAD_PATH"], profileImageFilename)
                        if imagePath.is_file():
                            profileImagePathExists = True
                            print("Profile image exists:", profileImagePathExists)
                        else:
                            profileImagePathExists = False

                    user = Teacher.Teacher(userID, username, email, "") # password will be empty string as placeholder as to avoid hashing a hash
                    user.set_password_hash(password) # set the hash as the user password
                    user.update_teacher_join_date_to_today()

                    # saving the user's profile image if the user has uploaded their profile image
                    if profileImageExists and profileImagePathExists:
                        user.set_profile_image(profileImageFilename)

                    # checking if the user has already became a teacher
                    # Not needed but for scability as if there's a feature that allows teachers to revert back to a student in the future, the free three months 0% commission system can be abused.
                    if bool(userKey.get_teacher_join_date()) == False:
                        user.update_teacher_join_date_to_today()
                        print("User has not been a teacher, setting today's date as joined date.")

                    if bool(userKey.get_purchases()):
                        user.set_purchases(userKey.get_purchases())

                    if bool(userKey.get_shoppingCart()):
                        user.set_shoppingCart(userKey.get_shoppingCart())

                    if bool(userKey.get_otp_setup_key()):
                        user.set_otp_setup_key(userKey.get_otp_setup_key())

                    user.set_tags_viewed(userKey.get_tags_viewed())

                    userDict[userID] = user # overrides old student object with the new teacher object
                    db["Users"] = userDict
                    db.close()
                    print("Account type updated to teacher.")
                    flash(Markup("Congratulations!<br>You have successfully become a teacher!<br>Please do not hesitate to contact us if you have any concerns, we will be happy to help!"), "Account Type Updated to Teacher")
                    return redirect(url_for("userProfile"))
                else:
                    print("Not POST request or did not have relevant hidden field.")
                    db.close()
                    return redirect(url_for("userProfile"))
            else:
                db.close()
                print("User is not a student.")
                # if the user is not a student but visits this webpage, it will redirect the user to the user profile page
                flash("You are already a teacher. If you require further assistance, feel free to contact us!", "Sorry!")
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

"""Cashout Preference View by Wei Ren"""

@app.route('/cashout_preference', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def cashoutPreference():
    if "userSession" in session:
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
                imagesrcPath = retrieve_user_profile_pic(userKey)

                # Initialise values
                cashoutForm = Forms.CashoutForm(request.form)
                phoneError = False


                renderedInfo = {}

                # Get preference value for rendering
                if userKey.get_cashoutPreference() == "Email":
                    renderedInfo["Preference"] = "Email"
                elif userKey.get_cashoutPreference() == "Phone":
                    renderedInfo["Preference"] = "Phone"

                # Get email for rendering
                renderedInfo["Email"] = userKey.get_email()

                # Check if phone data is saved
                if userKey.get_cashoutPhone() != None:
                    print("Yes Phone Exist")

                    # Get phone number object
                    phoneObject = phonenumbers.parse(userKey.get_cashoutPhone())

                    # Get phone number for rendering
                    renderedInfo["Phone Number"] = phoneObject.national_number

                    # Pre-set country code to saved value before rendering: Done
                    countryCode = "+" + str(phoneObject.country_code)
                    for choice in cashoutForm.countryCode.choices[1:]:
                        countryCodeChoice = list(choice)[0]
                        if countryCodeChoice == countryCode:
                            renderedInfo['Country Code'] = countryCodeChoice
                else:
                    renderedInfo['Phone Number'] = ""
                    renderedInfo['Country Code'] = ""

                print("Phone Error:", phoneError)
                print("Preference:", userKey.get_cashoutPreference())
                print("Phone Number:", userKey.get_cashoutPhone())
                print("International:",renderedInfo['Phone Number'])
                print("Country Code:",renderedInfo['Country Code'])
                print("Phone Validation:",userKey.get_phoneVerification())

                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())

                db.close()
                print("Yes Return?")
                return render_template('users/teacher/cashout_preference.html', shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, phoneError=phoneError, cashoutForm=cashoutForm, renderedInfo=renderedInfo, teacherUID=userSession, accType=accType)
            else:
                db.close()
                print("User is a student.")
                return redirect(url_for("userProfile"))
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

"""End of Cashout Preference View by Wei Ren"""

"""Cashout Preference Edit by Wei Ren"""

@app.route('/edit_cashout_preference', methods=["GET","POST"])
@limiter.limit("30/second") # to prevent ddos attacks
def editCashoutPreference():
    if "userSession" in session:
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
                imagesrcPath = retrieve_user_profile_pic(userKey)

                # Initialise values
                cashoutForm = Forms.CashoutForm(request.form)
                phoneError = False

                # Save changes, or delete email info
                if request.method == "POST" and cashoutForm.validate():
                    print(cashoutForm.data)
                    print("POST request sent and form entries validated")

                    # Initialise variables
                    cashoutPreference = cashoutForm.cashoutPreference.data
                    phoneNumber = cashoutForm.phoneNumber.data
                    countryCode = cashoutForm.countryCode.data
                    print(countryCode) # Afghanistan (+93)
                    print('Yes Post')
                    print(json.loads(cashoutForm.deleteInfo.data))

                    # Check if deleting info
                    if json.loads(cashoutForm.deleteInfo.data) == True:
                        print('Yes Delete')
                        userKey.set_cashoutPreference("Email")
                        userKey.set_cashoutPhone(None)
                        userKey.set_phoneVerification("Not Verified")

                    elif cashoutPreference == "Phone":
                        print('Yes Phone')

                        # Validate phone number
                        try:
                            fullPhoneNumber = countryCode + phoneNumber
                            phoneObject = phonenumbers.parse(fullPhoneNumber, None)
                            if phonenumbers.is_possible_number(phoneObject):
                                userKey.set_cashoutPhone(fullPhoneNumber)
                                if phonenumbers.is_valid_number(phoneObject):
                                    userKey.set_phoneVerification("Verified")
                                else:
                                    userKey.set_phoneVerification("Not Verified")
                            else:
                                phoneError = True
                        except:
                            print("Something went wrong. Parsing error?")
                            phoneError = True

                        # Set email as preference
                        userKey.set_cashoutPreference(cashoutPreference)

                    elif cashoutPreference == "Email":
                        print("Yes Email")
                        # Set email as preference
                        userKey.set_cashoutPreference(cashoutPreference)

                    # Check whether phone validation successful
                    if phoneError:
                        print("Yes Phone Error")

                        # Get entered info for rendering again
                        renderedInfo = {"Preference": cashoutPreference,
                                        "Phone Number": phoneNumber,
                                        "Email": userKey.get_email()}

                        # Pre-set country code to previously input value before rendering
                        renderedInfo['Country Code'] = ""
                        for choice in cashoutForm.countryCode.choices:
                            print(countryCode)
                            if list(choice)[0] == countryCode:
                                renderedInfo['Country Code'] = choice
                                print(cashoutForm.countryCode.data)

                    else:
                        print("Yes Success")
                        # Save values if no errors
                        userDict[userKey.get_user_id()] = userKey
                        db['Users'] = userDict
                        print("Payment added")

                        if not json.loads(cashoutForm.deleteInfo.data):
                            flash("Your cashout preferences has been successfully edited.", "Cashout Preferences Edited")
                        else:
                            flash("Your cashout phone info has been successfully deleted.", "Cashout Phone Info Deleted")

                        return redirect(url_for('cashoutPreference'))

                else:
                    print("Yes Alright")
                    renderedInfo = {}

                    # Get preference value for rendering
                    if userKey.get_cashoutPreference() == "Email":
                        renderedInfo["Preference"] = "Email"
                    elif userKey.get_cashoutPreference() == "Phone":
                        renderedInfo["Preference"] = "Phone"

                    # Get email for rendering
                    renderedInfo["Email"] = userKey.get_email()

                    # Check if phone data is saved
                    if userKey.get_cashoutPhone() != None:
                        print("Yes Phone Exist")

                        # Get phone number object
                        phoneObject = phonenumbers.parse(userKey.get_cashoutPhone())

                        # Get phone number for rendering
                        renderedInfo["Phone Number"] = phoneObject.national_number

                        # Pre-set country code to saved value before rendering: Done
                        countryCode = "+" + str(phoneObject.country_code)
                        print(cashoutForm.countryCode.choices)
                        for choice in cashoutForm.countryCode.choices[1:]:
                            countryCodeChoice = list(choice)[0]
                            if countryCodeChoice == countryCode:
                                renderedInfo['Country Code'] = countryCodeChoice
                    else:
                        renderedInfo['Phone Number'] = ""
                        renderedInfo['Country Code'] = ""


                print("Phone Error:", phoneError)
                print("Preference:", userKey.get_cashoutPreference())
                print("Phone Number:", userKey.get_cashoutPhone())
                print("International:",renderedInfo['Phone Number'])
                print("Country Code Entered:",cashoutForm.countryCode.data)
                print("Country Code:", renderedInfo['Country Code'])
                print("Phone Validation:",userKey.get_phoneVerification())

                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())

                db.close()
                print("Yes Return?")
                return render_template('users/teacher/edit_cashout_preference.html', shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, phoneError=phoneError, cashoutForm=cashoutForm, renderedInfo=renderedInfo, teacherUID=userSession, accType=accType)
            else:
                db.close()
                print("User is a student.")
                return redirect(url_for("userProfile"))
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

"""End of Cashout Preference Edit by Wei Ren"""

"""Teacher Cashout System by Jason"""
"""PayPal Integration by Wei Ren"""

@app.route("/teacher_cashout", methods=['GET', 'POST'])
def teacherCashOut():
    if "userSession" in session:
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
                imagesrcPath = retrieve_user_profile_pic(userKey)
                joinedDate = userKey.get_teacher_join_date()
                zeroCommissionEndDate = joinedDate + timedelta(days=90)
                currentDate = date.today()

                # if it's the first day of the month
                resetMonth = check_first_day_of_month(currentDate)
                initialEarnings = userKey.get_earnings()
                accumulatedEarnings = userKey.get_accumulated_earnings()
                if resetMonth:
                    accumulatedEarnings += initialEarnings
                    userKey.set_accumulated_earnings(accumulatedEarnings)
                    userKey.set_earnings(0)

                lastDayOfMonth = check_last_day_of_month(currentDate)

                dbAdmin = shelve.open(app.config["DATABASE_FOLDER"] + "/admin", "c")
                try:
                    if 'Cashouts' in dbAdmin:
                        cashoutDict = dbAdmin['Cashouts']
                    else:
                        print("Cashout data in shelve is empty.")
                        cashoutDict = {}
                except:
                    print("Error in retrieving Cashouts from admin.db")

                if request.method == "POST":
                    typeOfCollection = request.form.get("typeOfCollection")
                    if ((accumulatedEarnings + initialEarnings) > 0):

                        # deducting from the teacher object
                        if typeOfCollection == "collectingAll" and lastDayOfMonth:
                            # calculating how much the teacher has earned
                            if currentDate <= zeroCommissionEndDate:
                                commission = 0
                            else:
                                commission = 0.25
                            totalEarned = (initialEarnings + accumulatedEarnings) * (1 - commission)
                            totalEarned = Course.get_two_decimal_pt(totalEarned) # round off and get price in two decimal points

                            # Connecting to PayPal
                            accessToken = get_paypal_access_token()
                            cashoutID = generate_ID_to_length(cashoutDict, 13) # generate a ID with a length of 13 as PayPal payout IDs expire after a month. At the same time, PayPal also utilises a 13 digit code for their IDs.

                            if userKey.get_cashoutPreference() == "Phone":
                                recipientType = "PHONE"     # recipient_type can be 'EMAIL', 'PHONE', 'PAYPAL_ID'
                                receiver = userKey.get_cashoutPhone()
                            elif userKey.get_cashoutPreference() == "Email":
                                recipientType = "EMAIL"
                                receiver = userKey.get_email()

                            payoutSubmit = pyPost('https://api-m.sandbox.paypal.com/v1/payments/payouts',
                                                headers = {
                                                            "Content-Type": "application/json",
                                                            "Authorization": "Bearer " + accessToken
                                                            },
                                                data = json.dumps({"sender_batch_header": {
                                                                                            "sender_batch_id": cashoutID,
                                                                                            "email_subject": "CourseFinity payout of "+totalEarned+" dollars.",
                                                                                            "email_message": "You received a payment. Thanks for using CourseFinity!"
                                                                                            },"items": [{
                                                                                                        "amount": {
                                                                                                                    "value": float(totalEarned),
                                                                                                                    "currency": "USD"
                                                                                                                },
                                                                                                        "note": "If there is any error, please contact us as soon as possible via our Contact Us Page.",
                                                                                                        "sender_item_id": userKey.get_user_id(),
                                                                                                        "recipient_type": recipientType,
                                                                                                        "receiver": receiver
                                                                                                        }]}))

                            response = json.loads(payoutSubmit.text)
                            print(response)

                            paypalError = False
                            try:
                                cashout = Cashout(cashoutID, datetime.now(), totalEarned, userKey.get_cashoutPreference(), receiver, response['batch_header']['payout_batch_id'])
                                cashoutDict[cashoutID] = cashout
                            except:
                                print("Error in PayPal Payout.")
                                paypalError = True


                            """
                            Examples of response.text:

                            Successful
                            {"batch_header":{"payout_batch_id":"KJCS252HBQV9C","batch_status":"PENDING","sender_batch_header":{"sender_batch_id":"2014021802","email_subject":"You have money!","email_message":"You received a payment. Thanks for using our service!"}},"links":[{"href":"https://api.sandbox.paypal.com/v1/payments/payouts/KJCS252HBQV9C","rel":"self","method":"GET","encType":"application/json"}]}

                            Batch Previously Sent
                            {"name":"USER_BUSINESS_ERROR","message":"User business error.","debug_id":"a1e223fd00566","information_link":"https://developer.paypal.com/docs/api/payments.payouts-batch/#errors","details":[{"field":"SENDER_BATCH_ID","location":"body","issue":"Batch with given sender_batch_id already exists","link":[{"href":"https://api.sandbox.paypal.com/v1/payments/payouts/KJCS252HBQV9C","rel":"self","method":"GET","encType":"application/json"}]}],"links":[]}

                            Insufficient Funds [Please don't run out during presentation day.]
                            {"name":"INSUFFICIENT_FUNDS","message":"Sender does not have sufficient funds. Please add funds and retry.","debug_id":"f96c6622de821","information_link":"https://developer.paypal.com/docs/api/payments.payouts-batch/#errors","links":[]}

                            Token Not Found
                            {"error":"invalid_token","error_description":"The token passed in was not found in the system"}

                            Invalid Token
                            {"error":"invalid_token","error_description":"Token signature verification failed"}
                            """

                            if paypalError:
                                flash(Markup("We believe this may be an issue on our side. Please try again later, or inform us via our <a href='/contact_us'>Contact Us</a> page."), "Failed to cash out")
                            else:
                                flash("You have successfully collected your revenue (after commission)!", "Collected Revenue")
                                userKey.set_earnings(0)
                                userKey.set_accumulated_earnings(0)

                            db["Users"] = userDict
                            db.close()
                            return redirect(url_for("teacherCashOut"))

                        elif typeOfCollection == "collectingAccumulated":
                            if currentDate <= zeroCommissionEndDate:
                                commission = 0
                            else:
                                commission = 0.25
                            totalEarned = accumulatedEarnings * (1 - commission)
                            totalEarned = Course.get_two_decimal_pt(totalEarned) # round off and get price in two decimal points

                            # Connecting to PayPal
                            accessToken = get_paypal_access_token()
                            cashoutID = generate_ID_to_length(cashoutDict, 13) # generate a ID with a length of 13 as PayPal payout IDs expire after a month. At the same time, PayPal also utilises a 13 digit code for their IDs.

                            if userKey.get_cashoutPreference() == "Phone":
                                recipientType = "PHONE"     # recipient_type can be 'EMAIL', 'PHONE', 'PAYPAL_ID'
                                receiver = userKey.get_cashoutPhone()
                            elif userKey.get_cashoutPreference() == "Email":
                                recipientType = "EMAIL"
                                receiver = userKey.get_email()

                            payoutSubmit = pyPost('https://api-m.sandbox.paypal.com/v1/payments/payouts',
                                                headers = {
                                                            "Content-Type": "application/json",
                                                            "Authorization": "Bearer " + accessToken
                                                            },
                                                data = json.dumps({"sender_batch_header": {
                                                                                            "sender_batch_id": cashoutID,
                                                                                            "email_subject": "CourseFinity payout of "+totalEarned+" dollars.",
                                                                                            "email_message": "You received a payment. Thanks for using CourseFinity!"
                                                                                            },"items": [{
                                                                                                        "amount": {
                                                                                                                    "value": float(totalEarned),
                                                                                                                    "currency": "USD"
                                                                                                                },
                                                                                                        "note": "If there is any error, please contact us as soon as possible via our Contact Us Page.",
                                                                                                        "sender_item_id": userKey.get_user_id(),
                                                                                                        "recipient_type": recipientType,
                                                                                                        "receiver": receiver
                                                                                                        }]}))

                            response = json.loads(payoutSubmit.text)
                            print(response)

                            paypalError = False
                            try:
                                cashout = Cashout(cashoutID, datetime.now(), totalEarned, userKey.get_cashoutPreference(), receiver, response['batch_header']['payout_batch_id'])
                                cashoutDict[cashoutID] = cashout
                            except:
                                print("Error in PayPal Payout.")
                                paypalError = True

                            if paypalError:
                                flash(Markup("We believe this may be an issue on our side. Please try again later, or inform us via our <a href='/contact_us'>Contact Us</a> page."), "Failed to cash out")
                            else:
                                flash("You have successfully collected your revenue (after commission)!", "Collected Revenue")
                                userKey.set_accumulated_earnings(0)

                            db["Users"] = userDict
                            db.close()
                            return redirect(url_for("teacherCashOut"))
                        else:
                            db.close()
                            print("POST request sent but it is not the last day of the month or post request sent but had tampered values in hidden input.")
                            flash("This could be because it is either not the last day of the month, you have already collected your revenue, or you did not earn any for this month.", "Failed to cash out")
                            return redirect(url_for("teacherCashOut"))
                    else:
                        db.close()
                        print("POST request sent but user have already collected their revenue or user did not earn any this month.")
                        flash("This could be because it is either not the last day of the month, you have already collected your revenue, or you did not earn any for this month.", "Failed to cash out")
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
                        totalEarned = initialEarnings + accumulatedEarnings

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
                        totalEarned = (initialEarnings + accumulatedEarnings) * (1 - 0.25)

                    totalEarnedInt = totalEarned
                    # converting the numbers into strings of 2 decimal place for the earnings
                    initialEarnings = Course.get_two_decimal_pt(initialEarnings)
                    totalEarned = Course.get_two_decimal_pt(totalEarned)
                    accumulatedEarnings = Course.get_two_decimal_pt(accumulatedEarnings)

                    # Get cashout preference info
                    cashoutPreference = userKey.get_cashoutPreference()
                    if cashoutPreference == "Phone":
                        cashoutContact = userKey.get_cashoutPhone()
                        cashoutVerification = userKey.get_phoneVerification()
                    elif cashoutPreference == "Email":
                        cashoutContact = userKey.get_email()
                        cashoutVerification = userKey.get_email_verification()

                    # Get shopping cart len
                    shoppingCartLen = len(userKey.get_shoppingCart())

                    return render_template('users/teacher/teacher_cashout.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, monthYear=monthYear, lastDayOfMonth=lastDayOfMonth, commission=commission, totalEarned=totalEarned, initialEarnings=initialEarnings, accumulatedEarnings=accumulatedEarnings, remainingDays=remainingDays, totalEarnedInt=totalEarnedInt, accumulatedCollect=accumulatedCollect, teacherUID=userSession, cashoutContact=cashoutContact, cashoutVerification=cashoutVerification, cashoutPreference=cashoutPreference)
            else:
                db.close()
                print("User is a student.")
                return redirect(url_for("userProfile"))
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
def search(pageNum):
    checker = ""
    course = ""
    courseDict = {}
    courseTitleList = []
    userDict = {}
    try:
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
        courseDict = db["Courses"]
        userDict = db["Users"]
        db.close()

    except:
        print("Error in obtaining course.db data")
        return redirect(url_for("home"))

    searchInput = str(request.args.get("q"))

    searchURL = "?q=" + searchInput

    courseDictCopy = courseDict.copy()
    for courseID, courseObject in courseDictCopy.items():
        if userDict.get(courseObject.get_userID()).get_status() != "Good":
            courseDict.pop(courseID)

    searchfound = []
    for courseID in courseDict:
        courseTitle = courseDict.get(courseID).get_title()
        courseTitleList.append(courseTitle)

    try:
        matchedCourseTitleList = difflib.get_close_matches(searchInput, courseTitleList, len(courseTitleList), 0.25) # return a list of closest matched search with a length of the whole list as difflib will only return the 3 closest matches by default. I then set the cutoff to 0.80, i.e. must match to a certain percentage else it will be ignored.
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
                courseOwner = userDict[course.get_userID()].get_username()

                rating = course.get_averageRating()

                searchInformation = {"CourseID":course.get_courseID(),
                    "Title":course.get_title(),
                    "Description":course.get_description(),
                    "Thumbnail":course.get_thumbnail(),
                    "Owner": courseOwner,
                    "OwnerID":course.get_userID(),
                    "Rating": rating}

                searchfound.append(searchInformation)

    print(searchfound)
    if bool(searchfound): #If there is something inside the list
        checker = True
    else:
        checker = False

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

            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                purchasedCourses = userKey.get_purchases()
                for searchInformation in searchfound:
                    if searchInformation["CourseID"] in purchasedCourses:
                        searchInformation["Bought"] = True
                    else:
                        searchInformation["Bought"] = False
            else:
                purchasedCourses = ""

            # Get shopping cart len
            if accType != "Admin":
                shoppingCartLen = len(userKey.get_shoppingCart())
            else:
                shoppingCartLen = 0

            return render_template('users/general/search.html', course=course, accType=accType , shoppingCartLen=shoppingCartLen, courseDict=courseDict, matchedCourseTitleList=matchedCourseTitleList,searchInput=searchInput, pageNum=pageNum, previousPage = previousPage, nextPage = nextPage, paginationList = paginationList, maxPages=maxPages, imagesrcPath=imagesrcPath, checker=checker, searchfound=paginatedCourseList, teacherUID=teacherUID,submittedParameters=searchURL)
        else:
            print("Admin/User account is not found or is not active/banned.")
            return render_template('users/general/search.html',course=course, courseDict=courseDict, matchedCourseTitleList=matchedCourseTitleList,searchInput=searchInput, pageNum=pageNum, previousPage = previousPage, nextPage = nextPage, paginationList = paginationList, maxPages=maxPages, checker=checker, searchfound=paginatedCourseList,searchURL=searchURL,submittedParameters=searchURL, accType="Guest")
    else:
        return render_template('users/general/search.html',course=course, courseDict=courseDict, matchedCourseTitleList=matchedCourseTitleList,searchInput=searchInput, pageNum=pageNum, previousPage = previousPage, nextPage = nextPage, paginationList = paginationList, maxPages=maxPages, checker=checker, searchfound=paginatedCourseList,searchURL=searchURL,submittedParameters=searchURL, accType="Guest")

"""End of Search Function by Royston"""

"""Purchase History by Royston"""

@app.route("/purchasehistory/<int:pageNum>")
def purchaseHistory(pageNum):
    if "userSession" in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if "Users" in db and "Courses" in db:
                userDict = db['Users']
                courseDict = db["Courses"]
                db.close()
            else:
                db.close()
                print("User & Course data in shelve is empty.")
                session.clear() # since the file data is empty either due to the admin deleting the shelve files or something else, it will clear any session and redirect the user to the homepage (This is assuming that is impossible for your shelve file to be missing and that something bad has occurred)
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Users from user & course db")
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

            course = ""
            courseID = ""
            courseType = ""
            historyCheck = True
            historyList = []
            reviewlist = []
            # Get purchased courses
            purchasedCourses = userKey.get_purchases()
            print("PurchaseID exists?: ", purchasedCourses)

            if purchasedCourses != {}:
                # Get specific course with course ID
                for courseID in list(purchasedCourses.keys()):
                    print(courseID)

                    # Find the correct course
                    course = courseDict[courseID]
                    courseOwner = userDict[course.get_userID()].get_username()
                    reviewlist = course.get_review()
                    reviewCourse = False
                    for review in reviewlist:
                        user = review.get_userID()
                        if user == userSession:
                            reviewCourse = True

                    courseInformation = {"CourseID":course.get_courseID(),
                                        "Title":course.get_title(),
                                        "Description":course.get_description(),
                                        "Thumbnail":course.get_thumbnail(),
                                        "CourseTypeCheck":course.get_course_type(),
                                        "Price":course.get_price(),
                                        "Owner":courseOwner,
                                        "ReviewChecker":reviewCourse}
                    historyList.append(courseInformation)
                    session["courseIDGrab"] = courseID
                print(historyList)

            else:
                print("Purchase History is Empty")
                historyCheck = False

            maxItemsPerPage = 5 # declare the number of items that can be seen per pages
            courseListLen = len(purchasedCourses) # get the length of the userList
            maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
            pageNum = int(pageNum)
            # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
            if pageNum < 0:
                session["pageNumber"] = 0
                return redirect("/purchasehistory/0")
            elif courseListLen > 0 and pageNum == 0:
                session["pageNumber"] = 1
                return redirect("/purchasehistory/1")
            elif pageNum > maxPages:
                session["pageNumber"] = maxPages
                redirectRoute = "/purchasehistory/" + str(maxPages)
                return redirect(redirectRoute)
            else:
                # pagination algorithm starts here
                courseList = historyList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                pageNumForPagination = pageNum - 1 # minus for the paginate function
                paginatedCourseList = paginate(courseList, pageNumForPagination, maxItemsPerPage)
                purchasedCourses = paginate(historyList[::-1], pageNumForPagination, maxItemsPerPage)

                paginationList = get_pagination_button_list(pageNum, maxPages)

                session["pageNumber"] = pageNum

                previousPage = pageNum - 1
                nextPage = pageNum + 1

                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())

                return render_template('users/loggedin/purchasehistory.html',course=course, shoppingCartLen=shoppingCartLen, courseID=courseID, courseType=courseType,historyList=paginatedCourseList, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, accType=accType, imagesrcPath=imagesrcPath,historyCheck=historyCheck, teacherUID=teacherUID)
        else:
            print("Invalid Session")
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Purchase History by Royston"""

"""Purchase Review by Royston"""

@app.route("/purchasereview/<courseID>", methods=["GET","POST"])
def createPurchaseReview(courseID):
    if "userSession" in session:
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

            pageNum = session.get("pageNumber")

            if "pageNumber" in session:
                pageNum = session["pageNumber"]
            else:
                pageNum = 0

            purchasedCourses = userKey.get_purchases()
            createReview = Forms.CreateReviewText(request.form)
            print("Purchased course exists?: ", purchasedCourses)
            courseID = session.get("courseIDGrab")
            courseDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            print(courseID)

            try:
                courseDict = db["Courses"]
            except:
                print("Error in retrieving review from review.db")
                db.close()
                return redirect(url_for("purchasehistory"))

            if courseID in list(purchasedCourses.keys()):
                redirectURL = "/purchasehistory/" + str(pageNum)
                if request.method == 'POST' and createReview.validate():
                    review = createReview.review.data
                    title = createReview.title.data
                    rating = request.form.get("rate")
                    course = courseDict[courseID]
                    reviewID = course.add_review(userSession, title, review, rating)
                    print("What is the review info?: ",reviewID)

                    db["Courses"] = courseDict

                    session.pop("courseIDGrab", None)
                    print("Review addition was successful", course.get_review())
                    flash("Your review submission was successful. To check your review, visit the course page.", "Review submission successful!")
                    db.close() # remember to close your shelve files!
                    return redirect(redirectURL)
                else:

                    # Get shopping cart len
                    shoppingCartLen = len(userKey.get_shoppingCart())

                    db.close()
                    print("Error in Process")
                    return render_template('users/loggedin/purchasereview.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID, form=createReview, pageNum=pageNum)

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

@app.post("/deletereview/<courseID>")
def deleteReview(courseID):
    if "userSession" in session:
        userSession = session["userSession"]

        userFound, accGoodStatus, accType = validate_session_open_file(userSession)

        if userFound and accGoodStatus:
            # add in your own code here for your C,R,U,D operation and remember to close() it after manipulating the data

            redirectURL = "/purchaseview/" + courseID
            reviewlist = []

            courseDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                courseDict = db["Courses"]
            except:
                print("Unable to open up course shelve")
                db.close()
                return redirect(redirectURL)

            if courseID in courseDict:
                course = courseDict[courseID]

                reviewlist = course.get_review()
                for review in reviewlist:
                    user = review.get_userID()
                    if user == userSession:
                        course.remove_review(review)
                        flash("Your deletion of review has been successful!","Success!")
                        db["Courses"] = courseDict
                        return redirect(redirectURL)

                print("Either the user did not review the course or the course has no reviews.")
                return redirect(redirectURL)
            else:
                print("Course not found.")
                return redirect(redirectURL)
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect("/course/" + courseID)
        else:
            return redirect("/course/" + courseID)

@app.post("/course/deletereview/<courseID>")
def coursePageDeleteReview(courseID):
    if "userSession" in session:
        userSession = session["userSession"]

        userFound, accGoodStatus, accType = validate_session_open_file(userSession)

        if userFound and accGoodStatus:
            # add in your own code here for your C,R,U,D operation and remember to close() it after manipulating the data

            redirectURL = "/course/" + courseID
            reviewlist = []

            courseDict = {}
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                courseDict = db["Courses"]
            except:
                print("Unable to open up course shelve")
                db.close()
                return redirect(redirectURL)

            if courseID in courseDict:
                course = courseDict[courseID]

                reviewlist = course.get_review()
                for review in reviewlist:
                    user = review.get_userID()
                    if user == userSession:
                        course.remove_review(review)
                        flash("Your deletion of review has been successful!","Success!")
                        db["Courses"] = courseDict
                        return redirect(redirectURL)

                print("Either the user did not review the course or the course has no reviews.")
                return redirect(redirectURL)
            else:
                print("Course not found.")
                return redirect(redirectURL)
        else:
            print("User not found or is banned.")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(redirectURL)
        else:
            return redirect(redirectURL)

"""End of Purchase Review by Royston"""

"""Purchase View by Royston"""

@app.route("/purchaseview/<courseID>", methods=["GET", "POST"])
def purchaseView(courseID):
    if "userSession" in session:
        userSession = session["userSession"]

        # Retrieving data from shelve and to write the data into it later
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if "Users" in db and "Courses" in db:
                userDict = db['Users']
                courseDict = db["Courses"]
                db.close()
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

            pageNum = session.get("pageNumber")

            if "pageNumber" in session:
                pageNum = session["pageNumber"]
            else:
                pageNum = 0

            courseList = []
            historyCheck = True
            reviewlist = []
            reviewMatch = ""
            checker = False
            # Get purchased courses
            purchasedCourses = userKey.get_purchases()
            print("PurchaseID exists?: ", purchasedCourses)
            redirectURL = "/purchasehistory/" + str(pageNum)

            if purchasedCourses != {}:
                if courseID in purchasedCourses:

                    date = purchasedCourses[courseID]['Date']
                    time = purchasedCourses[courseID]['Time']
                    order = purchasedCourses[courseID]['PayPalOrderID']
                    account = purchasedCourses[courseID]['PayPalAccountID']


                    # Find the correct course
                    course = courseDict[courseID]

                    reviewlist = course.get_review()
                    for review in reviewlist:
                        checker = False
                        user = review.get_userID()
                        if user == userSession:
                            reviewMatch = review
                            checker = True
                            break

                    courseInformation = {"CourseID":course.get_courseID(),
                                        "Title":course.get_title(),
                                        "Description":course.get_description(),
                                        "Thumbnail":course.get_thumbnail(),
                                        "CourseTypeCheck":course.get_course_type(),
                                        "Price":course.get_price(),
                                        "Owner":course.get_userID(),
                                        "Lesson":course.get_lesson_list(),
                                        "Date": date,
                                        "Time": time,
                                        "OrderID": order,
                                        "PaypalID": account,
                                        "Review": reviewMatch}
                    courseList.append(courseInformation)
                    print(courseList)

                    # Get shopping cart len
                    shoppingCartLen = len(userKey.get_shoppingCart())

                    return render_template('users/loggedin/purchaseview.html',course=course, checker=checker, courseList = courseList, courseID=courseID, accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath,historyCheck = historyCheck, teacherUID = teacherUID, pageNum = pageNum, courseInformation = courseInformation)
                else:
                    print("User has not purchased the course.")
                    return redirect(url_for("home"))
            else:
                print("Invalid Purchase View")
                return redirect(redirectURL)
        else:
            print("Invalid Session")
            return redirect(url_for("home"))

    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home")) # if it make sense to redirect the user to the home page, you can delete the if else statement here and just put return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Purchase View by Royston"""

"""About Us Page by Royston"""

@app.route('/about_us', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
def aboutUs():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())
            else:
                shoppingCartLen = 0

            return render_template('users/general/about_us.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/about_us.html", accType="Guest")
            # return redirect(url_for("insertName"))
    else:
        return render_template("users/general/about_us.html", accType="Guest")

"""End of About Us Page by Royston"""

"""Explore Category by Royston"""

@app.route('/explore/<tag>/<int:pageNum>', methods=["GET","POST"]) # delete the methods if you do not think that any form will send a request to your app route/webpage
def explore(pageNum, tag):
    checker = ""
    readableTagDict = {"Programming": "Development - Programming",
                        "Web_Development": "Development - Web Development",
                        "Game_Development": "Development - Game Development",
                        "Mobile_App_Development": "Development - Mobile App Development",
                        "Software_Development": "Development - Software Development",
                        "Other_Development": "Development - Other Development",
                        "Entrepreneurship": "Business - Entrepreneurship",
                        "Project_Management": "Business - Project Management",
                        "BI_Analytics": "Business - Business Intelligence & Analytics",
                        "Business_Strategy": "Business - Business Strategy",
                        "Other_Business": "Business - Other Business",
                        "3D_Modelling": "Design - 3D Modelling",
                        "Animation": "Design - Animation",
                        "UX_Design": "Design - UX Design",
                        "Design_Tools": "Design - Design Tools",
                        "Other_Design": "Design - Other Design",
                        "Digital_Photography": "Photography/Videography - Digital Photography",
                        "Photography_Tools": "Photography/Videography - Photography Tools",
                        "Video_Production": "Photography/Videography - Video Production",
                        "Video_Design_Tools": "Photography/Videography - Video Design Tools",
                        "Other_Photography_Videography": "Photography/Videography - Other Photography/Videography",
                        "Science": "Academics - Science",
                        "Math": "Academics - Math",
                        "Language": "Academics - Language",
                        "Test_Prep": "Academics - Test Prep",
                        "Other_Academics": "Academics - Other Academics"}


    searchfound = []
    course= ""

    try:
        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
        courseDict = db["Courses"]
        userDict = db["Users"]
        db.close()

    except:
        print("Unable to open up course shelve")
        return redirect(url_for("home"))

    courseDictCopy = courseDict.copy()
    for courseID, courseObject in courseDictCopy.items():
        if userDict.get(courseObject.get_userID()).get_status() != "Good":
            courseDict.pop(courseID)

    if tag in readableTagDict:
        for courseID in courseDict:
            courseObject = courseDict.get(courseID)
            tagCourse = courseObject.get_tag()
            if tagCourse == tag:
                course = courseDict[courseID]
                courseOwner = userDict[course.get_userID()].get_username()

                rating = course.get_averageRating()

                searchInformation = {"CourseID":course.get_courseID(),
                    "Title":course.get_title(),
                    "Description":course.get_description(),
                    "Thumbnail":course.get_thumbnail(),
                    "Owner": courseOwner,
                    "OwnerID":course.get_userID(),
                    "Rating":rating}
                searchfound.append(searchInformation)
            else:
                print("The tags does not match.")
                print(tagCourse)
                print(tag)
    else:
        print("Tag is not inside the course Tag Dictionary.")
        print(tag)
        abort(404)

    print(searchfound)
    if bool(searchfound): #If there is something inside the list
        checker = True
    else:
        checker = False

    noOfCourse = len(searchfound)

    maxItemsPerPage = 5 # declare the number of items that can be seen per pages
    courseListLen = len(searchfound) # get the length of the userList
    maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
    pageNum = int(pageNum)
    # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
    if pageNum < 0:
        return redirect("/explore/" + tag + "/0")
    elif courseListLen > 0 and pageNum == 0:
        return redirect("/explore/" + tag + "/1")
    elif pageNum > maxPages:
        redirectRoute = "/explore/" + tag + "/" + str(maxPages)
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
    
    tagReadable = readableTagDict[tag]

    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())
            else:
                shoppingCartLen = 0
            
            if accType != "Admin":
                purchasedCourses = userKey.get_purchases()
                for searchInformation in searchfound:
                    if searchInformation["CourseID"] in purchasedCourses:
                        searchInformation["Bought"] = True
                    else:
                        searchInformation["Bought"] = False
            else:
                purchasedCourses = ""

            return render_template('users/general/explore.html',tagReadable=tagReadable, course=course,noOfCourse=noOfCourse,tag=tag,checker=checker, searchfound=paginatedCourseList, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            return render_template('users/general/explore.html',tagReadable=tagReadable, course=course,noOfCourse=noOfCourse,tag=tag,checker=checker, searchfound=paginatedCourseList, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, accType="Guest")
    else:
        return render_template('users/general/explore.html',tagReadable=tagReadable, course=course,noOfCourse=noOfCourse,tag=tag,checker=checker, searchfound=paginatedCourseList, maxPages=maxPages, pageNum=pageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, accType="Guest")

"""End of Explore Category by Royston"""

"""View Video Courses by Royston"""

@app.route("/purchaseview/<courseID>/view_video/<lessonID>" , methods=["GET","POST"])
def viewVideo(courseID,lessonID):
    if "userSession" in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)


        if userFound and accGoodStatus:
            # add in your own code here for your C,R,U,D operation and remember to close() it after manipulating the data
            imagesrcPath = retrieve_user_profile_pic(userKey)
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            purchasedCourses = userKey.get_purchases()
            print("PurchaseID exists?: ", purchasedCourses)

            try:
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "r")
                courseDict = db["Courses"]
                db.close()

            except:
                print("Error in obtaining course.db data")
                return redirect(url_for("home"))

            pageNum = session.get("pageNumber")

            if "pageNumber" in session:
                pageNum = session["pageNumber"]
            else:
                pageNum = 0
            
            if purchasedCourses != {}:
                if courseID in purchasedCourses:
                    course = courseDict[courseID]
                    lessonList = course.get_lesson_list()
                    for lessonObject in lessonList:
                        lessonObjectID = lessonObject.get_lessonID()
                        if lessonID == lessonObjectID:
                            video = lessonObject.get_videoPath()
                            print(video)
                            break

            else:
                print("Purchase History is Empty")
                return redirect(url_for("home"))
            
            # Get shopping cart len
            shoppingCartLen = len(userKey.get_shoppingCart())
            
            return render_template('users/loggedin/view_video.html',courseID=courseID, pageNum = pageNum, shoppingCartLen=shoppingCartLen,video = video, accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID)

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

# blocks all user from viewing the video so that they are only allowed to view the video from the purchase view
@app.route("/static/course_videos/<courseID>/<lessonID>")
def blockAccess(courseID, lessonID):
    # courseID is the folder for the course videos and lessonID is technically the file name with its extension, e.g. hello.mp4
    if "userSession" in session:
        userSession = session["userSession"]
        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)
        if userFound and accGoodStatus:
            db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
            try:
                if "Courses" in db and "Users" in db:
                    courseDict = db['Courses']
                    db.close()
                else:
                    db.close()
                    abort(404)
            except:
                db.close()
                print("Error in retrieving Users from user.db")
                abort(404)

            if (courseID in userKey.get_purchases()) or (courseDict.get(courseID).get_userID() == userSession):
                directoryPath = construct_path(app.config["COURSE_VIDEO_FOLDER"], courseID)
                # first argument is the absolute path to the course video directory and the second argument is the filename (e.g. hello.mp4)
                return send_from_directory(directoryPath, lessonID, as_attachment=False) # display instead of telling the browser to download the video
            else:
                abort(403)
        else:
            abort(403)
    else:
      abort(403)

"""End of View Video Courses by Royston"""

"""Add to Cart by Wei Ren"""

@app.post("/add_to_cart/<courseID>")
def addToCart(courseID):
    if "userSession" in session:
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

            # Remember to validate
            try:
                if "Courses" in db:
                    courseDict = db['Courses']
                else:
                    print("user.db has no course entries.")
                    courseDict = {}
            except:
                print("Error in retrieving Course from user.db")

            # Does Course Exist?
            if courseID not in courseDict:
                print("Course ID not in CourseDict")
                abort(404)

            session["Course Title"] = courseDict[courseID].get_title()

            # Is course already in cart?
            if courseID in userKey.get_shoppingCart():
                session["Add To Cart Status"] = "Already in Cart"
                return redirect(url_for('shoppingCart'))

            # Is course already purchased?
            elif courseID in userKey.get_purchases():
                session["Add To Cart Status"] = "Already Purchased"
                return redirect(url_for('shoppingCart'))

            # Is it your own course?
            elif accType == "Teacher":
                if courseID in userKey.get_coursesTeaching():
                    session["Add To Cart Status"] = "Own Course"
                    return redirect(url_for('shoppingCart'))

            userKey.add_to_cart(courseID)

            userDict[userKey.get_user_id()] = userKey
            db["Users"] = userDict

            db.close() # remember to close your shelve files!

            session["Add To Cart Status"] = "Success"
            return redirect(url_for('shoppingCart'))

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

"""End of Add to Cart by Wei Ren"""

"""Shopping Cart by Wei Ren"""

@app.route("/shopping_cart", methods = ["GET","POST"])
def shoppingCart():
    if "userSession" in session:
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

                    orderID = checkoutCompleteForm.checkoutOrderID.data
                    payerID = checkoutCompleteForm.checkoutPayerID.data

                    purchasedCourses = userKey.get_purchases()

                    for courseID in shoppingCart:

                        course = courseDict[courseID]

                        cost = course.get_price()

                        if courseID not in purchasedCourses:
                            purchasedCourses[courseID] = {'Course ID' : courseID, "Date" : date, 'Time' : time, 'Cost' : cost, "PayPalOrderID" : orderID, "PayPalAccountID" : payerID}

                        # Add some earnings to teacher
                        teacher = userDict[course.get_userID()]
                        teacher.set_earnings(teacher.get_earnings() + float(cost))

                        # Increase purchased count
                        course.set_numberPurchased(course.get_numberPurchased() + 1)


                    print("Shopping Cart:", userKey.get_shoppingCart())
                    print("Purchases:", userKey.get_purchases())

                    userKey.set_purchases(purchasedCourses)
                    userKey.set_shoppingCart([])

                    userDict[userKey.get_user_id()] = userKey
                    db['Users'] = userDict
                    db.close()

                    flash("Your purchase is successful. For more info on courses, view your course materials. Good luck and have fun learning!", "Course(s) successfully purchased!")
                    return redirect('/purchasehistory/0')

                elif removeCourseForm.validate():
                    courseID =  removeCourseForm.courseID.data

                    print("Removing course with Course ID:", courseID)      # D for Delete

                    if courseID in shoppingCart:
                        userKey.remove_from_cart(courseID)
                        print(userKey.get_shoppingCart())
                        userDict[userKey.get_user_id] = userKey
                        db["Users"] = userDict
                        db.close()

                    return redirect(url_for('shoppingCart'))

                else:
                    print("Error with form.")
                    return redirect(url_for('home'))

            # Render the page
            else:                                                                               # R for Read
                print("Purchases:", userKey.get_purchases())
                # Initialise lists for jinja2 tags
                courseList = []
                subtotal = 0

                print(shoppingCart)
                print(session)

                # Check if there were courses added
                if "Course Title" in session:
                    courseAddedTitle = session["Course Title"]
                    status = session["Add To Cart Status"]
                    session.pop("Course Title")
                    session.pop("Add To Cart Status")
                else:
                    courseAddedTitle = None
                    status = None

                for courseID in shoppingCart:
                    # Getting course info
                    course = courseDict[courseID]

                    # Getting subtototal
                    subtotal += float(course.get_price())

                    # Getting course owner info
                    courseOwner = userDict[course.get_userID()]

                    courseOwnerID = courseOwner.get_user_id()
                    courseOwnerUsername = courseOwner.get_username()
                    courseOwnerProfile = retrieve_user_profile_pic(courseOwner)

                    # Add additional info to list
                    courseList.append({"courseID" : courseID,
                                       "courseType" : course.get_course_type(),
                                       "courseTitle" : course.get_shortTitle(),
                                       "courseDescription" : ellipsis(course.get_description(), "Custom", 140),
                                       "coursePricePaying" : course.get_price(),
                                       "courseOwnerUsername" : courseOwnerUsername,
                                       "courseOwnerProfile" : courseOwnerProfile,
                                       "courseOwnerLink" : "/teacher_page/" + courseOwnerID,
                                       "courseThumbnail" : course.get_thumbnail()})

                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""

                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())

                db.close() # remember to close your shelve files!
                print(courseAddedTitle)
                return render_template('users/loggedin/shopping_cart.html', status=status, courseAddedTitle=courseAddedTitle, courseList=courseList[::-1],form = removeCourseForm, checkoutForm = checkoutCompleteForm, subtotal = "{:,.2f}".format(subtotal), accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)

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

                    ticketID = generate_6_char_id(ticketDict)

                    ticket = Ticket(ticketID, userKey.get_user_id(), accType, name, email, subject, contactForm.enquiry.data)

                    print(ticket)

                    ticketDict[ticketID] = ticket
                    dbAdmin['Tickets'] = ticketDict

                    try:
                        send_contact_us_email(ticketID, subject, name, email)
                    except:
                        print("Email server is down, please try again later.")

                    dbAdmin.close()

                    flash("Our staff will be with you shortly. Check your email soon!", "Thank you for your Feedback!")

                    return(redirect(url_for("home")))

                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""

                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())

                return render_template('users/general/contact_us.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, form = contactForm, teacherUID=teacherUID)
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

            ticket = Ticket(ticketID, None, "Guest", name, email, subject, contactForm.enquiry.data)

            ticketDict[ticketID] = ticket
            dbAdmin['Tickets'] = ticketDict

            try:
                send_contact_us_email(ticketID, subject, name, email)
            except:
                print("Email server is down, please try again later")

            dbAdmin.close()

            flash("Our staff will be with you shortly. Check your email soon!", "Thank you for your Feedback!")

            return(redirect(url_for("home")))

        else:
            return render_template("users/general/contact_us.html", accType="Guest", form = contactForm)

"""End of Contact Us by Wei Ren"""

"""Support Ticket Management by Wei Ren"""

@app.route("/support_ticket_management/<int:pageNum>", methods = ["GET", "POST"])
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
                if not(ticketSearch.checkedFilters.data == None and ticketSearch.querySearch.data == None):
                    print(ticketSearch.checkedFilters.data)
                    session["Checked Filters"] = json.loads(ticketSearch.checkedFilters.data)
                    print(ticketSearch.querySearch.data)
                    if ticketSearch.querySearch.data == None:
                        session["Query"] = ""
                    else:
                        session["Query"] = ticketSearch.querySearch.data
                    search = True

                # Ticket Toggling
                if ticketAction.ticketAction.data == "Toggle":
                    print("Toggling")
                    print(ticketAction.ticketID.data)
                    ticket = ticketDict[ticketAction.ticketID.data]
                    if ticket.get_status() == "Open":
                        ticket.set_status("Closed")
                    else:
                        ticket.set_status("Open")
                    ticketDict[ticketAction.ticketID.data] = ticket

                    issueTitle = ticket.get_subject()
                    name = ticket.get_name()
                    email = ticket.get_email()

                    try:
                        send_ticket_closed_email(ticketAction.ticketID.data, issueTitle, name, email)
                    except:
                        print("Email server is down, please try again later.")

                    print(ticketDict)

                # Ticket Deleting
                elif ticketAction.ticketAction.data == "Delete":
                    print("Deleting")
                    if ticketAction.ticketID.data in ticketDict:
                        ticketID = ticketAction.ticketID.data
                        ticketDict.pop(ticketID)


            # print(ticketDict)

            # Preparing filtration system
            query = session["Query"].lower()
            filters = ["Open", "Closed", "Guest", "Student", "Teacher", "General", "Account", "Business", "Bugs", "Jobs", "News", "Others"]
            for filter in session["Checked Filters"]:
                if filter in filters:
                    filters.remove(filter)

            # Checking tickets
            for ticket in ticketDict.values():

                # Checking filters
                filtered = False
                for filter in filters:
                    if filtered == True:
                        continue
                    if filter == "Open" or filter == "Closed":
                        if ticket.get_status() == filter:
                            filtered = True
                    elif filter == "Guest" or filter == "Student" or filter == "Teacher":
                        if ticket.get_accType() == filter:
                            filtered = True
                    else:
                        if ticket.get_subject() == filter:
                            filtered = True


                if not filtered and (query in ticket.get_name().lower() or query in ticket.get_email().lower() or query in ticket.get_ticketID().lower()):
                    ticketList.append(ticket)
                    # print(ticket)

            renderedFilters = session['Checked Filters']

            dbAdmin['Tickets'] = ticketDict
            dbAdmin.close() # remember to close your shelve files!

            maxItemsPerPage = 10 # declare the number of items that can be seen per pages
            ticketListLen = len(ticketList) # get the length of the userList
            maxPages = math.ceil(ticketListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number
            # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/0" or negative numbers, "user_management/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/999999"
            if pageNum < 0:
                session["pageNum"] = 0
                return redirect("/support_ticket_management/0")
            elif ticketListLen > 0 and pageNum == 0:
                session["pageNum"] = 1
                return redirect("/support_ticket_management/1")
            elif pageNum > maxPages:
                session["pageNum"] = maxPages
                redirectRoute = "/support_ticket_management/" + str(maxPages)
                return redirect(redirectRoute)
            else:
                # pagination algorithm starts here
                ticketList = ticketList[::-1] # reversing the list to show the newest users in CourseFinity using list slicing
                pageNumForPagination = pageNum - 1 # minus for the paginate function
                paginatedTicketList = paginate(ticketList, pageNumForPagination, maxItemsPerPage)

                session["pageNum"] = pageNum

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

"""Teapot by Wei Ren for fun"""

@app.route("/teapot")
def teapot():
    abort(418)

"""End of Teapot by Wei Ren for fun"""

"""Teacher's Channel Page by Clarence"""

@app.route('/teacher_page/<teacherPageUID>', methods=["GET", "POST"])
def teacherPage(teacherPageUID):
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
    if teacherObject != None:
        teacherUsername = teacherObject.get_username()
        teacherProfile = get_user_profile_pic_only(teacherPageUID)
        teacherCourseList = []
        print("teacher course list is defined")
        for course in courseDict.values():
            if course.get_userID() == teacherPageUID:
                teacherCourseList.append(course)

        teacherCourseLen = len(teacherCourseList)
        if teacherCourseLen >= 3:
            # Get last 3 elements from the list and reverse it such that the latest course will be first
            lastThreeCourseList = teacherCourseList[-3:][::-1]
        else:
            # if there is less than 3 courses, reverse the list to show the latest courses first
            lastThreeCourseList = teacherCourseList[::-1]

        # Popular courses are highest rated courses
        popularCourseList = []
        teacherCourseCopy = teacherCourseList.copy()
        if teacherCourseLen >= 3:
            for i in range(3):
                highestRatedCourse = max(teacherCourseCopy, key=lambda course: course.get_averageRating())
                popularCourseList.append(highestRatedCourse)
                teacherCourseCopy.remove(highestRatedCourse)
        else:
            for i in range(teacherCourseLen):
                highestRatedCourse = max(teacherCourseCopy, key=lambda course: course.get_averageRating())
                popularCourseList.append(highestRatedCourse)
                teacherCourseCopy.remove(highestRatedCourse)

        lastThreeCourseLen = len(lastThreeCourseList)
        popularCourseLen = len(popularCourseList)
        bio = teacherObject.get_bio()

        teacherURLPage = "".join(["/teacher/", teacherPageUID, "/page_1"])

        if "adminSession" in session or "userSession" in session:
        #checks if session is admin or user
            if "adminSession" in session:
                userSession = session["adminSession"]
            else:
                userSession = session["userSession"]

            userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

            if userFound and accGoodStatus:

                if accType != "Admin":
                    # Get shopping cart len
                    shoppingCartLen = len(userKey.get_shoppingCart())
                else:
                    shoppingCartLen = 0
                return render_template('users/general/teacher_page.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherPageUID=teacherPageUID, bio=bio, teacherCourseList=teacherCourseList, lastThreeCourseList=lastThreeCourseList, lastThreeCourseLen=lastThreeCourseLen, popularCourseList=popularCourseList, popularCourseLen=popularCourseLen, teacherUsername=teacherUsername, teacherProfile=teacherProfile, teacherCourseLen=teacherCourseLen, teacherUID=teacherPageUID)

            else:
                print("Admin/User account is not found or is not active/banned.")
                session.clear()
                return render_template("users/general/teacher_page.html", accType="Guest", teacherPageUID=teacherPageUID, bio=bio, teacherCourseList=teacherCourseList, lastThreeCourseList=lastThreeCourseList, lastThreeCourseLen=lastThreeCourseLen, popularCourseList=popularCourseList, popularCourseLen=popularCourseLen, teacherUsername=teacherUsername, teacherProfile=teacherProfile,teacherCourseLen=teacherCourseLen, teacherUID=teacherPageUID)
        else:
            return render_template("users/general/teacher_page.html", accType="Guest", teacherPageUID=teacherPageUID, bio=bio, teacherCourseList=teacherCourseList, lastThreeCourseList=lastThreeCourseList, lastThreeCourseLen=lastThreeCourseLen, popularCourseList=popularCourseList, popularCourseLen=popularCourseLen, teacherUsername=teacherUsername, teacherProfile=teacherProfile, teacherCourseLen=teacherCourseLen, teacherUID=teacherPageUID)
    else:
        print("No such teacher exists...")
        abort(404)

"""End of Teacher's Channel Page by Clarence"""

"""Course Content Management by Clarence"""

@app.route('/channel_content/<teacherUID>/<int:pageNum>') # delete the methods if you do not think that any form will send a request to your app route/webpage
def channelContent(teacherUID, pageNum):
    if "userSession" in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(userSession)

        if userFound and accGoodStatus:
            # add in your code below
            imagesrcPath = retrieve_user_profile_pic(userKey)
            if accType == "Teacher":
                db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
                try:
                    if "Courses" in db and "Users" in db:
                        courseDict = db['Courses']
                        userDict = db["Users"]
                    else:
                        db.close()
                        return redirect(url_for("home"))

                except:
                    db.close()
                    print("Error in retrieving Users from user.db")
                    return redirect(url_for("home"))

                userKey = userDict.get(userSession)

                courseIDList = userKey.get_coursesTeaching()
                courseObjectList = []
                for courseID in courseIDList:
                    courseObject = courseDict.get(courseID)
                    if courseObject != None:
                        courseObjectList.append(courseDict.get(courseID))
                    else:
                        # if course has been deleted
                        userKey.remove_courseTeaching(courseID)
                
                # saves the dictionary if there was any course ID not existing in the original courseDictionary 
                db["Users"] = userDict
                db.close()
                
                maxItemsPerPage = 10 # declare the number of items that can be seen per pages
                courseObjectListLen = len(courseObjectList) # get the length of the userList
                maxPages = math.ceil(courseObjectListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number

                # redirecting for handling different situation where if the user manually keys in the url and put "/user_management/page/0" or negative numbers, "user_management/page/-111" and where the user puts a number more than the max number of pages available, e.g. "/user_management/page/999999"
                if pageNum < 0:
                    return redirect("/channel_content/" + teacherUID + "/0")
                elif courseObjectListLen > 0 and pageNum == 0:
                    return redirect("/channel_content/" + teacherUID + "/1")
                elif pageNum > maxPages:
                    redirectRoute = "/channel_content/" + teacherUID + "/" + str(maxPages)
                    return redirect(redirectRoute)
                else:
                    # pagination algorithm starts here
                    courseObjectList = courseObjectList[::-1] # reverses the list such that the latest course is shown at the top
                    pageNumForPagination = pageNum - 1 # minus for the paginate function
                    paginatedCourseList = paginate(courseObjectList, pageNumForPagination, maxItemsPerPage)
                    paginationList = get_pagination_button_list(pageNum, maxPages)


                    previousPage = pageNum - 1
                    nextPage = pageNum + 1

                    shoppingCartLen = len(userKey.get_shoppingCart())

                    return render_template('users/teacher/channel_content.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=userSession, courseObjectList=paginatedCourseList, shoppingCartLen=shoppingCartLen, paginationList=paginationList, previousPage=previousPage, nextPage=nextPage, maxPages=maxPages)
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
            # determine if it make sense to redirect the user to the home page or the login page
            return redirect(url_for("home"))
            # return redirect(url_for("userLogin"))

"""End of Course Management app.route by Clarence"""

"""Teacher's All Courses Page by Clarence"""

@app.route('/teacher/<teacherPageUID>/page_<int:coursePageNum>')
def teacherCourses(teacherPageUID, coursePageNum):
    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
    try:
        if "Courses" in db and "Users" in db:
            courseDict = db['Courses']
            userDict = db['Users']
            db.close()
        else:
            db.close()
            abort(404)
    except:
        db.close()
        print("Error in retrieving Users from user.db")
        abort(404)

    teacherObject = userDict.get(teacherPageUID)
    
    if teacherObject == None:  # if the teacherPageUID does not exist in userDict
        abort(404)

    teacherCourseList = teacherObject.get_coursesTeaching() # list of Course IDs
    
    courseList = []
    for courseID in teacherCourseList:
        courseList.append(courseDict.get(courseID))

    courseList = courseList[::-1] # reverses the list so that the latest one will show first
    courseListLen =  len(courseList)
    print(courseListLen)

    # paginate the courseList
    maxItemsPerPage = 15 # declare the number of items that can be seen per pages
    maxPages = math.ceil(courseListLen/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number

    # redirecting for handling different situation
    if coursePageNum < 0:
        return redirect("/teacher/" + teacherPageUID + "/page_0")
    elif coursePageNum > 0 and courseListLen == 0:
        return redirect("/teacher/" + teacherPageUID + "/page_1")
    elif coursePageNum > maxPages:
        return redirect("/teacher/" + teacherPageUID + "/page_" + str(maxPages))
    else:
        pageNumForPagination = coursePageNum - 1 # minus for the paginate function
        paginationCourseList = paginate(courseList, pageNumForPagination, maxItemsPerPage)
        paginationList = get_pagination_button_list(coursePageNum, maxPages)

        previousPage = coursePageNum - 1
        nextPage = coursePageNum + 1

    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())
            else:
                shoppingCartLen = 0

            return render_template('users/general/teacher_courses.html', accType=accType, imagesrcPath=imagesrcPath, teacherUID=teacherUID, shoppingCartLen=shoppingCartLen, courseList=paginationCourseList, courseListCount=courseListLen, maxPages=maxPages, pageNum=coursePageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, teacherPageUID=teacherPageUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/teacher_courses.html", accType="Guest", courseList=paginationCourseList, courseListCount=courseListLen, maxPages=maxPages, pageNum=coursePageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, teacherPageUID=teacherPageUID)
            # return redirect(url_for("insertName"))
    else:
        return render_template("users/general/teacher_courses.html", accType="Guest", courseList=paginationCourseList, courseListCount=courseListLen, maxPages=maxPages, pageNum=coursePageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage, teacherPageUID=teacherPageUID)


"""End of Teacher's All Courses Page by Clarence"""

"""Course Creation by Clarence"""

@app.route("/create_course/<teacherUID>", methods=["GET", "POST"])
def courseUpload(teacherUID):
    if "userSession" in session:
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
                if request.method == "POST":
                    courseID = generate_course_ID(courseDict)

                    courseTitleInput = sanitise(request.form.get("courseTitle"))
                    courseDescriptionInput = sanitise(request.form.get("courseDescription"))
                    courseTagInput = sanitise(request.form.get("courseTag"))
                    courseTypeInput = request.form.get("courseType")
                    coursePriceInput = sanitise(request.form.get("coursePrice"))
                    
                    if "courseThumbnail" not in request.files:
                        print("No file sent.")
                        return redirect(url_for("courseUpload", teacherUID=teacherUID))

                    file = request.files.get("courseThumbnail")

                    extensionType = get_extension(file.filename)
                    if extensionType != False:
                        # renaming the file name of the submitted image data payload
                        file.filename = courseID + extensionType
                        filename = file.filename
                    else:
                        filename = "invalid"

                    # getting the uploaded file size value from the cookie made in the javascript when uploading the user profile image
                    uploadedFileSize = request.cookies.get("filesize")
                    print("Uploaded file size:", uploadedFileSize, "bytes")


                    if file and allowed_image_file(filename):
                        # will only accept .png, .jpg, .jpeg
                        print("File extension accepted and is within size limit.")

                        # to construct a file path for userID.extension (e.g. 0.jpg) for renaming the file

                        userImageFileName = file.filename
                        newFilePath = construct_path(app.config["THUMBNAIL_UPLOAD_PATH"], userImageFileName)
                        file.save(newFilePath)

                        # resizing, compressing, and converting the thumbnail image to webp
                        imageResized, webpFilePath = resize_image(newFilePath, (1920, 1080))

                        if imageResized:
                            # if file was successfully resized, it means the image is a valid image
                            relativeWebpFilePath = "".join(["/", app.config["THUMBNAIL_UPLOAD_PATH"], "/", webpFilePath.name])
                            course = Course.Course(courseID, courseTypeInput, coursePriceInput ,courseTagInput ,courseTitleInput, courseDescriptionInput, relativeWebpFilePath, teacherUID)

                            userKey.set_courseTeaching(courseID)
                            db["Users"] = userDict

                            courseDict[courseID] = course
                            db["Courses"] = courseDict
                            print("Course created successfully.")
                            db.close()
                            print("Course details have been created.")
                            flash("Your course has been created! You can now add lessons to the course.", "Course Created")

                            return redirect("/channel_content/" + teacherUID + "/1")
                        else:
                            db.close()
                            flash("Image file is corrupted", "Corrupted File")
                            webpFilePath.unlink(missing_ok=True)
                            return redirect(url_for("courseUpload", teacherUID=teacherUID))
                    else:
                        db.close()
                        flash(Markup("Sorry! Only png, jpg, jpeg are only supported currently!<br>Please upload a supported image file!<br>Thank you!"), "File Extension Not Accepted")
                        return redirect(url_for("courseUpload", teacherUID=teacherUID))
                else:
                    db.close()
                    imagesrcPath = retrieve_user_profile_pic(userKey)

                    # Get shopping cart len
                    shoppingCartLen = len(userKey.get_shoppingCart())

                    db.close()  # remember to close your shelve files!
                    return render_template('users/teacher/create_course.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=userSession)
            else:
                print("User is not a teacher!")
                db.close()
                return redirect(url_for("userProfile"))
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
            return redirect(url_for("userLogin"))

"""Course Creation by Clarence"""

"""Lesson Creation by Clarence"""

@app.route("/course/<courseID>/edit/<lessonID>", methods=["GET", "POST"])
def editLessonVideo(courseID, lessonID):
    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
    try:
        if "Courses" in db:
            courseDict = db['Courses']
        else:
            db.close()
            return redirect(url_for("home"))
    except:
        db.close()
        print("Error in retrieving Users from user.db")
        return redirect(url_for("home"))

    courseObject = courseDict.get(courseID)
    if courseObject == None:  # if courseID does not exist in courseDict
        db.close()
        abort(404)

    lessonList = courseObject.get_lesson_list()
    lessonFound = False
    for lesson in lessonList:
        if lesson.get_lessonID() == lessonID:
            lessonObject = lesson
            # lessonIndex = lessonList.index(lesson) # if the object doesn't reflect the changes
            lessonFound = True
            break
    
    if lessonFound != True:
        db.close()
        abort(404)

    if "userSession" in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = validate_session_get_userKey_open_file(
            userSession)
        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            if accType == "Teacher":
                if request.method == "POST":

                    videoTitleInput = sanitise(request.form.get("videoTitle"))
                    videoDescriptionInput = sanitise(
                        request.form.get("videoDescription"))

                    if "videoThumbnail" not in request.files:
                        # if user did not upload a thumbnail
                        print("No file sent.")
                        lessonObject.set_title(videoTitleInput)
                        lessonObject.set_description(videoDescriptionInput)

                        db["Courses"] = courseDict
                        print("Video Lesson created successfully.")
                        db.close()
                        flash("Your Video lesson has been edited!", "Video Lesson Edited")
                        return redirect("/teacher/" + userSession + "/page_1")
                    else:
                        # if the user has uploaded a thumbnail for the course details to be edited
                        file = request.files.get("videoThumbnail")

                        extensionType = get_extension(file.filename)
                        if extensionType != False:
                            # renaming the file name of the submitted image data payload
                            file.filename = lessonID + extensionType
                            filename = file.filename
                        else:
                            filename = "invalid"

                        if file and allowed_image_file(filename):
                            # will only accept .png, .jpg, .jpeg
                            print("File extension accepted and is within size limit.")

                            # to construct a file path for userID.extension (e.g. 0.jpg) for renaming the file

                            userImageFileName = file.filename
                            newFilePath = construct_path(
                                app.config["THUMBNAIL_UPLOAD_PATH"], userImageFileName)
                            file.save(newFilePath)

                            # resizing, compressing, and converting the thumbnail image to webp
                            imageResized, webpFilePath = resize_image(
                                newFilePath, (1920, 1080))

                            if imageResized:
                                # if file was successfully resized, it means the image is a valid image
                                relativeWebpFilePath = "".join(["/", app.config["THUMBNAIL_UPLOAD_PATH"], "/", webpFilePath.name])

                                lessonObject.set_title(videoTitleInput)
                                lessonObject.set_description(videoDescriptionInput)
                                lessonObject.set_thumbnail(relativeWebpFilePath)

                                db["Courses"] = courseDict
                                print("Video Lesson created successfully.")
                                db.close()
                                flash("Your Video lesson has been edited!", "Video Lesson Edited")
                                return redirect("/course/" + courseID)
                            else:
                                db.close()
                                flash("Image file is corrupted", "Corrupted File")
                                webpFilePath.unlink(missing_ok=True)
                                return redirect("/course/" + courseID + "/edit/" + lessonID)
                        else:
                            db.close()
                            flash(Markup("Sorry! Only png, jpg, jpeg are only supported currently!<br>Please upload a supported image file!<br>Thank you!"),
                                "File Extension Not Accepted")
                            return redirect("/course/" + courseID + "/edit/" + lessonID)
                else:
                    db.close()
                    imagesrcPath = retrieve_user_profile_pic(userKey)
                    teacherUID = userSession

                    # Get shopping cart len
                    shoppingCartLen = len(userKey.get_shoppingCart())
                    return render_template('users/teacher/upload_lesson.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
            else:
                db.close()
                print("User is not a teacher!")
                return redirect(url_for("userProfile"))
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        db.close()
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

"""End of Lesson Creation by Clarence"""

"""Video Upload by Clarence"""

@app.post('/upload/<courseID>')
def upload(courseID):
    if "userSession" in session:

        userSession = session["userSession"]

        db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
        try:
            if "Courses" in db and "Users" in db:
                courseDict = db['Courses']
                userDict = db['Users']
            else:
                db.close()
                return redirect(url_for("home"))
        except:
            db.close()
            print("Error in retrieving Lessons from user.db")
            return redirect(url_for("home"))

        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)

        if userFound and accGoodStatus and accType == "Teacher":

            courseObject = courseDict.get(courseID)
            if courseObject == None: # if courseID does not exist in courseDict
                return make_response("Course noot found!", 404)

            file = request.files.get("lessonVideo")
            
            extensionType = get_extension(file.filename)
            if extensionType != False:
                # using secure_filename to get a safe version of the filename to prevent malicious attacks
                filename = secure_filename(file.filename)
            else:
                filename = "invalid"
                return make_response("Not a valid file!", 500)

            # create the folder if it doesn't exist
            directoryPath = construct_path(app.config["COURSE_VIDEO_FOLDER"], courseID)
            directoryPath.mkdir(parents=True, exist_ok=True)

            savePath = directoryPath.joinpath(filename)
            print(savePath)
            
            currentChunk = int(request.form['dzchunkindex'])
            
            # If the file already exists it's ok if we are appending to it,
            # but not if it's new file that would overwrite the existing one
            if savePath.is_file() and currentChunk == 0:
                # if the user has uploaded another video with the same filename of an existing video
                return make_response("Video file with the same name already exists! Please rename to a different filename.", 500)

            try:
                with open(savePath, 'ab') as f:
                    f.seek(int(request.form['dzchunkbyteoffset']))
                    f.write(file.stream.read())
            except OSError:
                db.close()
                return make_response(("Not sure why,"
                                    " but we couldn't write the file to web server", 500))

            totalChunks = int(request.form['dztotalchunkcount'])

            if currentChunk + 1 == totalChunks:
                # This was the last chunk, the file should be complete and the size we expect
                if savePath.stat().st_size != int(request.form['dztotalfilesize']):
                    db.close()
                    return make_response(('The uploaded video is corrupted, please try again!', 500))
                else:
                    relativePath = "".join(["/", app.config["COURSE_VIDEO_FOLDER"], f"/{courseID}/", filename])
                    courseObject.add_video_lesson(filename, "", "/static/images/courses/placeholder.webp", relativePath) # initialise the title to the filename, empty description, placeholder thumbnail, and relative path of the video
                    
                    lessonObject = courseObject.get_lesson_list()[-1] # get the latest lesson object
                    userKey.set_courseTeaching(lessonObject.get_lessonID())

                    db["Courses"] = courseDict
                    db['Users'] = userDict
                    db.close()

                    flash("Video successfully uploaded, you can now edit the lesson details!", "Video Uploaded!")
                    return make_response("File " + filename + " has been uploaded successfully", 200)
            else:
                db.close()
                return make_response("Chunk " + str(currentChunk + 1) + " of " + str(totalChunks) + " for file " + file.filename + " complete", 200)
        else:
            db.close()
            print("User is banned/not found or is not a teacher!")
            return redirect(url_for("home"))
    else:
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

"""End of Video Upload by Clarence"""

"""Zoom Creation app.route(") by Clarence"""

@app.route("/course/<courseID>/upload_zoom", methods=["GET", "POST"])
def uploadZoom(courseID):
    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
    try:
        if "Courses" in db and "Users" in db:
            courseDict = db['Courses']
            userDict = db['Users']
        else:
            db.close()
            return redirect(url_for("home"))
    except:
        db.close()
        print("Error in retrieving Users from user.db")
        return redirect(url_for("home"))

    courseObject = courseDict.get(courseID)
    redirectURL = "course/" + courseID + "/upload_zoom"
    if courseObject == None:  # if courseID does not exist in courseDict
        abort(404)

    if "userSession" in session:
        userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType = get_key_and_validate(userSession, userDict)
        if userFound and accGoodStatus:
            # insert your C,R,U,D operation here to deal with the user shelve data files
            if accType == "Teacher":
                if request.method == "POST":

                    zoomTitleInput = sanitise(request.form.get("zoomTitle"))
                    zoomDescriptionInput = sanitise(request.form.get("zoomDescription"))
                    zoomTimeInput = request.form.get("zoomTime")
                    zoomDayInput = request.form.get("zoomDay")
                    zoomLinkInput = sanitise(request.form.get("zoomLink"))
                    zoomPasswordInput = sanitise(request.form.get("zoomPassword"))

                    if "zoomThumbnail" not in request.files:
                        print("No file sent.")
                        return redirect(redirectURL)

                    file = request.files.get("zoomThumbnail")

                    extensionType = get_extension(file.filename)
                    if extensionType != False:
                        # renaming the file name of the submitted image data payload
                        file.filename = generate_ID_to_length_no_dict(16) + extensionType
                        filename = file.filename
                    else:
                        filename = "invalid"

                    if file and allowed_image_file(filename):
                        # will only accept .png, .jpg, .jpeg
                        print("File extension accepted and is within size limit.")

                        # to construct a file path for userID.extension (e.g. 0.jpg) for renaming the file

                        newFilePath = construct_path(
                            app.config["THUMBNAIL_UPLOAD_PATH"], filename)
                        file.save(newFilePath)

                        # resizing, compressing, and converting the thumbnail image to webp
                        imageResized, webpFilePath = resize_image(
                            newFilePath, (1920, 1080))

                        if imageResized:
                            # if file was successfully resized, it means the image is a valid image
                            relativeWebpFilePath = "".join(
                                ["/", app.config["THUMBNAIL_UPLOAD_PATH"], "/", webpFilePath.name])

                            courseObject.add_zoom_lessons(zoomTitleInput, zoomDescriptionInput, relativeWebpFilePath, zoomLinkInput, zoomPasswordInput, zoomTimeInput, zoomDayInput)

                            db["Courses"] = courseDict
                            db.close()
                            print("Zoom Lesson created successfully.")
                            flash("Your zoom lesson has been created!", "Zoom Lesson Created")
                            return redirect("/channel_content/" + userSession + "/1")
                        else:
                            db.close()
                            flash("Image file is corrupted", "Corrupted File")
                            webpFilePath.unlink(missing_ok=True)
                            return redirect(redirectURL)
                    else:
                        db.close()
                        flash(Markup("Sorry! Only png, jpg, jpeg are only supported currently!<br>Please upload a supported image file!<br>Thank you!"),
                            "File Extension Not Accepted")
                        return redirect(redirectURL)
                else:
                    db.close()
                    imagesrcPath = retrieve_user_profile_pic(userKey)
                    teacherUID = userSession

                    # Get shopping cart len
                    shoppingCartLen = len(userKey.get_shoppingCart())
                    return render_template('users/teacher/upload_zoom.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
            else:
                db.close()
                print("User is not a teacher!")
                return redirect(url_for("userProfile"))
        else:
            db.close()
            print("User not found or is banned")
            # if user is not found/banned for some reason, it will delete any session and redirect the user to the homepage
            session.clear()
            return redirect(url_for("home"))
    else:
        db.close()
        if "adminSession" in session:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("userLogin"))

"""End of Zoom Creation app.route by Clarence"""

"""Course Page and its review page by Jason"""

@app.route('/course/<courseID>')
def coursePage(courseID):
    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
    try:
        if "Courses" in db and "Users" in db:
            courseDict = db['Courses']
            userDict = db['Users']
        else:
            db.close()
            abort(404)
    except:
        db.close()
        print("Error in retrieving Users from user.db")
        abort(404)

    courseObject = courseDict.get(courseID)

    if courseObject == None: # if courseID does not exist in courseDict
        abort(404)

    courseTeacherUsername = userDict.get(courseObject.get_userID()).get_username()

    lessons = courseObject.get_lesson_list() # get a list of lesson objects
    lessonsCount = len(lessons)

    reviews = courseObject.get_review() # get a list of review objects

    reviewsCount = len(reviews)
    if reviewsCount > 3:
        reviews = reviews[-3:][::-1] # get latest five reviews and reverses it such that the latest review is first
    else:
        reviews = reviews[::-1] # get latest reviews

    # Retrieving the user's uername and profile image url for the reviews
    reviewsDict = {}
    for review in reviews:
        userID = review.get_userID()
        userObject = userDict.get(userID)
        if userObject != None:
            userProfile = retrieve_user_profile_pic(userObject)
            reviewsDict[review] = [userObject.get_username(), userProfile]
        else:
            # if user account is deleted from the database
            courseObject.remove_review(review)

    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey_userDict(userSession, userDict)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                print("User is not an admin.")
                if courseID in userKey.get_purchases():
                    userPurchased = True
                else:
                    userPurchased = False
                # if user is not admin, increase the number of tag views for the course's tag and increase the course's number of views
                userKey.change_no_of_view(courseObject.get_tag())
                courseObject.increase_view()
                db["Users"] = userDict

                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())

            else:
                userPurchased = False
                shoppingCartLen = 0

            db["Courses"] = courseDict
            db.close()

            return render_template('users/general/course_page.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID, course=courseObject, userPurchased=userPurchased, lessons=lessons, lessonsCount=lessonsCount, reviews=reviewsDict, reviewsCount=reviewsCount, courseTeacherUsername=courseTeacherUsername)
        else:
            db.close()
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return redirect("/course/" + courseID)
    else:
        res = make_response(render_template("users/general/course_page.html", accType="Guest", course=courseObject, userPurchased=False, lessons=lessons, lessonsCount=lessonsCount, reviews=reviewsDict, reviewsCount=reviewsCount, courseTeacherUsername=courseTeacherUsername))

        courseTag = courseObject.get_tag()
        if not request.cookies.get("guestSeenTags"):
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
            if courseTag in originalCourseTagDict:
                originalCourseTagDict[courseTag] += 1
            else:
                print("Tag does not exist.")

            res.set_cookie(
                "guestSeenTags",
                value=b64encode(json.dumps(originalCourseTagDict).encode("utf-8")),
                expires=datetime.now() + timedelta(days=90)
            )
        else:
            # if user have an existing cookie with the name guestSeenTags
            try:
                userTagDict = json.loads(b64decode(request.cookies.get("guestSeenTags")))
                if courseTag in userTagDict:
                    userTagDict[courseTag] += 1
                    res.set_cookie(
                        "guestSeenTags",
                        value=b64encode(json.dumps(userTagDict).encode("utf-8")),
                        expires=datetime.now() + timedelta(days=90)
                    )
                else:
                    print("Tag does not exist.")
            except:
                print("Error with editing guest's cookie.")
                # if the guest user had tampered with the cookie value
                tagDict = {"Programming": 0,
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
                if courseTag in tagDict:
                    tagDict[courseTag] += 1
                else:
                    print("Tag does not exist.")
                res.set_cookie(
                    "guestSeenTags",
                    value=b64encode(json.dumps(tagDict).encode("utf-8")),
                    expires=datetime.now() + timedelta(days=90)
            )

        courseObject.increase_view()
        db["Courses"] = courseDict
        db.close()

        return res

@app.route('/course/<courseID>/reviews/page_<int:reviewPageNum>')
def courseReviews(courseID, reviewPageNum):
    db = shelve.open(app.config["DATABASE_FOLDER"] + "\\user", "c")
    try:
        if "Courses" in db and "Users" in db:
            courseDict = db['Courses']
            userDict = db['Users']
        else:
            db.close()
            return redirect(url_for("home"))
    except:
        db.close()
        print("Error in retrieving Users from user.db")
        return redirect(url_for("home"))

    courseObject = courseDict.get(courseID)

    if courseObject == None: # if courseID does not exist in courseDict
        abort(404)

    courseTeacherUsername = userDict.get(courseObject.get_userID()).get_username()

    reviews = courseObject.get_review() # get a list of review objects

    reviewsCount = len(reviews)
    if reviewsCount > 3:
        reviews = reviews[::-1] # get latest reviews
        reviewsDict = {}
        for review in reviews:
            userID = review.get_userID()
            userObject = userDict.get(userID)
            if userObject != None:
                userProfile = retrieve_user_profile_pic(userObject)
                reviewsDict[review] = [userObject.get_username(), userProfile]
            else:
                # if user account is deleted from the database
                courseObject.remove_review(review)

        db["Courses"] = courseDict
        db.close()

        maxItemsPerPage = 10 # declare the number of items that can be seen per pages
        maxPages = math.ceil(reviewsCount/maxItemsPerPage) # calculate the maximum number of pages and round up to the nearest whole number

        # redirecting for handling different situation
        if reviewPageNum < 0:
            return redirect("/courseReviews/" + courseID + "/reviews/page_0")
        elif reviewsCount > 0 and reviewPageNum == 0:
            return redirect("/courseReviews/" + courseID + "/reviews/page_1")
        elif reviewPageNum > maxPages:
            return redirect("/courseReviews/" + courseID + "/reviews/page_" + str(maxPages))
        else:
            # reversing the dictionary keys to show the latest review in CourseFinity using list slicing
            reviewKeyList = []
            for reviews in reversed(reviewsDict):
                reviewKeyList.append(reviews)

            pageNumForPagination = reviewPageNum - 1 # minus for the paginate function
            paginatedReviewKeyList = paginate(reviewKeyList, pageNumForPagination, maxItemsPerPage)
            paginationList = get_pagination_button_list(reviewPageNum, maxPages)

            paginatedReviewDict = {}
            for key in paginatedReviewKeyList:
                paginatedReviewDict[key] = reviewsDict.get(key)

            previousPage = reviewPageNum - 1
            nextPage = reviewPageNum + 1

        if "adminSession" in session or "userSession" in session:
            if "adminSession" in session:
                userSession = session["adminSession"]
            else:
                userSession = session["userSession"]

            userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

            if userFound and accGoodStatus:
                if courseID in userKey.get_purchases():
                    userPurchased = True
                else:
                    userPurchased = False

                # for showing the user's own review on the page
                userReviewed = False
                userReview = {}
                for review in reviewsDict.keys():
                    if review.get_userID() == userSession:
                        userReviewed = True
                        userReview[review] = reviewsDict.get(review)
                        if review in paginatedReviewDict:
                            del paginatedReviewDict[review]
                        break

                if accType == "Teacher":
                    teacherUID = userSession
                else:
                    teacherUID = ""

                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())

                return render_template('users/general/course_page_reviews.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID, course=courseObject, reviews=paginatedReviewDict, reviewsCount=reviewsCount, courseTeacherUsername=courseTeacherUsername, userReviewed=userReviewed, userReview=userReview, userPurchased=userPurchased, count=reviewsCount, maxPages=maxPages, pageNum=reviewPageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage)
            else:
                print("Admin/User account is not found or is not active/banned.")
                session.clear()
                return redirect("/courseReviews/" + courseID + "/reviews/page_" + str(reviewPageNum))
        else:
            return render_template("users/general/course_page_reviews.html", accType="Guest", course=courseObject, userReviewed=False, userPurchased=False, reviews=paginatedReviewDict, reviewsCount=reviewsCount, courseTeacherUsername=courseTeacherUsername, count=reviewsCount, maxPages=maxPages, pageNum=reviewPageNum, paginationList=paginationList, nextPage=nextPage, previousPage=previousPage)
    else:
        db.close()
        return redirect("/course/" + courseID)

"""End of Course Page and its review page by Jason"""

"""General Pages"""

@app.route('/cookie_policy')
def cookiePolicy():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())
            else:
                shoppingCartLen = 0

            return render_template('users/general/cookie_policy.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/cookie_policy.html", accType="Guest")
    else:
        return render_template("users/general/cookie_policy.html", accType="Guest")

@app.route('/terms_and_conditions')
def termsAndConditions():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())
            else:
                shoppingCartLen = 0

            return render_template('users/general/terms_and_conditions.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/terms_and_conditions.html", accType="Guest")
    else:
        return render_template("users/general/terms_and_conditions.html", accType="Guest")

@app.route('/privacy_policy')
def privacyPolicy():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())
            else:
                shoppingCartLen = 0

            return render_template('users/general/privacy_policy.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/privacy_policy.html", accType="Guest")
    else:
        return render_template("users/general/privacy_policy.html", accType="Guest")

@app.route("/faq")
def faq():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)


        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())
            else:
                shoppingCartLen = 0

            return render_template('users/general/faq.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/faq.html", accType="Guest")
    else:
        return render_template("users/general/faq.html", accType="Guest")

@app.route("/teacher_handbook")
def teacherHandbook():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())
            else:
                shoppingCartLen = 0

            return render_template('users/general/teacher_handbook.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/teacher_handbook.html", accType="Guest")
    else:
        return render_template("users/general/teacher_handbook.html", accType="Guest")

@app.route('/community_guidelines')
def communityGuidelines():
    if "adminSession" in session or "userSession" in session:
        if "adminSession" in session:
            userSession = session["adminSession"]
        else:
            userSession = session["userSession"]

        userKey, userFound, accGoodStatus, accType, imagesrcPath = general_page_open_file_with_userKey(userSession)

        if userFound and accGoodStatus:
            if accType == "Teacher":
                teacherUID = userSession
            else:
                teacherUID = ""

            if accType != "Admin":
                # Get shopping cart len
                shoppingCartLen = len(userKey.get_shoppingCart())
            else:
                shoppingCartLen = 0

            return render_template('users/general/community_guidelines.html', accType=accType, shoppingCartLen=shoppingCartLen, imagesrcPath=imagesrcPath, teacherUID=teacherUID)
        else:
            print("Admin/User account is not found or is not active/banned.")
            session.clear()
            return render_template("users/general/community_guidelines.html", accType="Guest")
    else:
        return render_template("users/general/community_guidelines.html", accType="Guest")

"""End of Genral Pages"""

"""Custom Error Pages by Jason"""

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

# I'm a Teapot
@app.errorhandler(418)
def error418(e):
    return render_template("errors/418.html"), 418

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

"""End of Custom Error Pages by Jason"""

if __name__ == '__main__':
    scheduler.configure(timezone="Asia/Singapore") # configure timezone to always follow Singapore's timezone
    # adding a scheduled job to save data for the graph everyday at 11.59 p.m. below
    scheduler.add_job(saveNoOfUserPerDay, trigger="cron", hour="23", minute="59", second="0", id="collectUserbaseData")
    scheduler.add_job(delete_QR_code_images, "interval", hours=1, id="deleteOtpImages")
    scheduler.start()
    app.run(debug=True, use_reloader=False)

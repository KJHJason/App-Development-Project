"""
This file, when run, creates databases to portray a scenario, using all the
variables in each file to ensure everything can be tested.

This helps support testing for the CRUD processes (not much for 'C').

Please update with variables and relevant shelve files accordingly for testing purposes.
"""



"""Databases"""
from Admin import Admin
from Teacher import Teacher
from Student import Student
from Course import Course
from Security import hash_password, sanitise
from IntegratedFunctions import generate_ID, generate_course_ID
from datetime import date
import shelve, shortuuid

def generate_admin_id(adminDict):
    generatedID = str(shortuuid.ShortUUID().random(length=5))
    if generatedID in adminDict:
        generate_admin_id(adminDict) # using recursion if there is a collision to generate a new unique ID
    return generatedID

# Open shelve
userBase = shelve.open("user", "c")
adminBase = shelve.open("admin", "c")

# Remove all prior entries
userDict = {}
adminDict = {}
courseDict = {}



"""
{"Users":{userID:User()}
         {userID:User()}
         {userID:User()}}
"""
"""
{"Admins":{adminID:Admin()}
          {adminID:Admin()}
          {adminID:Admin()}}
"""
"""
{"Courses":{courseID:Course()}
           {courseID:Course()}
           {courseID:Course()}}
"""
"""Student 1"""

#General
userID = generate_ID(userDict)
username = "James"
email = sanitise("CourseFinity123@gmail.com".lower())
password = hash_password("123!@#")
user = Student(userID, username, email, password)

# Get corresponding userID for updating/adding to dictionary
userDict[userID] = user


"""Student 2"""

#General
userID = generate_ID(userDict)
username = "Daniel"
email = sanitise("abc.net@gmail.com".lower())
password = hash_password("456$%^")
user = Student(userID, username, email, password)

#Courses (Royston)

# Get corresponding userID for updating/adding to dictionary
userDict[userID] = user

"""Teacher 1"""

#General
userID = generate_ID(userDict)
username = "Avery"
email = sanitise("ice_cream@gmail.com".lower())
password = hash_password("789&*(")
user = Teacher(userID, username, email, password)

#Teacher
user.set_earnings("100")
user.set_teacher_join_date(date(2022, 1, 1)) ## wtforms default datefield format = YYYY-MM-DD

#Card --> No Validation for Simulation
user.set_card_name("Avery Tim")
user.set_card_no("1122334455667788")
user.set_card_expiry("4/2024") ## Format Important
user.set_card_type("mastercard") ## [visa, mastercard, american express]

#Courses (Royston)

#Courses Teaching (Wei Ren)
title = "Making Web Apps The Easy Way (Spoilers: You can't!)"
description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
thumbnail = ""
price = "{:,.2f}".format(72.5)
courseType = "Zoom" ## Zoom or Video
status = "Available" ## Available or Unavailable

courseID = generate_course_ID(courseDict)
course = Course(courseID, userID, title, description, thumbnail, price, status)
course.add_tags("a","b","c","d","e")

course.switch_zoomCondition() # Video = True

# def __init__(self, userID, title, comment, rating)
course.add_rating("2", "Very Good", "Please make more.", "4")

# def __init__(self, title, description, thumbnail, **kwargs):
course.add_scheduleZoomLesson("Step 1: See Documentation","We learn Flask Documentation","")
course.get_lesson(0).set_timing("2022-07-03","15:30")
course.add_scheduleZoomLesson("Step 2: Practice","At least 5 Codeforces a Week","")
course.get_lesson(1).set_timing("2022-07-10","15:30")

user.set_courseTeaching(courseID)



# Get corresponding userID for updating/adding to dictionary
userDict[userID] = user
courseDict[courseID] = course

"""Teacher 2"""

#General
userID = generate_ID(userDict)
username = "Sara"
email = sanitise("tourism@gmail.com".lower())
password = hash_password("0-=)_+")
user = Teacher(userID, username, email, password)

#Teacher
user.set_earnings("100")
user.set_teacher_join_date(date(2020, 5, 2)) ## wtforms default datefield format = YYYY-MM-DD

#Card --> No Validation for Simulation
user.set_card_name("Sara Louise")
user.set_card_no("987654321234567")
user.set_card_expiry("9/2023") ## Format Important
user.set_card_type("american express") ## [visa, mastercard, american express]

#Courses (Royston)



#Courses Teaching (Wei Ren)
title = "Using Math to Find When Your Dad is Coming Home"
description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
thumbnail = ""
price = "69"
status = "Available" ## Available or Unavailable

courseID = generate_course_ID(courseDict)
course = Course(courseID, userID, title, description, thumbnail, price, status)
course.add_tags("z","y","x","w","v")

course.switch_videoCondition() # Video = True

# def __init__(self, userID, title, comment, rating)
course.add_rating("1", "A work of art.", "Cambridge be real quiet since this dropped.", "5")

# def __init__(self, title, description, thumbnail, videoData):
course.add_scheduleVideoLesson("Step 1: Calculate the Circumference of the Sun","He is probably travelling there.","","")

course.add_scheduleVideoLesson("Step 2: Going out into the field.","Follow the journey of the man who went out to get milk.","","")


user.set_courseTeaching(courseID)

# Get corresponding userID for updating/adding to dictionary
userDict[userID] = user
courseDict[courseID] = course



"""Admin 1"""
#General
adminID = generate_admin_id(adminDict)
username = "The Archivist"
email = sanitise("O5-2@SCP.com".lower())
password = hash_password("27sb2we9djaksidu8a")
admin = Admin(adminID, username, email, password)

#Admin


# Get corresponding userID for updating/adding to dictionary
adminDict[adminID] = admin

"""Admin 2"""
#General
adminID = generate_admin_id(adminDict)
username = "Tamlin"
email = sanitise("O5-13@SCP.com".lower())
password = hash_password("o4jru5fjr49f8ieri4")
admin = Admin(adminID, username, email, password)

#Admin


# Get corresponding userID for updating/adding to dictionary
adminDict[adminID] = admin




# Add courses
user = userDict[list(userDict.keys())[0]]
course = courseDict[list(courseDict.keys())[0]]
user.add_to_cart(course.get_courseID(),"Zoom") # Course ID '0' is "Making Web Apps The Easy Way (Spoilers: You can't!)"

print(user.get_shoppingCart())


# Overwrite entire shelve with updated dictionary
userBase["Users"] = userDict
adminBase["Admins"] = adminDict
userBase["Courses"] = courseDict

# Make sure to close!
userBase.close()
adminBase.close()
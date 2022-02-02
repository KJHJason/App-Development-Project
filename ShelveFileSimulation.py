"""
This file, when run, creates databases to portray a scenario, using all the
variables in each file to ensure everything can be tested.

This helps support testing for the CRUD processes (not much for 'C').

Please update with variables and relevant shelve files accordingly for testing purposes.
"""



"""Databases"""
from python_files.Admin import Admin
from python_files.Teacher import Teacher
from python_files.Student import Student
from python_files.Course import Course
from python_files.Security import sanitise, generate_admin_id
from python_files.IntegratedFunctions import generate_ID, generate_course_ID
from python_files.Graph import userbaseGraph
from datetime import date, timedelta
import shelve, pathlib

databaseFolder = str(pathlib.Path.cwd()) + "\\databases"

# Open shelve
userBase = shelve.open(databaseFolder + "\\user", "c")
adminBase = shelve.open(databaseFolder + "\\admin", "c")

# Remove all prior entries
userDict = {}
adminDict = {}
courseDict = {}
ticketDict = {}
graphList = []

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
userIDStudent1 = generate_ID(userDict)
username = "James"
email = sanitise("CourseFinity123@gmail.com".lower())
password = "123!@#"
user = Student(userIDStudent1, username, email, password)

# Get corresponding userID for updating/adding to dictionary
userDict[userIDStudent1] = user


"""Student 2"""

#General
userIDStudent2 = generate_ID(userDict)
username = "Daniel"
email = sanitise("abc.net@gmail.com".lower())
password = "456$%^"
user = Student(userIDStudent2, username, email, password)

#Courses (Royston)

# Get corresponding userID for updating/adding to dictionary
userDict[userIDStudent2] = user

"""Teacher 1"""

#General
userID = generate_ID(userDict)
username = "Avery"
email = sanitise("ice_cream@gmail.com".lower())
password = "789&*("
user = Teacher(userID, username, email, password)

#Teacher
user.set_earnings("100")
user.set_teacher_join_date(date(2022, 1, 1)) ## wtforms default datefield format = YYYY-MM-DD

#Courses (Royston)

#Courses Teaching (Wei Ren)
title = "Making Web Apps The Easy Way (Spoilers: You can't!)"
description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
thumbnail = "/static/images/courses/thumbnails/course_thumbnail_2.png"
zoomPrice = "{:,.2f}".format(72.5)
courseType = "Zoom" ## Zoom or Video

courseID = generate_course_ID(courseDict)
course = Course(courseID, courseType, zoomPrice, "Web_Development", title, description, thumbnail, userID)

course.add_review(userIDStudent2, "Good course to be honest", "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.", "4")

course.set_views(13)

user.set_courseTeaching(courseID)



# Get corresponding userID for updating/adding to dictionary
userDict[userID] = user
courseDict[courseID] = course

"""Teacher 2"""

#General
userID = generate_ID(userDict)
username = "Sara"
email = sanitise("tourism@gmail.com".lower())
password = "0-=)_+"
user = Teacher(userID, username, email, password)

#Teacher
user.set_earnings("100")
user.set_teacher_join_date(date(2020, 5, 2)) ## wtforms default datefield format = YYYY-MM-DD
"""
#Cashout Info
user.set_cashoutPreference("Phone")
user.set_cashoutContact("+6512345678")
"""
#Courses (Royston)



#Courses Teaching (Wei Ren)
title = "Using Math to Find When Your Dad is Coming Home"
description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
thumbnail = "/static/images/courses/thumbnails/course_thumbnail_1.png"
price = "{:,.2f}".format(69)
courseType = "Video"

courseID = generate_course_ID(courseDict)
course = Course(courseID, courseType, price, "Math", title, description, thumbnail, userID)


course.add_review(userIDStudent2, "Good course to be honest", "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.", "5")

course.set_views(1)

user.set_courseTeaching(courseID)

# Get corresponding userID for updating/adding to dictionary
userDict[userID] = user
courseDict[courseID] = course

title = "How to be a Daniel"
description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
thumbnail = "/static/images/courses/thumbnails/course_thumbnail_3.png"
price = "{:,.2f}".format(69)
courseType = "Video"

courseID = generate_course_ID(courseDict)
course = Course(courseID, courseType, price, "Other_Academics", title, description, thumbnail, userID)

# def __init__(self, userID, title, comment, rating)
course.add_review(userIDStudent1, "Very god tier course!", "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.", "5")

course.set_views(123)

user.set_courseTeaching(courseID)

# Get corresponding userID for updating/adding to dictionary
userDict[userID] = user
courseDict[courseID] = course

# Get corresponding userID for updating/adding to dictionary
userDict[userID] = user
courseDict[courseID] = course

title = "How to be a Daniel 2"
description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
thumbnail = "/static/images/courses/thumbnails/course_thumbnail_3.png"
videoPrice = "{:,.2f}".format(69)
courseType = "Video"

courseID = generate_course_ID(courseDict)
course = Course(courseID, courseType, videoPrice, "Other_Academics", title, description, thumbnail, userID)

# def __init__(self, userID, title, comment, rating)
course.add_review(userIDStudent1, "A sequel to the very god tier course!", "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.", "5")

course.set_views(1000)

user.set_courseTeaching(courseID)

# Get corresponding userID for updating/adding to dictionary
userDict[userID] = user
courseDict[courseID] = course




"""Admin 1"""
#General
adminID = generate_admin_id(adminDict)
username = "The Archivist"
email = sanitise("O52@SCP.com".lower())
password = "27sb2we9djaksidu8a"
admin = Admin(adminID, username, email, password)

#Admin


# Get corresponding userID for updating/adding to dictionary
adminDict[adminID] = admin

"""Admin 2"""
#General
adminID = generate_admin_id(adminDict)
username = "Tamlin"
email = sanitise("O513@SCP.com".lower())
password = "o4jru5fjr49f8ieri4"
admin = Admin(adminID, username, email, password)

#Admin

"""Admin 3"""
#General
adminID = generate_admin_id(adminDict)
username = "test"
email = sanitise("test@test.com".lower())
password = "123123123"
admin = Admin(adminID, username, email, password)

#Admin

# Get corresponding userID for updating/adding to dictionary
adminDict[adminID] = admin




# Add courses
user = userDict[list(userDict.keys())[0]]
course = courseDict[list(courseDict.keys())[0]]
user.add_to_cart(course.get_courseID()) # Course ID '0' is "Making Web Apps The Easy Way (Spoilers: You can't!)"

print(user.get_shoppingCart())


# set some data for user base graph for admin dashboard
todayDate = date.today()

graphList = [userbaseGraph(1), userbaseGraph(3), userbaseGraph(3), userbaseGraph(4), userbaseGraph(10), userbaseGraph(25), userbaseGraph(150), userbaseGraph(200), userbaseGraph(180), userbaseGraph(300), userbaseGraph(500), userbaseGraph(700), userbaseGraph(800), userbaseGraph(900), userbaseGraph(1001), userbaseGraph(1200), userbaseGraph(1500), userbaseGraph(1800), userbaseGraph(2600), userbaseGraph(3900), userbaseGraph(5000), userbaseGraph(8000), userbaseGraph(9000), userbaseGraph(9500), userbaseGraph(9900), userbaseGraph(12000), userbaseGraph(12000), userbaseGraph(12000), userbaseGraph(12000), userbaseGraph(12000)]

for i in range(len(graphList)-1, -1, -1):
    graphList[i].set_date(todayDate - timedelta(days=30-i))

print(graphList)

# Overwrite entire shelve with updated dictionary
userBase["Users"] = userDict
adminBase["Admins"] = adminDict
userBase["Courses"] = courseDict
userBase["userGraphData"] = graphList
adminBase["Tickets"] = ticketDict

# Make sure to close!
userBase.close()
adminBase.close()
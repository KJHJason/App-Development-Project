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
from Security import password_manager, sanitise, validate_email


import shelve
userBase = shelve.open("user", "c")
adminBase = shelve.open("admin", "c")



"""Student 1"""

#General
userID = "0"
username = "James"
email = validate_email(sanitise("CourseFinity123@gmail.com".lower()))
password = password_manager().hash_password("123!@#")
user = Student(userID, username, email, password)

#Card --> No Validation for Simulation
user.set_card_name("James Oliver")
user.set_card_no("0102030405060708")
user.set_card_expiry("7/2022") ## Format Important
user.set_card_cvv("123")
user.set_card_type("visa") ## [visa, mastercard, american express]

#Courses (Royston)



userBase[userID]=user

"""Student 2"""

#General
userID = "1"
username = "Daniel"
email = validate_email(sanitise("abc.net@gmail.com".lower()))
password = password_manager().hash_password("456$%^")
user = Student(userID, username, email, password)

#Card --> No Validation for Simulation
user.set_card_name("Daniel Pang")
user.set_card_no("8070605040302010")
user.set_card_expiry("10/2023") ## Format Important
user.set_card_cvv("321")
user.set_card_type("mastercard") ## [visa, mastercard, american express]

#Courses (Royston)


userBase[userID]=user

"""Teacher 1"""

#General
userID = "2"
username = "Avery"
email = validate_email(sanitise("ice_cream@gmail.com".lower()))
password = password_manager().hash_password("789&*(")
user = Teacher(userID, username, email, password)

#Teacher
user.set_earnings("100")
user.set_joinDate("2022-04-01") ## wtforms default datefield format = YYYY-MM-DD

#Card --> No Validation for Simulation
user.set_card_name("Avery Tim")
user.set_card_no("1122334455667788")
user.set_card_expiry("4/2024") ## Format Important
user.set_card_cvv("543")
user.set_card_type("mastercard") ## [visa, mastercard, american express]

#Courses (Royston)



#Courses Teaching (Wei Ren)
title = "Making Web Apps The Easy Way (Spoilers: You can't!)"
description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
thumbnail = ""
price = "72.5"
courseType = "Zoom" ## Zoom or Video
status = "Available" ## Available or Unavailable

course = Course(title, description, thumbnail, price, courseType, status)
course.add_tags("a","b","c","d","e")

# def __init__(self, userID, title, comment, rating)
course.add_rating("2", "Very Good", "Please make more.", "4")

# def __init__(self, title, description, thumbnail, **kwargs):
course.add_scheduleZoomPart("Step 1: See Documentation","We learn Flask Documentation","")
course.get_part(0).set_timing("2022-07-03","15:30")

course.add_scheduleZoomPart("Step 2: Practice","At least 5 Codeforces a Week","")
course.get_part(1).set_timing("2022-07-10","15:30")



userBase[userID]=user

"""Teacher 2"""

#General
userID = "3"
username = "Sara"
email = validate_email(sanitise("tourism@gmail.com".lower()))
password = password_manager().hash_password("0-=)_+")
user = Teacher(userID, username, email, password)

#Teacher
user.set_earnings("100")
user.set_joinDate("2020-05-02") ## wtforms default datefield format = YYYY-MM-DD

#Card --> No Validation for Simulation
user.set_card_name("Sara Louise")
user.set_card_no("987654321234567")
user.set_card_expiry("9/2023") ## Format Important
user.set_card_cvv("934")
user.set_card_type("american express") ## [visa, mastercard, american express]

#Courses (Royston)



#Courses Teaching (Wei Ren)
title = "Using Math to Find When Your Dad is Coming Home"
description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
thumbnail = ""
price = "69"
courseType = "Video" ## Zoom or Video
status = "Available" ## Available or Unavailable

user.set_courseTeaching(title, description, thumbnail, price, courseType, status)
course.add_tags("z","y","x","w","v")

# def __init__(self, userID, title, comment, rating)
course.add_rating("1", "A work of art.", "Cambridge be real quiet since this dropped.", "5")

# def __init__(self, title, description, thumbnail, videoData):
course.add_scheduleVideoPart("Step 1: Calculate the Circumference of the Sun","He is probably travelling there.","","")

course.add_scheduleVideoPart("Step 2: Going out into the field.","Follow the journey of the man who went out to get milk.","","")



userBase[userID]=user

"""Admin 1"""
#General
adminID = "0"
username = "The Archivist"
email = validate_email(sanitise("O5-2@SCP.com".lower()))
password = password_manager().hash_password("27sb2we9djaksidu8a")
admin = Admin(userID, username, email, password)

#Admin



adminBase[adminID] = admin

"""Admin 2"""
#General
adminID = "1"
username = "Tamlin"
email = validate_email(sanitise("O5-13@SCP.com".lower()))
password = password_manager().hash_password("o4jru5fjr49f8ieri4")
admin = Admin(userID, username, email, password)

#Admin




adminBase[adminID] = admin


userBase.close()
adminBase.close()

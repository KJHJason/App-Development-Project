"""
This file, when run, creates databases to portray a scenario, using all the
variables in each file to ensure everything can be tested.

This helps support testing for the CRUD processes (not much for 'C').

Please update with variables and relevant shelve files accordingly for testing purposes.
"""



"""Databases"""
from Teacher import Teacher
from Student import Student
from Security import password_manager, sanitise, validate_email
from CardValidation import validate_card_number, get_card_type, validate_cvv, validate_formatted_expiry_date, validate_expiry_date


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




"""Teacher 1"""

#General
userID = "2"
username = "Avery"
email = validate_email(sanitise("ice_cream@gmail.com".lower()))
password = password_manager().hash_password("789&*(")
user = Teacher(userID, username, email, password)

#Teacher
user.set_earnings()
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
user.set_courseTeaching(title, description, thumbnail, price, courseType, status)


"""Teacher 2"""

#General
userID = "3"
username = "Sara"
email = validate_email(sanitise("tourism@gmail.com".lower()))
password = password_manager().hash_password("0-=)_+")
user = Teacher(userID, username, email, password)

#Teacher
user.set_earnings()
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



"""Admin 1"""
#General
userID = "4"
username = "The Archivist"
email = validate_email(sanitise("O5-2@SCP.com".lower()))
password = password_manager().hash_password("27sb2we9djaksidu8a")
user = Teacher(userID, username, email, password)

#Admin




"""Admin 2"""
#General
userID = "5"
username = "Tamlin"
email = validate_email(sanitise("O5-13@SCP.com".lower()))
password = password_manager().hash_password("o4jru5fjr49f8ieri4")
user = Teacher(userID, username, email, password)

#Admin






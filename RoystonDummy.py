from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import shelve, os, math, stripe
import Student, Teacher, Admin, Forms
from Security import password_manager, sanitise, validate_email
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path    

courseDict = {
    0: {'name': 'Python 101', 'description': "lorem ipsum on deez python nuts", 'price': 420, "tag": "programming"},
    1: {'name': 'Maths 101', 'description': "lorem ipsum on deez maths nuts", 'price': 69, "tag": "maths"},
    2: {'name': 'Science 101', 'description': "lorem ipsum on deez science nuts", 'price': 1337, "tag": "science"}
}

print(courseDict[1]['name'])

coursePurchasedList = []
purchaseHistoryDict = {
    0:courseDict[2]
}

for purchasedCourseID in purchaseHistoryDict:
    coursePurchasedList.append(purchasedCourseID)


print(purchaseHistoryDict[0])
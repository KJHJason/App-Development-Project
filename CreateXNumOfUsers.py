import shelve
import Student
from Security import hash_password
from IntegratedFunctions import get_userID

userDict = {}
db = shelve.open("user", "c")
try:
    if 'Users' in db:
        userDict = db['Users']
    else:
        print("No user data in user shelve files.")
        db["Users"] = userDict
except:
    db.close()
    print("Error in retrieving Users from user.db")

noOfUser = int(input("How many user account to create?: "))

startID = get_userID(userDict)
    
for i in range(startID, noOfUser+startID):
    hashedPwd = hash_password("123123")
    email = "test" + str(i) + "@gmail.com"
    username = "test" + str(i)
    user = Student.Student(i, username, email, hashedPwd)
    userDict[i] = user
    print(f"User created with the ID, {i}.")

db["Users"] = userDict
db.close()
print(f"{noOfUser} users created successfully.")
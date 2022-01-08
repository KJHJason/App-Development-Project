import shelve
import Student
from Security import hash_password

def get_userID(userDict):
    userIDShelveData = 0 # initialise to 0 as the shelve files can be missing or new which will have no data
    for key in userDict:
        print("retrieving")
        userIDShelveData = int(userDict[key].get_user_id())
        print("ID in database:", userIDShelveData)
        userIDShelveData += 1 # add 1 to get the next possible user ID if there is/are user data in the user shelve files
    return userIDShelveData

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
import shelve, Student, uuid
from Security import hash_password

def get_userID(userDict):
    generatedID = str(uuid.uuid4())
    if generatedID in userDict:
        get_userID(userDict) # using recursion if there is a collision to generate a new unique ID
    return generatedID

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
    
for i in range(noOfUser):
    hashedPwd = hash_password("123123")
    email = "test" + str(i) + "@gmail.com"
    username = "test" + str(i)
    uid = get_userID(userDict)
    user = Student.Student(uid, username, email, hashedPwd)
    userDict[uid] = user
    db["Users"] = userDict
    print(f"User created with the ID, {uid}.")


db.close()
print(f"{noOfUser} users created successfully.")
import shelve, Student, uuid
from Security import hash_password

def generate_ID(inputDict):
    generatedID = str(uuid.uuid4())
    if generatedID in inputDict:
        generate_ID(inputDict) # using recursion if there is a collision to generate a new unique ID
    return generatedID

def getLatestTestI(userDict):
    try:
        latestID = list(userDict.keys())[-1]
        userObject = userDict.get(latestID)
        username = userObject.get_username()[-1]
        return (int(username) + 1)
    except:
        return 0 # meaning that there is no users in the user db yet

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
    
getLatestTestI = int(getLatestTestI(userDict))
print(getLatestTestI)
for i in range(getLatestTestI, noOfUser+getLatestTestI):
    hashedPwd = hash_password("123123")
    email = "test" + str(i) + "@gmail.com"
    username = "test" + str(i)
    uid = generate_ID(userDict)
    user = Student.Student(uid, username, email, hashedPwd)
    userDict[uid] = user
    db["Users"] = userDict
    print(f"User, {username}, created with the ID, {uid}.")


db.close()
print(f"{noOfUser} users created successfully.")
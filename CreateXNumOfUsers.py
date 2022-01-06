import shelve
import Student
from Security import password_manager


userDict = {}
db = shelve.open("user", "c")  # "c" flag as to create the files if there were no files to retrieve from and also to create the user if the validation conditions are met
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
    hashedPwd = password_manager().hash_password("123123")
    email = "test" + str(i) + "@gmail.com"
    username = "test" + str(i)
    user = Student.Student(i, username, email, hashedPwd)
    userDict[i] = user

db["Users"] = userDict
db.close()
print(f"{noOfUser} users created successfully.")
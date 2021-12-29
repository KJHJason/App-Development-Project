from Admin import Admin
from Security import PasswordManager, Sanitise
import shelve, re

def validate_email(email):
    if(re.fullmatch(regex, email)):
        print("Valid Email")
        return True
    else:
        print("Invalid Email")
        return False

# regular expression for validating an Email
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

pwdManager = PasswordManager()

cmd_menu = """
Welcome to admin control panel!
1. Create a new admin account
0. Exit
"""

while True:
    print(cmd_menu)
    cmd_input = input("Enter number: ")
    if cmd_input == "1":
        username = Sanitise(input("Enter username for admin account: "))
        email = Sanitise(input("Enter email for admin account: "))
        password = pwdManager.hash_password(input("Enter password for admin account: "))
        cfm_password = input("Confirm password for admin account: ")

        pwdMatched = pwdManager.verify_password(password, cfm_password)

        if pwdMatched:
            print("Password for admin entered matched.")
            # Retrieving data from shelve for duplicate data checking
            adminDict = {}
            db = shelve.open("admin", "c")  # "c" flag as to create the files if there were no files to retrieve from and also to create the user if the validation conditions are met
            try:
                if 'Admins' in db:
                    adminDict = db['Admins']
                else:
                    print("No admin account data in user shelve files")
                    db["Admins"] = adminDict
            except:
                db.close()
                print("Error in retrieving Admins from user.db")
            
            email_duplicates = False
            username_duplicates = False

            adminIDShelveData = 0 # initialise to 0 as the shelve files can be missing or new which will have no data
            # checking duplicates for username and getting the latest possible user ID from the admin shelve files
            for key in adminDict:
                print("retrieving")
                usernameShelveData = adminDict[key].get_username()
                adminIDShelveData = int(adminDict[key].get_user_id())
                print("ID in database:", adminIDShelveData)
                adminIDShelveData += 1 # add 1 to get the next possible user ID if there is/are user data in the user shelve files
                if username == usernameShelveData:
                    print("Username in database:", usernameShelveData)
                    print("Username input:", username)
                    print("Verdict: Username already taken.")
                    email_duplicates = True
                else:
                    print("Username in database:", usernameShelveData)
                    print("Username input:", username)
                    print("Verdict: Username is unique.")

            # Checking duplicates for email
            for key in adminDict:
                print("retrieving")
                emailShelveData = adminDict[key].get_email()
                if email == emailShelveData:
                    print("Email in database:", emailShelveData)
                    print("Email input:", email)
                    print("Verdict: User email already exists.")
                    email_duplicates = True
                else:
                    print("Email in database:", emailShelveData)
                    print("Email input:", email)
                    print("Verdict: User email is unique.")
            
            if email_duplicates:
                db.close()
                print("Duplicate admin email, please enter a unique email.")
            else:
                emailValid = validate_email(email)
                if emailValid:
                    if username_duplicates:
                        db.close()
                        print("Duplciate admin username, please enter a unique username.")
                    else:
                        admin = Admin(adminIDShelveData, username, email, password)
                        adminDict[adminIDShelveData] = admin
                        print("Admin account created.")
                        db["Admins"] = adminDict
                        db.close()
                        print("Admin account ID:", admin.get_user_id())
                else:
                    db.close()
        else:
            print("Password for admin entered did not matched.")
    elif cmd_input == "0":
        print("Thank you and have a nice day.")
        quit()
    else:
        print("Invalid command, please enter the number 1 or 0 as specified in the control panel guide.")
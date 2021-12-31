from Admin import Admin
from Security import password_manager, sanitise, validate_email
import shelve, re

def validate_pwd_length(pwd, pwdMinimumLength):
    if len(pwd) < pwdMinimumLength:
        print("\nError: Please enter a password with at least {} characters!" .format(pwdMinimumLength))
        return False
    else:
        print("Verdict: Password length accepted, within {} characters minimum requirement." .format(pwdMinimumLength))
        return True

pwdManager = password_manager()

cmd_menu = """
Welcome to admin control panel!
1. Create a new admin account
0. Exit

Important Notes:
In the event of the program freezing, press CTRL + C to force shut down the program.
However, it may result in data corruption.
Hence, please only force shut down the program if necessary.
"""

while True:
    print(cmd_menu)
    cmd_input = input("Enter number: ")
    if cmd_input == "1":
        username = sanitise(input("Enter username for admin account: "))
        email = sanitise(input("Enter email for admin account: "))
        emailValid = False
        if email != False:
            print("\nValidating Email...")
            emailValid = validate_email(email)
        if emailValid and username != False and email != False:
            password = input("\nEnter password for admin account: ")
            
            pwdLengthValidate = validate_pwd_length(password, 6) # change the number accordingly to specify the minimum characters of the password that is required (accordingly to CourseFinity's password policy)

            if pwdLengthValidate:
                password = pwdManager.hash_password(password)
                cfm_password = input("\nConfirm password for admin account: ")

                pwdMatched = pwdManager.verify_password(password, cfm_password)

                if pwdMatched:
                    print("\nPassword for admin entered matched.")
                    # Retrieving data from shelve for duplicate data checking
                    adminDict = {}
                    db = shelve.open("admin", "c")  # "c" flag as to create the files if there were no files to retrieve from and also to create the user if the validation conditions are met
                    try:
                        if 'Admins' in db:
                            adminDict = db['Admins']
                            print("\nRetrieved data from admin account database")
                        else:
                            print("\nError: No admin account data in admin account database")
                            db["Admins"] = adminDict
                            print("Error resolved: Created an empty admin account database")
                    except:
                        db.close()
                        print("\nError in retrieving Admins from user.db")
                    
                    email_duplicates = False
                    username_duplicates = False

                    adminIDShelveData = 0 # initialise to 0 as the shelve files can be missing or new which will have no data
                    # checking duplicates for username and getting the latest possible user ID from the admin shelve files
                    for key in adminDict:
                        print("\nretrieving usernames")
                        usernameShelveData = adminDict[key].get_username()
                        adminIDShelveData = int(adminDict[key].get_user_id())
                        adminIDShelveData += 1 # add 1 to get the next possible user ID if there is/are user data in the user shelve files
                        if username == usernameShelveData:
                            print("Error: Username already taken.")
                            username_duplicates = True
                            break

                    # Checking duplicates for email
                    for key in adminDict:
                        print("\nretrieving emails")
                        emailShelveData = adminDict[key].get_email()
                        if email == emailShelveData:
                            print("Error: Admin email already exists.")
                            email_duplicates = True
                            break
                    
                    if email_duplicates and username_duplicates:
                        print("\nError: Duplicate admin username and password, please enter unique username and password!")
                        db.close()
                    else:
                        if email_duplicates:
                            db.close()
                            print("\nError: Duplicate admin email, please enter a unique email.")
                        else:
                            if username_duplicates:
                                db.close()
                                print("\nError: Duplicate admin username, please enter a unique username.")
                            else:
                                admin = Admin(adminIDShelveData, username, email, password)
                                adminDict[adminIDShelveData] = admin
                                print("\nAdmin account created/updated in the admin account database")
                                db["Admins"] = adminDict
                                db.close()
                                print("Admin account ID:", admin.get_user_id())
                else:
                    print("\nError: Password for admin entered did not matched.")
        else:
            if email == False:
                print("\nError: You cannot enter an empty input for the email!")
            if username == False:
                print("\nError: You cannot enter an empty input for the username!")

    elif cmd_input == "0":
        print("\nThank you and have a nice day.")
        quit()
    else:
        print("\nError: Invalid command, please enter the number 1 or 0 as specified in the control panel guide.")
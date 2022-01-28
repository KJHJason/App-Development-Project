from python_files.Admin import Admin
from python_files.Security import sanitise, validate_email, generate_admin_id, validate_pwd_length
import shelve, pathlib

cmd_menu = """
Welcome to the admin console!

Please select the following command number to continue:
1. Create a new admin account
2. Update admin password
3. Deactivate an admin account
4. Reactivate an admin account
5. Delete an admin account
6. View all admin accounts
0. Exit

Important Notes:
In the event of the program freezing, press CTRL + C to force shut down the program.
However, it may result in data corruption.
Hence, please only force shut down the program if necessary.
"""

# Command line 1-2 feature/operations done by Jason
# Search by admin ID by Jason ID
# Note that UUID v4 is not used for id generation for the admins as there will not be millions of admins if deployed. Hence, using shortuuid to generate a 5 characters id for admins which is feasible for a few thousands of admin accounts.
# Command line 3-5 feature/operations done by Clarence
# Command line 6 feature/operation done by Royston

def main():
    adminDatabaseFilePath = str(pathlib.Path(__file__).parent.resolve()).replace("\\", "/") + "/databases" + "/admin"
    while True:
        print(cmd_menu)
        cmd_input = input("Enter number: ")
        if cmd_input == "1":
            while True:
                username = sanitise(input("Enter username for admin account (0 to exit): "))
                if username == "0":
                    break
                email = sanitise(input("Enter email for admin account (0 to exit): "))
                if email == "0":
                    break
                emailValid = False
                if email != False:
                    print("\nValidating Email...")
                    emailValid = validate_email(email)
                    if emailValid == False:
                        print("\nError: Invalid Email Format. Please try again.")
                        break
                if emailValid and username != False and email != False:
                    print("Email Validated")
                    while True:
                        password = input("\nEnter password for admin account (0 to exit): ")
                        if password == "0":
                            break
                        
                        pwdLengthValidate = validate_pwd_length(password, 8) # change the number accordingly to specify the minimum characters of the password that is required (accordingly to CourseFinity's password policy)

                        if pwdLengthValidate:
                            cfm_password = input("\nConfirm password (0 to exit): ")
                            if cfm_password == "0":
                                break
                        
                            if password == cfm_password:
                                pwdMatched = True
                            else:
                                pwdMatched = False

                            if pwdMatched:
                                print("\nPassword for admin entered matched.")
                                # Retrieving data from shelve for duplicate data checking
                                adminDict = {}
                                db = shelve.open(adminDatabaseFilePath, "c")
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
                                    print("\nError in retrieving Admins from admin.db")
                                
                                email_duplicates = False
                                username_duplicates = False

                                # checking duplicates for username and getting the latest possible user ID from the admin shelve files
                                print("\nretrieving usernames")
                                for key in adminDict:
                                    usernameShelveData = adminDict[key].get_username()
                                    if username == usernameShelveData:
                                        print("Error: Username already taken.")
                                        username_duplicates = True
                                        break

                                # Checking duplicates for email
                                print("\nretrieving emails")
                                for key in adminDict:
                                    emailShelveData = adminDict[key].get_email()
                                    if email == emailShelveData:
                                        print("Error: Admin email already exists.")
                                        email_duplicates = True
                                        break
                                
                                if email_duplicates and username_duplicates:
                                    print("\nError: Duplicate admin username and password, please enter unique username and password!")
                                    db.close()
                                    break
                                else:
                                    if email_duplicates:
                                        db.close()
                                        print("\nError: Duplicate admin email, please enter a unique email.")
                                        break
                                    else:
                                        if username_duplicates:
                                            db.close()
                                            print("\nError: Duplicate admin username, please enter a unique username.")
                                            break
                                        else:
                                            adminID = generate_admin_id(adminDict)
                                            admin = Admin(adminID, username, email, password)
                                            adminDict[adminID] = admin
                                            print("\nAdmin account created/updated in the admin account database")
                                            db["Admins"] = adminDict
                                            db.close()
                                            print("Admin account ID:", admin.get_user_id())
                                            break
                            else:
                                print("\nError: Password for admin entered did not matched.")
                    break
                else:
                    if email == False and username == False:
                        print("\nError: You cannot enter an empty input for the email and username!")
                    elif email == False:
                        print("\nError: You cannot enter an empty input for the email!")
                    elif username == False:
                        print("\nError: You cannot enter an empty input for the username!")

        elif cmd_input == "2":
            while True:
                email = sanitise(input("Enter email or admin id for the admin account (0 to exit): "))
                if email == "0":
                    break
                if email != False:
                    adminDict = {}
                    db = shelve.open(adminDatabaseFilePath, "c")
                    try:
                        if 'Admins' in db:
                            adminDict = db['Admins']
                            print("\nRetrieved data from admin account database")
                            fileFound = True
                        else:
                            db.close()
                            print("\nError: No admin account data in admin account database")
                            fileFound = False
                    except:
                        db.close()
                        print("\nError in retrieving Admins from admin.db")
                        fileFound = False

                    if fileFound:
                        emailValidation = validate_email(email)
                        if emailValidation:
                            emailValid = False
                            print("\nretrieving emails")
                            for key in adminDict:
                                emailShelveData = adminDict[key].get_email()
                                if email == emailShelveData:
                                    print("Verdict: Admin email Found.")
                                    emailValid = True
                                    adminKey = adminDict[key]
                                    break
                            if emailValid:
                                while True:
                                    password = input("\nEnter password for admin account (0 to cancel): ")
                                    pwdLengthValidate = validate_pwd_length(password, 8) # change the number accordingly to specify the minimum characters of the password that is required (accordingly to CourseFinity's password policy)
                                    if pwdLengthValidate or password == "0":
                                        break
                                if password == "0":
                                    break
                                if pwdLengthValidate:
                                    cfm_password = input("\nConfirm password for admin account (0 to cancel): ")
                                    if cfm_password == "0":
                                        break

                                    if password == cfm_password:
                                        pwdMatched = True
                                    else:
                                        pwdMatched = False

                                    if pwdMatched:
                                        adminKey.set_password(password)
                                        db["Admins"] = adminDict
                                        db.close()
                                        print(f"\nAdmin password updated successfully for the account with the email {email} .")
                                        break
                                    else:
                                        db.close()
                                        print(f"\nError: Password for admin email, {email}, entered did not matched.")
                                        break
                                else:
                                    db.close()
                                    break
                            else:
                                db.close()
                                print("\nError: No admin account with that email exists.")
                        else:
                            # if the admin searches for the admin accounts using the admin id
                            if email in adminDict:
                                adminObject = adminDict.get(email)
                                password = input("\nEnter password for admin account: ")
                                while True:
                                    password = input("\nEnter password for admin account (0 to cancel): ")
                                    pwdLengthValidate = validate_pwd_length(password, 8) # change the number accordingly to specify the minimum characters of the password that is required (accordingly to CourseFinity's password policy)
                                    if pwdLengthValidate or password == "0":
                                        break
                                if password == "0":
                                    break
                                if pwdLengthValidate:
                                    cfm_password = input("\nConfirm password for admin account (0 to cancel): ")
                                    if cfm_password == "0":
                                        break
                                    
                                    if password == cfm_password:
                                        pwdMatched = True
                                    else:
                                        pwdMatched = False

                                    if pwdMatched:
                                        adminObject.set_password(password)
                                        db["Admins"] = adminDict
                                        db.close()
                                        print(f"\nAdmin password updated successfully for admin id, {email}.")
                                        break
                                    else:
                                        db.close()
                                        print(f"\nError: Password for the admin id, {email}, entered did not matched.")
                                        break
                                else:
                                    db.close()
                                    break
                            else:
                                db.close()
                                print("\nError: Entered admin email or user id is invalid, please try again.")
                    else:
                        db.close()
                        print("\nError: Please create an admin account and try again later.")
                        break
                else:
                    print("\nError: You cannot leave the input empty! Please try again.")

        elif cmd_input == "3":
            while True:
                email = sanitise(input("Enter email or admin id for the admin account (0 to exit): "))
                if email == "0":
                    break
                if email != False:

                    adminDict = {}
                    db = shelve.open(adminDatabaseFilePath, "c")
                    try:
                        if 'Admins' in db:
                            adminDict = db['Admins']
                            print("\nRetrieved data from admin account database")
                            fileFound = True
                        else:
                            db.close()
                            print("\nError: No admin account data in admin account database")
                            fileFound = False
                    except:
                        db.close()
                        print("\nError in retrieving Admins from admin.db")
                        fileFound = False
                    
                    if fileFound:
                        emailValidation = validate_email(email)
                        if emailValidation:
                            emailValid = False
                            print("\nretrieving emails")
                            for key in adminDict:
                                emailShelveData = adminDict[key].get_email()
                                if email == emailShelveData:
                                    print("Verdict: Admin email Found.")
                                    emailValid = True
                                    adminKey = adminDict[key]
                                    break
                            if emailValid:
                                adminStatus = adminKey.get_status()
                                if adminStatus == "Active":
                                    adminKey.set_status("Inactive")
                                    db["Admins"] = adminDict
                                    db.close()
                                    print(f"\nAdmin account with the ID, {adminKey.get_user_id()}, deactivated.")
                                    break
                                else:
                                    db.close()
                                    print(f"\nAdmin account with the ID, {adminKey.get_user_id()}, is already deactivated.")
                                    break
                            else:
                                db.close()
                                print("\nError: No admin account with that email exists.")
                        else:
                            # if the admin searches for the admin accounts using the admin id
                            if email in adminDict:
                                adminObject = adminDict.get(email)
                                adminStatus = adminObject.get_status()
                                if adminStatus == "Active":
                                    adminObject.set_status("Inactive")
                                    db["Admins"] = adminDict
                                    db.close()
                                    print(f"\nAdmin account with the ID, {email}, deactivated.")
                                    break
                                else:
                                    db.close()
                                    print(f"\nAdmin account with the ID, {email}, is already deactivated.")
                                    break
                            else:
                                db.close()
                                print("\nError: Entered admin email or user id is invalid, please try again.")
                    else:
                        db.close()
                        print("\nError: Please create an admin account and try again later.")
                        break
                else:
                    print("\nError: You cannot leave the input empty! Please try again.")

        elif cmd_input == "4":
            while True:
                email = sanitise(input("Enter email or admin id for the admin account (0 to exit): "))
                if email == "0":
                    break
                if email != False:
                    adminDict = {}
                    db = shelve.open(adminDatabaseFilePath, "c")
                    try:
                        if 'Admins' in db:
                            adminDict = db['Admins']
                            print("\nRetrieved data from admin account database")
                            fileFound = True
                        else:
                            db.close()
                            print("\nError: No admin account data in admin account database")
                            fileFound = False
                    except:
                        db.close()
                        print("\nError in retrieving Admins from admin.db")
                        fileFound = False
                    
                    if fileFound:
                        emailValidation = validate_email(email)
                        if emailValidation:
                            emailValid = False
                            print("\nretrieving emails")
                            for key in adminDict:
                                emailShelveData = adminDict[key].get_email()
                                if email == emailShelveData:
                                    print("Verdict: Admin email Found.")
                                    emailValid = True
                                    adminKey = adminDict[key]
                                    break
                            if emailValid:
                                adminStatus = adminKey.get_status()
                                if adminStatus == "Inactive":
                                    adminKey.set_status("Active")
                                    db["Admins"] = adminDict
                                    db.close()
                                    print(f"\nAdmin account with the ID, {adminKey.get_user_id()}, reactivated.")
                                    break
                                else:
                                    db.close()
                                    print(f"\nAdmin account with the ID, {adminKey.get_user_id()}, is already active.")
                                    break
                            else:
                                db.close()
                                print("\nError: No admin account with that email exists.")
                        else:
                            # if the admin searches for the admin accounts using the admin id
                            if email in adminDict:
                                adminObject = adminDict.get(email)
                                adminStatus = adminObject.get_status()
                                if adminStatus == "Inactive":
                                    adminObject.set_status("Active")
                                    db["Admins"] = adminDict
                                    db.close()
                                    print(f"\nAdmin account with the ID, {email}, reactivated.")
                                    break
                                else:
                                    db.close()
                                    print(f"\nAdmin account with the ID, {email}, is already active.")
                                    break
                            else:
                                db.close()
                                print("\nError: Entered admin email or user id is invalid, please try again.")
                    else:
                        db.close()
                        print("\nError: Please create an admin account and try again later.")
                        break
                else:
                    print("\nError: You cannot leave the input empty! Please try again.")

        elif cmd_input == "5":
            while True:
                email = sanitise(input("Enter email or admin id for the admin account: "))
                if email != False:
                    adminDict = {}
                    db = shelve.open(adminDatabaseFilePath, "c")
                    try:
                        if 'Admins' in db:
                            adminDict = db['Admins']
                            print("\nRetrieved data from admin account database")
                            fileFound = True
                        else:
                            db.close()
                            print("\nError: No admin account data in admin account database")
                            fileFound = False
                    except:
                        db.close()
                        print("\nError in retrieving Admins from admin.db")
                        fileFound = False

                    if fileFound:
                        emailValidation = validate_email(email)
                        if emailValidation:
                            if fileFound:
                                emailValid = False
                                print("\nretrieving emails")
                                for key in adminDict:
                                    emailShelveData = adminDict[key].get_email()
                                    if email == emailShelveData:
                                        print("Verdict: Admin email Found.")
                                        emailValid = True
                                        adminKey = adminDict[key]
                                        break
                                if emailValid:
                                    removedAdmin = adminDict.pop(adminKey.get_user_id())
                                    db["Admins"] = adminDict
                                    db.close()
                                    print(f"\nAdmin account with the ID, {removedAdmin.get_user_id()}, deleted successfully.")
                                    break
                                else:
                                    db.close()
                                    print("\nError: No admin account with that email exists.")
                        else:
                            # if the admin searches for the admin accounts using the admin id
                            if email in adminDict:
                                removedAdmin = adminDict.pop(email)
                                db["Admins"] = adminDict
                                db.close()
                                print(f"\nAdmin account with the ID, {email}, deleted successfully.")
                                break
                            else:
                                db.close()
                                print("\nError: Entered admin email or user id is invalid, please try again.")
                    else:
                        db.close()
                        print("\nError: Please create an admin account and try again later.")
                        break
                else:
                    print("\nError: You cannot leave the input empty! Please try again.")

        elif cmd_input == "6":
            adminDict = {}
            db = shelve.open(adminDatabaseFilePath, "c")
            try:
                if 'Admins' in db:
                    adminDict = db['Admins']
                    print("\nRetrieved data from admin account database")
                    fileFound = True
                    db.close()
                else:
                    db.close()
                    print("\nError: No admin account data in admin account database")
                    fileFound = False
            except:
                db.close()
                print("\nError in retrieving Admins from admin.db")
                fileFound = False
            
            if fileFound:
                count = len(adminDict)
                print(f"There are {count} admin accounts.\n")
                for key in adminDict:
                    adminKey = adminDict[key]
                    adminID = adminKey.get_user_id()
                    username = adminKey.get_username()
                    email = adminKey.get_email()
                    status = adminKey.get_status()
                    print(f"Admin ID: {adminID} | Username: {username} | Email: {email} | Status: {status}")
            else:
                print("Error could not be resolved...\nSolution: Please create an admin account before reading all admin accounts.")
                
        elif cmd_input == "0":
            print("\nThank you and have a nice day.")
            break
        else:
            print("\nError: Invalid command, please enter the number 1 or 0 as specified in the control panel guide.")

if __name__ == '__main__':
    main()
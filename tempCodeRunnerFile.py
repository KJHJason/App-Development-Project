for key in userDict:
            passwordShelveData = userDict[key].get_password()
            if passwordInput == passwordShelveData:
                password_matched = True
            else:
                print("Password incorrect.")
                db.close()
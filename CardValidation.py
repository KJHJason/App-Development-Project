from datetime import date
# importing date module from the datetime library as I am only using it for getting the current date and to convert a string to a date object to validate the credit card expiry date

# Done by Jason

# helpful resources that was needed to create this credit card validation algorithm: 
# https://www.geeksforgeeks.org/python-converting-all-strings-in-list-to-integers/
# https://allwin-raju-12.medium.com/credit-card-number-validation-using-luhns-algorithm-in-python-c0ed2fac6234
# https://www.youtube.com/watch?v=zMAEI5A6dIA

# Research notes for the different types of credit cards: 
# https://support.cybersource.com/s/article/What-are-the-number-formats-for-different-credit-cards
# https://www.creditcardinsider.com/learn/anatomy-of-a-credit-card/

# # helpful resources for validating the card expiry date:
# https://www.geeksforgeeks.org/comparing-dates-python/
# https://stackoverflow.com/questions/48457027/how-to-compare-two-dates-based-on-month-and-year-only-in-python

# for converting a string or a number into a list of numbers by using map() function
def int_list(numbers):
    return list(map(int, str(numbers)))

# converting the card date to a list of numbers for cardMonth and cardYear using map()
def date_int_list(dateInput):
    cardMonth, cardYear = list(map(int, dateInput.split("/")))
    return cardMonth, cardYear

# function to recognise a card type by the card number
def get_card_type(cardNumber):
    try:
        cardLength = len(cardNumber)
        cardNoList = int_list(cardNumber)
        firstDigit = cardNoList[0] # getting the first digit of the credit card number
        if (firstDigit == 4) and (cardLength == 13 or cardLength == 16):
            # Visa cards starts with the number 4
            return "visa"
        elif (firstDigit == 5 or firstDigit == 2) and (cardLength == 16):
            # MasterCard 5-series starts with the number 5 and MasterCard 2-series starts with the number 2
            return "mastercard"
        elif firstDigit == 3 and cardLength == 15:
            # American Express cards starts with the number 3
            return "american express"
        else:
            print("Card type not accepted!")
            return False
    except:
        print("Card number input must only contain numbers!")
        return False

# main function to validate credit cards using the Luhn's algorithm, aka the modulus 10 or mod 10 algorithm
def validate_card_number(cardNumber):
    try:
        cardNoList = int_list(cardNumber)

        # list slicing to get the list of numbers from the odd indexes starting from the last digits/rightmost of the string
        oddIndexDigits = cardNoList[-1::-2] # starting from the very last digit/rightmost digit, with a stride of 2 digits

        # list slicing to get the list of numbers from the even indexes starting from the last digits/rightmost of the string
        evenIndexDigits = cardNoList[-2::-2] # starting from the 2nd last digit on the rightmost of the list, with a stride of 2 digits

        totalSum = 0 # initialise totalSum to 0
        totalSum += sum(oddIndexDigits) # adds up all the sum from the list of numbers

        # multiplying the numbers by 2 and if the the multiplied numbers have 2 digits, it will add the 2 digits up. E.g. 9 * 2 = 18, since it has 2 digits, it will add up 1 and 8 together to form 9.
        for number in evenIndexDigits:
            number = number * 2
            if number >= 10:
                numberList = int_list(number) # converting the number into a list e.g. the number 10 to [1,0]
                totalSum += sum(numberList) # then adding up the total sum with the sum of the number list elements
            else:
                totalSum += number
        isValid = totalSum % 10
        if isValid == 0:
            return True
        else:
            return False
    except:
        print("Card number input must only contain numbers!") # if the string contained any letters, it will raise a runtime error. Hence, using try and except to handle this error.
        return False

# function to format the card expiry date into a date object
def cardExpiryFormatter(cardDate):
    # try and except to handle user's input for invalid date formats
    try:
        cardMonth, cardYear = date_int_list(cardDate) # converting the string to a list of numbers using one of my functions
        if len(str(cardYear)) == 2: # checking if the year is in YY format
            cardYear = int(str(date.today().year)[:2] + str(cardYear)) # if so, I did some string slicing and concatenation to get YYYY format
        cardExpiryDate = date(cardYear, cardMonth, 1) # making a date object
        return cardExpiryDate
    except:
        print("Invalid date input.")
        return None

# function to convert user's input for the card expiry date to "MM/YYYY" or "M/YYYY" after card expiry date validation
def cardExpiryStringFormatter(cardDate):
    cardMonth, cardYear = cardDate.split("/") # spliting the string into a list of strings
    if cardMonth[0] == "0": # checking if the user's input added a 0 at the front
        cardMonth = cardMonth[1:] # if so it will slice the card month so that the 0 will be ignored
    if len(cardYear) == 2: # checking if the card year format is in "YY"
        cardYear = str(date.today().year)[:2] + cardYear # if so, I did some string slicing and concatenation to get YYYY format
    cardExpiryDateString = cardMonth + "/" + cardYear
    return cardExpiryDateString

# function to validate card's expiry date to check if the card is expired
def validate_expiry_date(cardDate):
    cardDate = cardExpiryFormatter(cardDate)
    print(cardDate)
    if cardDate != None:
        currentDate = date.today().replace(day=1) # getting the current date and replacing the day with 1 for comparison
        if cardDate >= currentDate:
            return True
        else:
            return False
    else:
        return False

# function to validate the card expiry date based on the MM/YYYY or M/YYYY format
def validate_formatted_expiry_date(cardDate):
    currentDate = date.today().replace(day=1) # getting the current date and replacing the day with the number 1
    cardMonth, cardYear = date_int_list(cardDate) # converting the string to a list of numbers using one of my functions
    cardDateList = date(cardYear, cardMonth, 1) # converting the list to a date object
    if cardDateList >= currentDate:
        return True
    else:
        return False
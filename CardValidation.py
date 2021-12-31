import re

# Done by Jason

# helpful resources that was needed to create this credit card validation algorithm: 
# https://www.geeksforgeeks.org/python-converting-all-strings-in-list-to-integers/
# https://allwin-raju-12.medium.com/credit-card-number-validation-using-luhns-algorithm-in-python-c0ed2fac6234
# https://www.youtube.com/watch?v=zMAEI5A6dIA

# Research notes for the different types of credit cards: 
# https://support.cybersource.com/s/article/What-are-the-number-formats-for-different-credit-cards
# https://www.experian.com/blogs/ask-experian/what-is-a-credit-card-cvv/

# helpful resources for validating CVV
# https://www.geeksforgeeks.org/how-to-validate-cvv-number-using-regular-expression/
# https://developers.google.com/edu/python/regular-expressions

# for converting a string or a number into a list of numbers by using map() function
def intList(numbers):
    return list(map(int, str(numbers)))

# main function to validate credit cards using the Luhn's algorithm, aka the modulus 10 or mod 10 algorithm
def validate_card(cardNumber):
    isValid = 1 # initialise the isValid to 1 for the finally block so that it will return False by default if there's an error such as the string containing letters
    try:
        cardNoList = intList(cardNumber)

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
                numberList = intList(number) # converting the number into a list e.g. the number 10 to [1,0]
                totalSum += sum(numberList) # then adding up the total sum with the sum of the number list elements
            else:
                totalSum += number
        isValid = totalSum % 10
    except:
        print("Card number input must only contain numbers!") # if the string contained any letters, it will raise a runtime error. Hence, using try and except to handle this error.
    finally:
        if isValid == 0:
            return True # if the totalSum is a multiple of 10, it is valid and will return True
        else:
            return False

def get_card_type(cardNumber):
    try:
        cardNoList = intList(cardNumber)
        firstDigit = cardNoList[0] # getting the first digit of the credit card number
        if firstDigit == 4:
            # Visa cards starts with the number 4
            return "visa"
        elif firstDigit == 5 or firstDigit == 2:
            # MasterCard 5-series starts with the number 5 and MasterCard 2-series starts with the number 2
            return "mastercard"
        else:
            return False
    except:
        print("Card number input must only contain numbers!")
        return False

def validate_cvv(cardCVV):
    # try and except as in the __init__.py, I validated the sanitise the CVV so if it return False for some reason (empty strings, etc.), it will go to the except block and return False
    try:
        regex = re.compile(r"^[0-9]{3,4}$") # compile the regex so that it does not have to rewrite the regex

        if(re.match(regex, cardCVV)):
            return True
        else:
            return False
    except:
        return False # if the cardCVV variable contained a string with letters, it will return False
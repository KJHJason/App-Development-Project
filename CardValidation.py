# Done by Jason

# helpful resources that was needed to create this credit card validation algorithm: 
# https://www.geeksforgeeks.org/python-converting-all-strings-in-list-to-integers/
# https://allwin-raju-12.medium.com/credit-card-number-validation-using-luhns-algorithm-in-python-c0ed2fac6234
# https://www.youtube.com/watch?v=zMAEI5A6dIA

# Research notes for the different types of credit cards: https://support.cybersource.com/s/article/What-are-the-number-formats-for-different-credit-cards

# for converting a string or a number into a list of numbers by using map() function
def intList(numbers):
    return list(map(int, str(numbers)))

# main function to validate credit cards
def validate_card(cardNumber):
    isValid = 1
    try:
        cardNoList = intList(cardNumber)
        # print(cardNoList)
        oddIndexDigits = cardNoList[-1::-2] # string slicing to get the list of numbers from the odd indexes starting from the last digits/rightmost of the string
        # print("Odd digits:", oddIndexDigits)
        evenIndexDigits = cardNoList[-2::-2] # string slicing to get the list of numbers from the even indexes starting from the last digits/rightmost of the string
        # print("Even digits:", evenIndexDigits)
        totalSum = 0 # initialise checksum to 0
        totalSum += sum(oddIndexDigits) # adds up all the sum from the list of numbers

        # multiplying the numbers by 2 and if the the multiplied numbers have 2 digits, it will add the 2 digits up. E.g. 9 * 2 = 18, since it has 2 digits, it will add up 1 and 8 together to form 9.
        numberList = []
        for number in evenIndexDigits:
            numberList.clear()
            # print("\nOriginal number:", number)
            number = number * 2
            # print("Multiplied number:", number)
            if number >= 10:
                numberList = intList(number) # converting the number into a list
                # print("Added numbers:", numberList)
                # print("Sum up number from list:", sum(numberList))
                totalSum += sum(numberList) # then adding up the total sum with the sum of the number list
            else:
                totalSum += number
        isValid = totalSum % 10
    except:
        print("Card number input must only contain numbers!")
    finally:
        if isValid == 0:
            return True
        else:
            return False

def get_card_type(cardNumber):
    try:
        cardNoList = intList(cardNumber)
        firstDigit = cardNoList[0]
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
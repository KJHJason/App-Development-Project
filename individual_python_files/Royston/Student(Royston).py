from User import User

class Student(User):
    def __init__(self, purchaseID, reviewID, viewed):
        super().__init__(purchaseID, reviewID, viewed)
        
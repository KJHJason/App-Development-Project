'''
User --> Teacher (Object)
  - Courses (Object) 1
    - Name 1
    - Description 1
    - Thumbnail 1
    - Price 1
    - Overall Rating 1
    - Zoom Link --> Zoom Lessons 1
    - Tags (List) 1
    - Ratings (List) 1
      - Rating (Object) 1
        - User_ID 1
        - Title 1
        - Comment 1
        - Ratings 1
    - Schedule/Parts (List) --> Course Structure 1
      - Part (Object) 1
        - Title 1
        - Description 1
        - Thumbnail 1
        - Dates & Times      [[date, time, [user_ID, ...]], [date, time, [user_ID, ...]]] --> Zoom 1
    - Students (List) 1
      - Student User_ID 1
      - Date, Time Selected 1
'''

from Rating import Rating
from CourseParts import ZoomPart, VideoPart

class Course():
    ratings = []    # TO THE PERSON DOING RATINGS: Cache a version, or calculate directly from shelves? Also see its set/get tags.
    def __init__(self, title, description, thumbnail, price, courseType, status):
        self.__title = title
        self.__description = description
        self.__thumbnail = thumbnail
        self.__price = price
        self.__courseType = courseType  # Zoom or Video?
        self.__status = status  # Is course available?
        self.__overallRating = None
        self.__tags = [] #TO THE PERSON DOING TAGS: Would you rather tags be assigned seperately per session, or 1 set of tags for the whole course?
        self.__ratings = []
        self.__schedule = []

    def set_title(self, title):
        self.__name = name
    def get_title(self):
        return self.__name

    def set_description(self, description):
        self.__description = description
    def get_description(self):
        return self.__description

    def set_thumbnail(self, thumbnail):
        self.__thumbnail = thumbnail
    def get_thumbnail(self):
        return self.__thumbnail

    def set_price(self, price):
        self.__price = price
    def get_price(self):
        return self.__price

    def set_courseType(self, courseType):
        self.__courseType = courseType
    def get_courseType(self):
        return self.__courseType

    def set_status(self,status):
        self.__status = status
    def get_status(self):
        return self.__status



    def set_overallRating(self):    # To update the value whenever run
        self.__overallRating = sum(self.__class__.ratings)/len(self.__class__.ratings)
    def get_overallRating(self):
        return self.__overallRating

    def add_tag(self, tag):
        self.__tags.append(tag) # As a value
    def remove_tag(self, tag):
        self.__tags.remove(tag)

    def get_tags(self):
        return self.__tags

    def add_rating(self, userID, title, comment, rating):
        rating = Rating(userID, title, comment, rating)
        self.__ratings.append(rating)
    def remove_rating(self, userID, comment):
        for rating in self.__ratings:
            if rating.get_userID() == userID and rating.get_comment() == comment:
                self.__ratings.remove(rating)
                break

    def get_ratings(self):
        return self.__ratings

    def add_scheduleVideoPart(self, title, description, thumbnail, videoData):
        videoPart = VideoPart(title, description, thumbnail, videoData)
        self.__schedule.append(videoPart)
    def remove_scheduleVideoPart(self, title, description):
        for VideoPart in self.__schedule:
            if VideoPart.get_title() == title and VideoPart.get_description() == description:
                self.__schedule.remove(VideoPart)
                break

    def add_scheduleZoomPart(self, title, description, thumbnail, **kwargs):
        zoomPart = ZoomPart(title, description, thumbnail, kwargs.items())
        self.__schedule.append(zoomPart)
    def remove_scheduleZoomPart(self, title, description):
        for ZoomPart in self.__schedule:
            if VideoPart.get_title() == title and VideoPart.get_description() == description:
                self.__schedule.remove(ZoomPart)


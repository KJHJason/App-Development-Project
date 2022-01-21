'''
User --> Teacher (Object) 1
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

"""Made by Wei Ren"""
"""Edited by Clarence"""

from Rating import Rating
from CourseLesson import ZoomLesson, VideoLesson
from IntegratedFunctions import ellipsis

class Course():
    def __init__(self, courseID,  userID, title, description, thumbnail, status, username):
        self.__courseID = courseID
        self.__userID = userID  # Owner of course
        self.__username = username # username of the course owner
        self.__title = title
        self.__description = description
        self.__thumbnail = thumbnail
        self.__videoPrice = None
        self.__zoomPrice = None
        self.__videoCondition = False # Zoom or Video?
        self.__zoomCondition = False
        self.__status = status  # Is course available?
        self.__overallRating = 0
        self.__tags = [] #TO THE PERSON DOING TAGS: Would you rather tags be assigned seperately per session, or 1 set of tags for the whole course? AND ALSO, PLEASE ADHERE TO THE ATTRIBUTE, tags_viewed, ON THE StudentAndTeacher.py
        self.__ratings = []
        self.__schedule = []
        self.__views = 0

    def set_views(self, views):
        self.__views = views
    def get_views(self):
        return self.__views
    def increase_view(self):
        self.__views += 1

    def set_courseID(self, courseID):
        self.__courseID = courseID
    def get_courseID(self):
        return self.__courseID

    def set_userID(self, userID):
        self.__userID = userID
    def get_userID(self):
        return self.__userID

    def set_username(self, username):
        self.__username = username
    def get_username(self):
        return self.__username

    def set_title(self, title):
        self.__title = title
    def get_title(self):
        return self.__title
    def get_shortTitle(self):
        return ellipsis(self.__title,"Title")

    def set_description(self, description):
        self.__description = description
    def get_description(self):
        return self.__description
    def get_shortDescription(self):
        return ellipsis(self.__description,"Description")

    def set_thumbnail(self, thumbnail):
        self.__thumbnail = thumbnail
    def get_thumbnail(self):
        return self.__thumbnail

    def set_zoomPrice(self, price):
        self.__zoomPrice = price
    def get_zoomPrice(self):
        return self.__zoomPrice

    def set_videoPrice(self, price):
        self.__videoPrice = price
    def get_videoPrice(self):
        return self.__videoPrice

    def switch_videoCondition(self):
        if self.__videoCondition: # if True:
            self.__videoCondition = False
        else:
            self.__videoCondition = True
    def switch_zoomCondition(self):
        if self.__zoomCondition: # if True:
            self.__zoomCondition = False
        else:
            self.__zoomCondition = True
    def get_videoCondition(self):
        return self.__videoCondition
    def get_zoomCondition(self):
        return self.__zoomCondition

    def set_status(self,status):
        self.__status = status
    def get_status(self):
        return self.__status

    def add_tags(self, *args):
        for tag in args:
            self.__tags.append(tag) # As a value
    def remove_tag(self, tag):
        self.__tags.remove(tag)
    def get_tags(self):
        return self.__tags

    def add_rating(self, userID, title, comment, rating):
        rating = Rating(userID, title, comment, rating)
        self.__ratings.append(rating)
    def get_ratings(self):
        return self.__ratings
    def get_averageRating(self):
        total = 0
        for rating in self.__ratings:
            total += int(rating.get_rating())
            return (total/len(self.__ratings))
    def remove_rating(self, userID, comment):
        for rating in self.__ratings:
            if rating.get_userID() == userID and rating.get_comment() == comment:
                self.__ratings.remove(rating)
                break

    def add_scheduleVideoLesson(self, title, description, thumbnail, videoData):
        videoLesson = VideoLesson(title, description, thumbnail, videoData)
        self.__schedule.append(videoLesson)
    def remove_scheduleVideoLesson(self, title, description):
        for VideoLesson in self.__schedule:
            if VideoLesson.get_title() == title and VideoLesson.get_description() == description:
                self.__schedule.remove(VideoLesson)
                break

    def add_scheduleZoomLesson(self, title, description, thumbnail):
        zoomLesson = ZoomLesson(title, description, thumbnail)
        self.__schedule.append(zoomLesson)
    def remove_scheduleZoomLesson(self, title, description):
        for ZoomLesson in self.__schedule:
            if ZoomLesson.get_title() == title and ZoomLesson.get_description() == description:
                self.__schedule.remove(ZoomLesson)

    def get_schedule(self):
        return self.__schedule

    def get_lesson(self, lesson):
        return self.__schedule[int(lesson)]
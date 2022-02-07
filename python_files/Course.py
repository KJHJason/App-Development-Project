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

from .Review import Review
from .CourseLesson import ZoomLesson, VideoLesson
from .IntegratedFunctions import ellipsis
import math

class Course():
    def __init__(self, courseID, courseType, price, tag, title, description, thumbnail, userID):
        self.__courseID = courseID
        self.__userID = userID  # Owner of course
        self.__title = title
        self.__description = description
        self.__thumbnail = thumbnail
        self.__price = price
        self.__course_type = courseType # "Zoom" or "Video"
        self.__tag = tag #  PLEASE ADHERE TO THE ATTRIBUTE, tags_viewed, ON THE Common.py
        self.__views = 0
        self.__review = []
        self.__lessons = [] # list of lessons objects

    """Done by Jason"""

    def set_views(self, views):
        self.__views = views
    def get_views(self):
        return self.__views
    def increase_view(self):
        self.__views += 1

    def add_video_lesson(self, title, description, thumbnail, videoAbsolutePath): 
        self.__lessons.append(VideoLesson(title, description, thumbnail, videoAbsolutePath))
    def add_zoom_lessons(self, title, description, thumbnail, zoomURL, zoomPassword):
        self.__lessons.append(ZoomLesson(title, description, thumbnail, zoomURL, zoomPassword))

    def remove_a_lesson_from_list(self, lessonID):
        lessonsList = self.__lessons
        for lesson in lessonsList:
            if lesson.get_lessonID() == lessonID:
                lessonsList.remove(lesson)
                break
    def set_lesson_list(self, lessonList):
        self.__lessons = lessonList
    def get_lesson_list(self):
        return self.__lessons

    def get_readable_tag(self):
        readableTagDict = {"Programming": "Development - Programming",
                           "Web_Development": "Development - Web Development",
                           "Game_Development": "Development - Game Development",
                           "Mobile_App_Development": "Development - Mobile App Development",
                           "Software_Development": "Development - Software Development",
                           "Other_Development": "Development - Other Development",
                           "Entrepreneurship": "Business - Entrepreneurship",
                           "Project_Management": "Business - Project Management",
                           "BI_Analytics": "Business - Business Intelligence & Analytics",
                           "Business_Strategy": "Business - Business Strategy",
                           "Other_Business": "Business - Other Business",
                           "3D_Modelling": "Design - 3D Modelling",
                           "Animation": "Design - Animation",
                           "UX_Design": "Design - UX Design",
                           "Design_Tools": "Design - Design Tools",
                           "Other_Design": "Design - Other Design",
                           "Digital_Photography": "Photography/Videography - Digital Photography",
                           "Photography_Tools": "Photography/Videography - Photography Tools",
                           "Video_Production": "Photography/Videography - Video Production",
                           "Video_Design_Tools": "Photography/Videography - Video Design Tools",
                           "Other_Photography_Videography": "Photography/Videography - Other Photography/Videography",
                           "Science": "Academics - Science",
                           "Math": "Academics - Math",
                           "Language": "Academics - Language",
                           "Test_Prep": "Academics - Test Prep",
                           "Other_Academics": "Academics - Other Academics"}

        if self.__tag in readableTagDict:
            return readableTagDict[self.__tag]
        else:
            return "Unknown Tag"

    """End of Done by Jason"""

    """Done by Royston"""

    def add_review(self, userID, title, comment, rating):
        self.__review.append(Review(userID, title, comment, rating))
    def get_review(self):
        return self.__review
    def remove_review(self, review): # review is a Rating object
        if review in self.__review:
            self.__review.remove(review)
        else:
            return False
    
    """End of Done by Royston"""

    """Done by Wei Ren"""

    def set_courseID(self, courseID):
        self.__courseID = courseID
    def get_courseID(self):
        return self.__courseID

    def set_userID(self, userID):
        self.__userID = userID
    def get_userID(self):
        return self.__userID

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

    def set_price(self, price):
        self.__price = price
    def get_price(self):
        return self.__price

    def set_course_type(self, courseType):
        self.__course_type = courseType
    def get_course_type(self):
        return self.__course_type

    def set_status(self,status):
        self.__status = status
    def get_status(self):
        return self.__status

    def set_tag(self, tag):
        self.__tag = tag
    def get_tag(self):
        return self.__tag

    def get_averageRating(self):
        total = 0
        for review in self.__review:
            total += int(review.get_rating())
        return math.floor(total/len(self.__review))

    # def add_VideoLesson(self, title, description, thumbnail, videoData):
    #     videoLesson = VideoLesson(title, description, thumbnail, videoData)
    #     self.__schedule.append(videoLesson)
    # def remove_scheduleVideoLesson(self, title, description):
    #     for VideoLesson in self.__schedule:
    #         if VideoLesson.get_title() == title and VideoLesson.get_description() == description:
    #             self.__schedule.remove(VideoLesson)
    #             break

    # def add_scheduleZoomLesson(self, title, description, thumbnail):
    #     zoomLesson = ZoomLesson(title, description, thumbnail)
    #     self.__schedule.append(zoomLesson)
    # def remove_scheduleZoomLesson(self, title, description):
    #     for ZoomLesson in self.__schedule:
    #         if ZoomLesson.get_title() == title and ZoomLesson.get_description() == description:
    #             self.__schedule.remove(ZoomLesson)

    # def get_schedule(self):
    #     return self.__schedule

    # def get_lesson(self, lesson):
    #     return self.__schedule[int(lesson)]

    """End of Done by Wei Ren"""
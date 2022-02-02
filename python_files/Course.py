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

from .Rating import Rating
from .CourseLesson import ZoomLesson, VideoLesson
from .IntegratedFunctions import ellipsis

class Course():
    def __init__(self, courseID, courseType, price, tag, title, description, thumbnail, userID):
        self.__courseID = courseID
        self.__userID = userID  # Owner of course
        self.__title = title
        self.__description = description
        self.__thumbnail = thumbnail
        self.__price = price
        self.__course_type = courseType # "Zoom" or "Video"
        self.__overallRating = 0
        self.__tag = tag #  PLEASE ADHERE TO THE ATTRIBUTE, tags_viewed, ON THE Common.py
        self.__ratings = []
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
        courseTag = self.__tag
        if courseTag == "Programming":
            return "Development - Programming"
        elif courseTag == "Web_Development":
            return "Development - Web Development"
        elif courseTag == "Game_Development":
            return "Development - Game Development"
        elif courseTag == "Mobile_App_Development":
            return "Development - Mobile App Development"
        elif courseTag == "Software_Development":
            return "Development - Software Development"
        elif courseTag == "Other_Development":
            return "Development - Other Development"
        elif courseTag == "Entrepreneurship":
            return "Business - Entrepreneurship"
        elif courseTag == "Project_Management":
            return "Business - Project Management"
        elif courseTag == "BI_Analytics":
            return "Business - BI Analytics"
        elif courseTag == "Business_Strategy":
            return "Business - Business Strategy"
        elif courseTag == "Other_Business":
            return "Business - Other Business"
        elif courseTag == "3D_Modelling":
            return "Design - 3D Modelling"
        elif courseTag == "Animation":
            return "Design - Animation"
        elif courseTag == "UX_Design":
            return "Design - UX Design"
        elif courseTag == "Design_Tools": 
            return "Design - Design Tools"
        elif courseTag == "Other_Design":
            return "Design - Other Design"
        elif courseTag == "Digital_Photography":
            return "Photography/Videography - Digital Photography"
        elif courseTag == "Photography_Tools":
            return "Photography/Videography - Photography Tools"
        elif courseTag == "Video_Production":
            return "Photography/Videography - Video Production"
        elif courseTag == "Video_Design_Tools":
            return "Photography/Videography - Video Design Tools"
        elif courseTag == "Other_Photography_Videography":
            return "Photography/Videography - Other Photography/Videography"
        elif courseTag == "Science":
            return "Academics - Science"
        elif courseTag == "Math":
            return "Academics - Math"
        elif courseTag == "Language":
            return "Academics - Language"
        elif courseTag == "Test_Prep":
            return "Academics - Test Prep"
        elif courseTag == "Other_Academics":
            return "Academics - Other Academics"
        else:
            return "Unknown Tag"

    """End of Done by Jason"""

    """Done by Royston"""

    def add_review(self, userID, title, comment, rating):
        self.__review.append(Rating(userID, title, comment, rating))
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
            return (total/len(self.__review))

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
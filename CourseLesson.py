"""Made by Wei Ren"""
"""Edited by Clarence"""
class Lesson():
    def __init__(self, title, description, thumbnail):
        self.__title = title
        self.__description = description
        self.__thumbnail = thumbnail

    def set_title(self, title):
        self.__title = title
    def get_title(self):
        return self.__title

    def set_description(self, description):
        self.__description = description
    def get_description(self):
        return self.__description

    def set_thumbnail(self, thumbnail):
        self.__thumbnail = thumbnail
    def get_thumbnail(self):
        return self.__thumbnail


# Video Data
class VideoLesson(Lesson):
    def __init__(self, title, description, thumbnail, videoData):
        super().__init__(title, description, thumbnail)
        self.__videoData = videoData

    def set_videoData(self, videoData):
        self.__videoData = videoData
    def get_videoData(self):
        return self.__videoData

# Zoom Link --> To be changed
# Different timings for different students for different courses
class ZoomLesson(Lesson):
    def __init__(self, title, description, thumbnail):
        super().__init__(title, description, thumbnail)
        self.__timings = []
        self.__userTimings = {}

    def set_timing(self, date, time):
        self.__timings.append([date, time])
    def remove_timing(self, date, time):
        self.__timings.remove([date, time])

    def get_timings(self):
        return self.__timings

    def add_user_timing(self, userID, date, time):
        for timing in self.__timings:
            if timing == [date, time]:
                self.__userTimings[userID] = {"date":timing[0],"time":timing[1]}  # As a way to index the timing; a format of [date, time, [userID, ...]] cannot be easily removed
                break                                # Instead, {userID:[date, time]}
    def remove_user_timing(self, userID):
        self.__userTimings.pop(userID)

    def get_user_timing(self, userID):  # [date, time]
        return self.__userTimings[userID]

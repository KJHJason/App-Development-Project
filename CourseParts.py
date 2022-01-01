class Part():
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
class VideoPart(Part):
    def __init__(self, title, description, thumbnail, videoData):
        super().__init__(title, description, thumbnail)
        self.__videoData = videoData

    def set_videoData(self, videoData):
        self.__videoData = videoData
    def get_videoData(self):
        return self.__videoData

# Zoom Link --> To be changed
# Different timings for different students for different courses
class ZoomPart(Part):
    def __init__(self, title, description, thumbnail, **kwargs):
        super().__init__(title, description, thumbnail)
        self.__timings = []
        self.__userTimings = {}
        for date, time in kwargs.items():
            self.__timings.append([date, time])

    def set_timings(self, **kwargs):
        for date, time in kwargs.items():
            self.__timings.append([date, time])
    def remove_timings(self, **kwargs):
        for date, time in kwargs.items():
            self.__timings.remove([date, time])

    def get_timings(self):
        return self.__timings

    def add_user_timing(self, userID, date, time):
        for index in range(self.__timings):
            if self.__timings[index] == [date, time]:
                self.__userTimings[userID] = index  # As a way to index the timing; a format of [date, time, [userID, ...]] cannot be easily removed
                break
    def remove_user_timing(self, userID):
        self.__userTimings.pop(userID)

    def get_user_timing(self, userID):  # [date, time]
        return self.__userTimings[userID]


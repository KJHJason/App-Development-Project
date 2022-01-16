class ViewsAndRecommendations:
    def __init__(self):
        self.__viewed = {}
        self.__tags_viewed = {"Programming": 0, 
                              "Web Development": 0,
                              "Game Development": 0,
                              "Mobile App Development": 0,
                              "Software Development": 0,
                              "Other Development": 0,
                              "Entrepreneurship": 0,
                              "Project Management": 0,
                              "BI & Analytics": 0,
                              "Business Strategy": 0,
                              "Other Business": 0,
                              "3D Modelling": 0,
                              "Animation": 0,
                              "UX Design": 0,
                              "Design Tools": 0,
                              "Other Design": 0,
                              "Digital Photography": 0,
                              "Photography Tools": 0,
                              "Video Production": 0,
                              "Video Design Tools": 0,
                              "Other Photography/Videography": 0,
                              "Science": 0,
                              "Math": 0,
                              "Language": 0,
                              "Test Prep": 0,
                              "Other Academics": 0}
    
    def set_viewed(self, viewedDict):
        self.__viewed = viewedDict
    def set_tags_viewed(self, tagsDict):
        self.__tags_viewed = tagsDict

    def get_viewed(self):
        return self.__viewed
    def get_tags_viewed(self):
        return self.__tags_viewed

    def change_no_of_view(self, seenTag):
        if seenTag in self.__tags_viewed:
            self.__tags_viewed[seenTag] += 1
        else:
            print("No such tag found.")
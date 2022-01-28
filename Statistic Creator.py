def create_statistic_dict(years, statisticTypes):
    if type(years) != list:
        raise ValueError("Years must be in a list, " + type(years) + "entered.")
    elif type(statisticTypes) != list:
        raise ValueError("Years must be in a list, " + type(statisticTypes) + "entered.")

    statisticDict = {}
    timeDict = {'1:00':None,'2:00':None,'3:00':None,'4:00':None,'5:00':None,'6:00':None,'7:00':None,'8:00':None,'9:00':None,'10:00':None,'11:00':None,'12:00':None,'13:00':None,'14:00':None,'15:00':None,'16:00':None,'17:00':None,'18:00':None,'19:00':None,'20:00':None,'21:00':None,'22:00':None,'23:00':None,'24:00':None}
    months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    dates = ['1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th','11th','12th','13th','14th','15th','16th','17th','18th','19th','20th','21st','22nd','23rd','24th','25th','26th','27th','28th','29th','30th','31st']

    for statisticType in statisticTypes:
        for year in years:
            yearDict = {}
            monthDict = {}
            for month in months:
                dateDict = {}
                if month in ['January','March','May','July','August','November']:
                    length = 31
                elif month in ['April','June','September','October','December']:
                    length = 30
                elif month == "February" and year % 4 == 0 and not (year % 100 == 0 and year % 400 != 0):
                    length = 29
                else:
                    length = 28

                for dateIndex in range(length):
                    dateDict[dates[dateIndex]] = timeDict

                monthDict[month] = dateDict
            yearDict[year] = monthDict
        statisticDict[type] = yearDict
    return statisticDict

print(create_statistic_dict([2020,2021,2022,2023],['Sales','Profits','Signups']))

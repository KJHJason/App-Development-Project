maxPages = 10 # maximum page number
paginationList = []

pageNum = 6 # current page number of the user

if maxPages <= 5:
    pageCount = 0
    for i in range(maxPages):
        pageCount += 1
        paginationList.append(pageCount)
    print(paginationList)
else:
    currentFromMax = maxPages - pageNum
    if pageNum < 4:
        paginationList.append(1)
        paginationList.append(2)     
        paginationList.append(3)
        paginationList.append(4)
        paginationList.append(5)
    elif currentFromMax <= 2:
        paginationList.append(maxPages - 4)
        paginationList.append(maxPages - 3)     
        paginationList.append(maxPages - 2)
        paginationList.append(maxPages - 1)
        paginationList.append(maxPages )
    else:
        paginationList.append(pageNum - 2)
        paginationList.append(pageNum - 1 )     
        paginationList.append(pageNum)
        paginationList.append(pageNum + 1)
        paginationList.append(pageNum + 2)


for key in paginationList:
    print(key)
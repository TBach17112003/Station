from datetime import datetime,timedelta

def getDateFormat(datimeTime : datetime):
    # print(now)
    ISODate_String = datimeTime.strftime('%Y-%m-%d')
    # print(ISODate_String)
    return ISODate_String

def getSevenDaysAgo():
    now = datetime.now()
    DateList = [now]
    for i in range(1,7):
        DateList.append(now-timedelta(i))
    return DateList
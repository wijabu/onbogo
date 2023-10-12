from datetime import datetime, timedelta, date

def isTodayThursday(num):
    thisDate = date.today()
    thisDay = date.today().strftime('%A')
    targetDay = "Thursday"
    prevDate = thisDate - timedelta(days=5)
    prevDay = prevDate.strftime('%A')
    formattedDate = ""

    if thisDay == targetDay:
        formattedDate = thisDate.strftime('%y%m%d')
        print(thisDay)
        return formattedDate
    else:

        if (num < 7):
            print(num)

            prevDate = thisDate - timedelta(days=num)
            prevDay = prevDate.strftime('%A')
            
            if prevDay == targetDay:
                print(prevDate)
                print(prevDay)
                formattedDate = prevDate.strftime('%y%m%d')
                return formattedDate
            else:
                num += 1
                isTodayThursday(num);


if __name__ == "__main__":
    isTodayThursday(1)
from datetime import datetime, timedelta, date

formattedDate = ""

def isTodayThursday(num):
    thisDate = date.today()
    thisDay = date.today().strftime('%A')
    targetDay = "Thursday"
    prevDate = thisDate - timedelta(days=5)
    prevDay = prevDate.strftime('%A')
    global formattedDate

    if thisDay == targetDay:
        formattedDate = thisDate.strftime('%y%m%d')
        print(thisDay)
        print(f"formattedDate: {formattedDate} - {num}")
        return formattedDate
    else:

        if (num < 7):
            print(num)

            prevDate = thisDate - timedelta(days=num)
            prevDay = prevDate.strftime('%A')
            
            if prevDay == targetDay:
                print(f"prevDay: {prevDay}")
                print(f"prevDate: {prevDate}")
                formattedDate = prevDate.strftime('%y%m%d')
                print(f"formattedDate: {formattedDate} - {num}")
            else:
                num += 1
                isTodayThursday(num);
    
    return formattedDate


if __name__ == "__main__":
    isTodayThursday(1)
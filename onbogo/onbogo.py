#!usr/bin/env python3

import logging

from flask import jsonify

from . import notify
from . import sales
from . import date
from . import db

logging.basicConfig(
    # filename='myLogFile.txt', # use this to write logs to specified file
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# def run(user):
#     try:
#         store_id = user["my_store"]["store_id"]
#         logging.debug(f"store_id: {store_id}")
        
#         if store_id:
#             # check if today is Thursday; if not, decrement until date found for most recent Thursday
#             formattedDate = date.isTodayThursday(1)

#             if formattedDate is None:
#                 logging.debug(f"formattedDate is set to 'None'")
#             elif formattedDate == "":
#                 logging.debug(f"formattedDate is empty string")
#             else:
#                 logging.debug(f"formattedDate: {formattedDate}")
            
#             # call URL for each page of weekly ad + build list of user's sale items
#             page = 1;
#             pages = sales.get_pages(user, page, formattedDate)
#             logging.debug(f"Pages count: {pages}")
            
#             # call each page in sales ad to compare against user's grocery list
#             for page in range(1, pages+1):
#                 my_sale_items = sales.find_sales(user, page, formattedDate)


def run(user):
    try:
        store_id = user["my_store"]["store_id"]
        logging.debug(f"store_id: {store_id}")
        
        if store_id:
            # scrape weekly_ad link from main page
            weekly_ad = sales.get_weekly_ad(store_id)
            
            # call URL for each page of weekly ad + build list of user's sale items
            pages = sales.get_pages(user, weekly_ad)
            logging.debug(f"Pages count: {pages}")
            
            # call each page in sales ad to compare against user's grocery list
            # page = 1
            for page in range(1, pages+1):
                my_sale_items = sales.find_sales(user, page, weekly_ad)

            logging.debug(f"my_sale_items for {user['username']}: {my_sale_items}")
            
            if my_sale_items == []:
                alert_msg = f"Hi {user['username']}, No sale items matching your list this week."
            else:
                # generate single list for titles, deals, and info of sale items
                list_items = []
                msg_items = []
                for item in my_sale_items:
                    list_items.append(list(item.values()))
                
                for item in list_items:
                    for val in item: 
                        msg_items.append(val)

                # add line break into list every nth element to break up mobile notification message
                for i in range (0,len(msg_items)):
                    msg_items.insert(i*4,"\n")

                alert_template = f"Hello, {user['username']}, here are your sales from onbogo.onrender.com\n" + "\n".join(msg_items)
                
                if len(alert_template) < 550:
                    alert_msg = alert_template.strip()
                else:
                    alert_msg = f"Hello, {user['username']}, here are your sales...\n" + "\n*****\nNOTE: This is an incomplete list. To see all sales, visit onbogo.onrender.com \n***** " + "\n".join(msg_items[:28])

            # send notification(s) to user(s)    
            notify.send_alert(alert_msg, user=user)
            
            logging.debug(f"Notifications sent to {user['username']}!")
            logging.debug(f"Notifications length: {len(alert_msg)}!")
            # logging.debug(alert_msg)

            return my_sale_items
        
        else:
            print(f"No store saved to profile for user: {user['_id']}. Unable to find sales.")
        
    except:
        return jsonify("ERROR: Unable to run app with this user. Verify required data found in user profile.", status=400)


def run_schedule():
    # ALL_USERS = db.users.find({"zip":"32789"})
    ALL_USERS = db.users.find({})

    print(ALL_USERS)

    for user in ALL_USERS:
        if user["my_store"]["store_id"] and user['favs']:
            run(user)


if __name__ == "__main__":
    pass

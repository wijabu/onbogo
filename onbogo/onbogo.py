#!usr/bin/env python3

import logging

from flask import jsonify

from . import notify
from . import sales
from . import db


def run(user):
    try:
        store_id = user["my_store"]["store_id"]
        
        if store_id:
            sale_id = user["sale_id"]
            sale_url = f"https://accessibleweeklyad.publix.com/PublixAccessibility/BrowseByListing/ByCategory/?ListingSort=8&StoreID={store_id}&CategoryID={sale_id}"
            
            my_sale_items = sales.find_sales(sale_url, user=user)

            logging.debug(f"my_sale_items for {user['username']}: {my_sale_items}")
            
            if my_sale_items == []:
                alert_msg = f"Hi {user['username']}, No sale items matching your list this week."
            else:
                # msg_items = [];
                # msg_deals = [];
                # for item in my_sale_items:
                #     msg_items.append(item["title"])
                #     msg_deals.append(item["deal"])

                # for i in range(len(my_sale_items)):
                #     msg_items.append(my_sale_items[i]["title"], my_sale_items[i]["deal"])


                msg_titles = [i['title'] for i in my_sale_items]
                msg_deals = [i['deal'] for i in my_sale_items]

                sale_keys = ["title", "deal"]

                # for i in range(len(my_sale_items)):
                #     msg_items = list(map(my_sale_items[i].get, sale_keys))
                
                # msg_items = [next(iter(i.values())) for i in my_sale_items]

                # items_list = list(my_sale_items[i].values())

                # for j in range(len(items_list)):
                #     for k in range(len(j)):
                #         msg_items = list(j)

                list_items = []
                for item in my_sale_items:
                    
                    list_items.append(list(item.values()))
                    print(list(item.values()))
                    # msg_items.append(my_sale_items[i].values())
                    msg_items = list_items

                print(f"msg_items: {msg_titles}")

                alert_msg = f"Hello, {user['username']}, here are your sales...\n\n" + "\n".join(msg_titles)
                
            notify.send_alert(alert_msg, user=user)
            
            print(f"Notifications sent to {user['username']}!")

            return my_sale_items
        else:
            print(f"No store saved to profile for user: {user['_id']}. Unable to find sales.")
        
    except:
        return jsonify("ERROR: Unable to run app with this user. Verify required data found in user profile.", status=400)


def run_schedule():
    ALL_USERS = db.users.find({})

    for user in ALL_USERS:
        if user["my_store"]["store_id"] and user['favs']:
            run(user)


if __name__ == "__main__":
    pass

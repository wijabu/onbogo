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
                alert_msg = "No sale items matching your list this week."
            else:
                alert_msg = "\n".join(my_sale_items)
                
            notify.send_alert(alert_msg, user=user)
            
            print(f"Notifications sent to {user['username']}!")
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

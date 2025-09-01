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


def run(user):
    try:
        store_id = user["my_store"]["store_id"]
        logging.debug(f"store_id: {store_id}")
        
        if store_id:
            # launch Selenium + go to weekly ad
            driver = sales.get_weekly_ad(store_id)
            if not driver:
                logging.error("No weekly ad found for store %s", store_id)
                return jsonify(error="No weekly ad available for this store."), 404

            # detect total pages
            pages = sales.get_pages(user, driver)
            logging.debug(f"Pages count: {pages}")
            
            # gather sale items across all pages
            all_sale_items = []
            for page in range(1, pages + 1):
                page_items = sales.find_sales(user, page, driver)
                all_sale_items.extend(page_items)

            logging.debug(f"my_sale_items for {user['username']}: {all_sale_items}")
            
            if not all_sale_items:
                alert_msg = f"Hi {user['username']}, No sale items matching your list this week."
            else:
                # flatten items into a message
                list_items = [list(item.values()) for item in all_sale_items]
                msg_items = [val for sub in list_items for val in sub]

                # insert line breaks for readability
                for i in range(0, len(msg_items)):
                    msg_items.insert(i * 4, "\n")

                alert_template = (
                    f"Hello, {user['username']}, here are your sales from onbogo.onrender.com\n"
                    + "\n".join(msg_items)
                )
                alert_msg = alert_template.strip()

            # send notification(s)
            notify.send_alert(alert_msg, user=user)
            
            logging.debug(f"Notifications sent to {user['username']}!")
            logging.debug(f"Notifications length: {len(alert_msg)}!")

            return all_sale_items, 200
        
        else:
            logging.warning(f"No store saved to profile for user: {user['_id']}. Unable to find sales.")
            return jsonify(error="No store found for this user."), 400

    except Exception as e:
        logging.error(f"App run error: {e}", exc_info=True)
        return jsonify(error="Unable to run app with this user. Verify required data found in user profile."), 400

    finally:
        # make sure Selenium driver closes even on error
        try:
            driver.quit()
            logging.debug("Selenium driver closed.")
        except Exception:
            pass


def run_schedule():
    ALL_USERS = db.users.find({})
    logging.debug(f"Running schedule for {ALL_USERS.count()} users")

    for user in ALL_USERS:
        if user.get("my_store", {}).get("store_id") and user.get("favs"):
            run(user)


if __name__ == "__main__":
    pass

#!usr/bin/env python3

import logging
from flask import jsonify

from . import notify
from . import sales
from . import date
from . import db

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def run(user):
    try:
        store_id = user.get("my_store", {}).get("store_id")
        logging.debug(f"store_id: {store_id}")

        if not store_id:
            logging.warning(f"No store saved to profile for user: {user.get('_id')}")
            return jsonify(error="No store saved to profile for this user."), 404

        # scrape weekly ad using Selenium
        weekly_ad = sales.get_weekly_ad(store_id)
        if not weekly_ad:
            logging.error("No weekly ad found for store %s", store_id)
            return jsonify(error="No weekly ad available for this store."), 404

        logging.debug(f"weekly_ad: {weekly_ad}")

        # determine number of pages in weekly ad
        pages = sales.get_pages(user, weekly_ad)
        logging.debug(f"Pages count: {pages}")

        # accumulate sale items across all pages
        my_sale_items = []
        for page in range(1, pages + 1):
            page_items = sales.find_sales(user, page, weekly_ad)
            if page_items:
                my_sale_items.extend(page_items)

        logging.debug(f"my_sale_items for {user.get('username')}: {my_sale_items}")

        # generate notification message
        if not my_sale_items:
            alert_msg = f"Hi {user.get('username')}, no sale items matching your list this week."
        else:
            msg_items = []
            for item in my_sale_items:
                msg_items.extend(item.values())

            # insert line breaks for mobile readability every 4 items
            for i in range(len(msg_items)):
                if i % 4 == 0:
                    msg_items.insert(i, "\n")

            alert_msg = f"Hello, {user.get('username')}, here are your sales from onbogo.onrender.com\n" + "\n".join(msg_items)

        # send notification
        notify.send_alert(alert_msg, user=user)
        logging.debug(f"Notifications sent to {user.get('username')}! Length: {len(alert_msg)}")

        return jsonify(my_sale_items)  # always JSON-serializable

    except Exception as e:
        logging.exception("Unable to run app with this user.")
        return jsonify(error=f"Unable to run app with this user: {e}"), 400


def run_schedule():
    ALL_USERS = db.users.find({})
    for user in ALL_USERS:
        if user.get("my_store", {}).get("store_id") and user.get("favs"):
            run(user)


if __name__ == "__main__":
    pass

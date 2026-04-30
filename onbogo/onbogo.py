#!usr/bin/env python3

import logging

from . import notify
from . import sales
from . import search
from . import date
from . import db

logging.basicConfig(
    # filename='myLogFile.txt', # use this to write logs to specified file
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def run(user):
    """Return {"items": [...matched sale items...], "misses": [...favs with no hits...]}."""
    try:
        store_id = user["my_store"]["store_id"]
        logging.debug(f"store_id: {store_id}")

        if not store_id:
            logging.warning(f"No store saved to profile for user: {user['_id']}. Unable to find sales.")
            return {"items": [], "misses": []}

        all_sale_items = sales.get_weekly_ad(store_id, user)
        favs = [f for f in user.get("favs", []) if f]

        my_sale_items = []
        misses = []
        seen_titles = set()

        for fav in favs:
            hits = [item for item in all_sale_items if search.matches(fav, item["title"])]
            if not hits:
                misses.append(fav)
                continue
            for item in hits:
                if item["title"] not in seen_titles:
                    my_sale_items.append(item)
                    seen_titles.add(item["title"])

        logging.debug(f"my_sale_items for {user['username']}: {len(my_sale_items)} hits, {len(misses)} misses")

        if not my_sale_items:
            alert_msg = f"Hi {user['username']}, no sale items matching your list this week."
        else:
            lines = []
            for item in my_sale_items:
                lines.append(f"\n{item['title']}")
                lines.append(item['deal'])
                lines.append(item['price_info'])
                lines.append(item['valid_dates'])
            alert_msg = f"Hello, {user['username']}, here are your sales from onbogo.onrender.com\n" + "\n".join(lines)
            if misses:
                alert_msg += f"\n\nNo sales this week for: {', '.join(misses)}"

        notify.send_alert(alert_msg, user=user)
        logging.debug(f"Notifications sent to {user['username']}!")
        logging.debug(f"Notifications length: {len(alert_msg)}!")

        return {"items": my_sale_items, "misses": misses}

    except Exception as e:
        logging.error(f"App run error: {e}", exc_info=True)
        return {"items": [], "misses": []}


def run_schedule():
    """Weekly Thursday job — alert every user with a saved store and a non-empty fav list."""
    logging.info("Scheduler fired: starting weekly run_schedule")
    try:
        total = db.users.count_documents({})
        eligible = list(db.users.find({
            "my_store.store_id": {"$exists": True, "$ne": ""},
            "favs": {"$exists": True, "$ne": []},
        }))
        logging.info(f"run_schedule: {total} total users, {len(eligible)} eligible for alerts")

        successes = 0
        failures = 0
        for user in eligible:
            try:
                run(user)
                successes += 1
            except Exception as e:
                failures += 1
                logging.error(
                    f"run_schedule: failed for user {user.get('username', user.get('_id'))}: {e}",
                    exc_info=True,
                )
        logging.info(f"run_schedule complete: {successes} succeeded, {failures} failed")
    except Exception as e:
        logging.error(f"run_schedule top-level failure: {e}", exc_info=True)


if __name__ == "__main__":
    pass

#!/usr/bin/env python3

import bs4
import requests
import logging
import json
from unidecode import unidecode

logging.basicConfig(
    # filename='myLogFile.txt', # use this to write logs to specified file
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# logging.disable(logging.CRITICAL) # this code disables logging for the program

with open(
    "../profile.json", "r"
) as profile:  # will be replaced in the future with user-created profiles
    profile = json.load(profile)


product_search_list = profile.get("product_search_list")
store_id = profile.get("store_id")
sale_id = profile.get("sale_id")
sale_url = f"https://accessibleweeklyad.publix.com/PublixAccessibility/BrowseByListing/ByCategory/?ListingSort=8&StoreID={store_id}&CategoryID={sale_id}"

all_sale_items = []
my_sale_items = []


def get_ad(sale_url):
    global all_sale_items
    all_sale_items.clear()
    logging.debug("Initial Items in all_sale_items: %s" % (all_sale_items))
    res = requests.get(sale_url)
    res.raise_for_status  # raise an exception if there is a problem downloading URL text

    soup = bs4.BeautifulSoup(res.text, features="html.parser")
    titles = soup.select("h2", {"class": "ellipsis_text"})

    logging.debug("Start of products search")

    for i in range(len(titles)):
        title = titles[i].text.strip()
        # logging.debug(
        #     "item %s is %s" % (i, title)
        # )  # will log all items found on weekly ad
        all_sale_items.append(title)

    return all_sale_items


def find_my_sale():
    global my_sale_items
    my_sale_items.clear()
    logging.debug("Intitial Items in my_sale_items: %s" % (my_sale_items))
    for i in range(len(all_sale_items)):
        for j in range(len(product_search_list)):
            if product_search_list[j].upper() in all_sale_items[i].upper():
                item = unidecode(all_sale_items[i])
                my_sale_items.append(str(item))
                # logging.debug("Current Items in my_sale_items: %s" % (my_sale_items))
    if my_sale_items == []:
        print("No items found matching search criteria")
    else:
        logging.debug("Current Items in my_sale_items: %s" % (my_sale_items))
    return my_sale_items


if __name__ == "__main__":
    get_ad(sale_url)
    find_my_sale()

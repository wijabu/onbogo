#!/usr/bin/env python3

import bs4
import requests
import logging
from unidecode import unidecode

from .models import User

logging.basicConfig(
    # filename='myLogFile.txt', # use this to write logs to specified file
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# logging.disable(logging.CRITICAL) # this code disables logging for the program


def find_sales(sale_url, user, all_sale_items=[]):
    favs = user["favs"]
    email = user["email"]    
    my_sale_items = []

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
        if not title in all_sale_items:
            all_sale_items.append(title)
    
    # logging.debug(f"All Sale Items This Week: {all_sale_items}")
    
    for i in range(len(all_sale_items)):
        for j in range(len(favs)):
            if favs[j].upper() in all_sale_items[i].upper():
                item = unidecode(all_sale_items[i])
                if not item in my_sale_items:
                    my_sale_items.append(str(item))
                logging.debug(f"Updated Items in {user['username']}'s my_sale_items: {my_sale_items}")
    
    if my_sale_items == []:
        print("No items found matching search criteria")
    else:
        logging.debug(f"Sale items found matching {user['username']}'s favs: {my_sale_items}")

    
    return my_sale_items


if __name__ == "__main__":
    find_sales()
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


def find_sales(sale_url, user, all_sale_items=[], all_deals=[]):
    favs = user["favs"]
    email = user["email"]    
    my_sale_items = []

    res = requests.get(sale_url)
    res.raise_for_status  # raise an exception if there is a problem downloading URL text

    soup = bs4.BeautifulSoup(res.text, features="html.parser")
    
    titles = soup.select("div > h2", {"class": "action-elide.title"})
    
    deal_divs = soup.select('div.action-elide.deal')

    for deal in deal_divs:
        deals = deal.find("span", {"class": "ellipsis_text"})
        for deal in deals:
            all_deals.append(deal)

    logging.debug("Start of products search")

    for i in range(len(titles)):
        title = titles[i].text.strip()
        deal = all_deals[i].upper()

        item = {
            "title":title,
            "deal":deal
        }

        # logging.debug(
        #     f"item {i} is {title}"
        # )  # will log all items found on weekly ad
        
        if not item in all_sale_items:
            all_sale_items.append(item)
            # print(all_sale_items)
    
    logging.debug(f"{len(all_sale_items)} Sale Items Found This Week: {all_sale_items}")
    
    for i in range(len(all_sale_items)):
        for j in range(len(favs)):
            if favs[j].upper() in all_sale_items[i]["title"].upper():
                my_item = unidecode(all_sale_items[i]["title"])
                my_deal = all_sale_items[i]["deal"]
                
                new_item = {
                    "title": str(my_item),
                    "deal": str(my_deal)
                }

                if not new_item in my_sale_items:
                    my_sale_items.append(new_item)
                
                logging.debug(f"Updated Items in {user['username']}'s my_sale_items: {my_sale_items}")
    
    if my_sale_items == []:
        print("No items found matching search criteria")
    else:
        logging.debug(f"Sale items found matching {user['username']}'s favs: {my_sale_items}")

    
    return my_sale_items


if __name__ == "__main__":
    find_sales()
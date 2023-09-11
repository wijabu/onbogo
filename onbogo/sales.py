#!/usr/bin/env python3

import bs4
import requests
import logging
from unidecode import unidecode

logging.basicConfig(
    # filename='myLogFile.txt', # use this to write logs to specified file
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# logging.disable(logging.CRITICAL) # this code disables logging for the program

user = {
    "username":"barry",
    "email":"barry@gmail.com",
    "sale_id":5232540,
    "my_store":{"store_id":2501054},
    "favs":["bacon","oatmilk","Sweet Baby","wine","all"]
    }

all_titles = []
all_deals = []
all_info = []
all_sale_items = []
my_sale_items = []

store_id = user["my_store"]["store_id"]

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}


def get_pages(user):
    store_id = user["my_store"]["store_id"]
    sale_url = f"https://accessibleweeklyad.publix.com/PublixAccessibility/BrowseByPage/Index/?StoreID={store_id}&PromotionCode=Publix-230907"
    
    res = requests.get(sale_url, headers=headers)
    res.raise_for_status  # raise an exception if there is a problem downloading URL text
    soup = bs4.BeautifulSoup(res.text, features="html.parser")

    pages_div = soup.select('div.paginationUnitMobile.includeInMobile')
    
    for page in pages_div:
        page_count = page.find("div", {"class": "pageXofY"}).text.strip()
        page_list = page_count.split()
        pages = page_list[-1]

        print(f"pages: {pages}")
        return pages


def find_sales(user, page):    
    store_id = user["my_store"]["store_id"]
    favs = user["favs"]
    email = user["email"]
    

    sale_url = f"https://accessibleweeklyad.publix.com/PublixAccessibility/BrowseByPage/Index/?StoreID={store_id}&PromotionCode=Publix-230907&PageNumber={page}"

    res = requests.get(sale_url, headers=headers)
    res.raise_for_status  # raise an exception if there is a problem downloading URL text
    soup = bs4.BeautifulSoup(res.text, features="html.parser")

    # find div for product cards
    cards = soup.select('div.unitB')
    # logging.debug(f"cards found: {len(cards)}")

    # strip product title and append to array
    for card in cards:
        title_element = card.find("div", class_="title").text.strip()
        all_titles.append(title_element)
        
        deal_element = card.find("div", class_="deal").text.strip()
        all_deals.append(deal_element)
        
        if card.find("div", class_="additionalDealInfo"):
            info_element = card.find("div", class_="additionalDealInfo").text.strip()
            all_info.append(info_element)
        else:
            info_element = ""
            all_info.append(info_element)

    # build list of all_sale_items
    for i in range(len(all_titles)):
        title = all_titles[i]
        deal = all_deals[i].upper()
        info = all_info[i].upper()

        item = {
            "title":title.replace("'",""),
            "deal":deal,
            "info":info
        }

        # logging.debug(
        #     f"item {i} is {title}"
        # )  # will log all items found on weekly ad
        
        if not item in all_sale_items:
            all_sale_items.append(item)
    
    # logging.debug(f"{len(all_sale_items)} Sale Items Found This Week: {all_sale_items}")
    
    # may need to refactor this; currently O(n^2)
    for i in range(len(all_sale_items)):
        for j in range(len(favs)):
            if favs[j].upper().replace("'","") in all_sale_items[i]["title"].upper():
                my_item = unidecode(all_sale_items[i]["title"])
                my_deal = all_sale_items[i]["deal"]
                my_info = all_sale_items[i]["info"]
                
                new_item = {
                    "title": str(my_item),
                    "deal": str(my_deal),
                    "info": str(my_info)
                }

                if not new_item in my_sale_items:
                    my_sale_items.append(new_item)
                
                # logging.debug(f"Updated Items in {user['username']}'s my_sale_items: {my_sale_items}")
    
    if my_sale_items == []:
        logging.debug("No items found matching search criteria")
    # else:
    #     logging.debug(f"Sale items found matching {user['username']}'s favs: {my_sale_items}")

    return my_sale_items


if __name__ == "__main__":
    pages = get_pages(user)
    for page in range(1, int(pages)):
        find_sales(user, page)
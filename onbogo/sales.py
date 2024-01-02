#!/usr/bin/env python3

import bs4
import requests
import logging
from unidecode import unidecode
from datetime import date

logging.basicConfig(
    # filename='myLogFile.txt', # use this to write logs to specified file
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# logging.disable(logging.CRITICAL) # this code disables logging for the program

testUser = {
    "username":"testUser",
    "email":"testUser@gmail.com",
    "sale_id":5232540,
    "my_store":{"store_id":2501054},
    "favs":["bacon","oatmilk","Sweet Baby","wine","sub"]
    }

all_titles = []
all_deals = []
all_info = []
all_sale_items = []

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}


def get_weekly_ad(store_id):
    logging.debug("initatite: get_weekly_ad")

    weekly_ad_url = f"https://accessibleweeklyad.publix.com/PublixAccessibility/Entry/LandingContent?storeid={store_id}&sneakpeek=N&listingid=0#"

    res = requests.get(weekly_ad_url, headers=headers)
    res.raise_for_status  # raise an exception if there is a problem downloading URL text
    soup = bs4.BeautifulSoup(res.text, features="html.parser")

    # find div for right column
    promotion = soup.select("div.rightcolumn")
    for el in promotion:
        info = el.select("div.infoUnit")

        for links in info:
            a_tags = links.findAll("a", recursive=False)
            
            for link in a_tags:
                sale_path = str(a_tags[0]["href"])
                sale_base = "https://accessibleweeklyad.publix.com:443"
                weekly_ad = sale_base + sale_path
                print("weekly_ad: ")
                print(weekly_ad)
                
    return weekly_ad

    
    


# def get_pages(user, page, sale_url):
#     logging.debug("initatite: get_pages")
#     store_id = user["my_store"]["store_id"]

#     # sale URL with date
#     sale_url = f"https://accessibleweeklyad.publix.com/PublixAccessibility/BrowseByPage/Index/?Breadcrumb=Weekly+Ad&StoreID={store_id}&PromotionCode=Publix-{formattedDate}&PromotionViewMode=1"

#     # temporary URL for thanksgiving holiday
#     # sale_url = f"https://accessibleweeklyad.publix.com/PublixAccessibility/BrowseByPage/Index/?Breadcrumb=Weekly+Ad&StoreID={store_id}&PromotionCode=Publix-231124&PromotionViewMode=1&PageNumber={page}"

    
#     res = requests.get(sale_url, headers=headers)


def get_pages(user, page, weekly_ad):
    logging.debug("initatite: get_pages")
    store_id = user["my_store"]["store_id"]
    
    res = requests.get(weekly_ad, headers=headers)
    res.raise_for_status  # raise an exception if there is a problem downloading URL text
    soup = bs4.BeautifulSoup(res.text, features="html.parser")

    pages_div = soup.select('div.paginationUnitMobile.includeInMobile')
    
    for page in pages_div:
        page_count = page.find("div", {"class": "pageXofY"}).text.strip()
        # logging.debug(f"page_count: {page_count}")
        page_list = page_count.split()
        # logging.debug(f"page_list: {page_list}")
        pages = int(page_list[-1])

        logging.debug(f"pages: {pages}")
        return pages


def find_sales(user, page, weekly_ad):    
    logging.debug("initatite: find_sales")
    store_id = user["my_store"]["store_id"]
    favs = user["favs"]
    email = user["email"]
    
    my_sale_items = []

    # sale URL with date
    # sale_url = f"https://accessibleweeklyad.publix.com/PublixAccessibility/BrowseByPage/Index/?Breadcrumb=Weekly+Ad&StoreID={store_id}&PromotionCode=Publix-{formattedDate}&PromotionViewMode=1&PageNumber={page}"
    
    sale_page = f"{weekly_ad}&PageNumber={page}"

    res = requests.get(sale_page, headers=headers)
    res.raise_for_status  # raise an exception if there is a problem downloading URL text
    soup = bs4.BeautifulSoup(res.text, features="html.parser")

    # find div for product cards
    cards = soup.select('div.unitB')
    # logging.debug(f"cards found: {len(cards)}")

    # strip product title and append to array
    for card in cards:
        title_element = card.find("div", class_="title").text.strip()
        all_titles.append(title_element)

        if card.find("div", class_="deal"):
            deal_element = card.find("div", class_="deal").text.strip()
            all_deals.append(deal_element)
        else:
            deal_element = ""
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
    store_id = "2500640"
    get_weekly_ad(store_id)
    # pages = get_pages(testUser)
    # for page in range(1, pages+1):
    #     find_sales(testUser, page)
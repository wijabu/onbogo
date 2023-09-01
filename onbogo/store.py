#!/usr/bin/env python3

from flask import jsonify, render_template

import bs4
import requests
import logging
# import json
from unidecode import unidecode

logging.basicConfig(
    # filename='myLogFile.txt', # use this to write logs to specified file
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# logging.disable(logging.CRITICAL) # this code disables logging for the program

def locate(zip, stores=[]):
    stores.clear()
    
    store_url = f"https://accessibleweeklyad.publix.com/PublixAccessibility?CityStateZip={zip}"

    res = requests.get(store_url)
    res.raise_for_status  # raise an exception if there is a problem downloading URL text

    soup = bs4.BeautifulSoup(res.text, features="html.parser")
    titles = soup.select("p.addressHeadline")
    addresses = soup.select("p.addressStoreTitle")
    ids = soup.select("a.mapddlink.action-tracking-directions.excludeFromMobile")

    logging.debug("Start store location search")

    for i in range(len(titles)):
        title = titles[i].text.strip()
        address = addresses[i].text.strip()
        store_id = ids[i]["data-tracking-storeid"]
        
        logging.debug(
            f"store {i} is {title}"
        )  # will log all items found on weekly ad
        
        stores.append({"title":title, "address":address, "store_id":int(store_id)})
        print(stores)
    
    if stores == []:
        print("No stores found by zip code")
    else:
        logging.debug(f"Stores found near my zip code: {stores}")
    
    return stores


if __name__ == "__main__":
    locate()
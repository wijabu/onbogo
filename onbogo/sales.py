import requests
import logging

logging.basicConfig(level=logging.DEBUG)
headers = {
    "User-Agent": "Mozilla/5.0 (compatible; WeeklyAdScraper/1.0)"
}


def get_weekly_ad(store_id):
    """
    Fetch weekly ad data for a given Publix store using the JSON API.
    Returns a dict with store info, categories, and items.
    """
    logging.debug(f"Initiating: get_weekly_ad for store_id={store_id}")

    url = f"https://services.publix.com/api/v1/weeklyad/store/{store_id}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logging.error(f"Error fetching weekly ad for store {store_id}: {e}")
        return None


def extract_items(ad_data):
    """
    Take the JSON response from get_weekly_ad and flatten it into a list of items.
    Each item contains category, title, price, and savings.
    """
    items = []
    if not ad_data or "weeklyAd" not in ad_data:
        logging.warning("No weekly ad data found in JSON")
        return items

    ad_info = ad_data["weeklyAd"]
    store_info = ad_data.get("store", {})

    valid_from = ad_info.get("validFrom")
    valid_to = ad_info.get("validTo")

    for category in ad_info.get("categories", []):
        cat_name = category.get("name", "Unknown")
        for item in category.get("items", []):
            items.append({
                "storeId": store_info.get("id"),
                "storeName": store_info.get("name"),
                "validFrom": valid_from,
                "validTo": valid_to,
                "category": cat_name,
                "title": item.get("title"),
                "price": item.get("price"),
                "savings": item.get("savings"),
                "description": item.get("description"),
                "image": item.get("imageUrl"),
            })
    return items


def get_sales(store_id):
    """
    High-level wrapper: fetch ad and return flattened list of sale items.
    """
    logging.debug(f"Fetching sales for store {store_id}")
    ad_data = get_weekly_ad(store_id)
    items = extract_items(ad_data)
    logging.info(f"Retrieved {len(items)} sale items for store {store_id}")
    return items


if __name__ == "__main__":
    # Example usage for a given store_id
    store_id = 1234  # replace with a real Publix store ID
    sales = get_sales(store_id)

    if sales:
        print(f"Got {len(sales)} sale items for store {store_id}")
        print(sales[0])  # show the first item
    else:
        print("No sales found.")


if __name__ == "__main__":
    store_id = testUser["my_store"]["store_id"]
    sales = get_sales(store_id)

    if sales:
        print(f"Got {len(sales)} sale items for store {store_id}")
        print(sales[0])  # show the first item
    else:
        print("No sales found.")

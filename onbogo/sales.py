
import requests
import logging
from decouple import config

def get_weekly_ad(store_id, user=None):
    url = f"https://www.publix.com/savings/weekly-ad/view-all?storeid={store_id}"
    logging.debug(f"Opening weekly ad URL: {url}")

    browserless_url = "https://chrome.browserless.io/playwright"
    api_key = config("BROWSERLESS_API_KEY")

    payload = {
        "url": url,
        "waitUntil": "networkidle",
        "actions": [
            {"type": "waitForSelector", "selector": ".weekly-ad-item"},
            {
                "type": "evaluate",
                "expression": """
                    Array.from(document.querySelectorAll('.weekly-ad-item')).map(item => ({
                        title: item.querySelector('.item-title')?.innerText,
                        price: item.querySelector('.item-price')?.innerText
                    }))
                """
            }
        ]
    }

    try:
        response = requests.post(
            browserless_url,
            headers={"Cache-Control": "no-cache"},
            params={"token": api_key},
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        sale_items = response.json()
        logging.debug(f"Found {len(sale_items)} sale items for store {store_id}")
        return sale_items
    except Exception as e:
        logging.error(f"Browserless API error: {e}")
        return []

#!/usr/bin/env python3

import logging
import time
from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def locate(zip):
    url = f"https://accessibleweeklyad.publix.com/PublixAccessibility?CityStateZip={zip}"
    logging.debug(f"Locating stores for zip: {zip}")

    stores = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            java_script_enabled=True,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = context.new_page()
        page.set_default_timeout(20000)
        page.goto(url, wait_until="domcontentloaded")

        try:
            page.wait_for_selector("p.addressHeadline", timeout=15000)
        except Exception as e:
            logging.error(f"Timeout waiting for store listings: {e}")
            browser.close()
            return []

        titles = page.query_selector_all("p.addressHeadline")
        addresses = page.query_selector_all("p.addressStoreTitle")
        ids = page.query_selector_all("a.mapddlink")

        for i in range(len(titles)):
            try:
                title = titles[i].inner_text().strip()
                address = addresses[i].inner_text().strip()
                store_id = ids[i].get_attribute("data-tracking-storeid")
                stores.append({
                    "title": title,
                    "address": address,
                    "store_id": int(store_id)
                })
                logging.debug(f"Found store: {title} (ID: {store_id})")
            except Exception as e:
                logging.warning(f"Error parsing store {i}: {e}")
                continue

        browser.close()

    if not stores:
        logging.warning(f"No stores found for zip: {zip}")

    return stores


if __name__ == "__main__":
    locate("32779")

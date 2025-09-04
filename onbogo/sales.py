from playwright.sync_api import sync_playwright
import logging
from decouple import config
import time

def get_weekly_ad(store_id, user=None):
    url = f"https://www.publix.com/savings/weekly-ad/view-all?storeid={store_id}"
    logging.debug(f"Opening weekly ad URL: {url}")

    start_time = time.time()

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(
            f"wss://production-sfo.browserless.io?token={config('BROWSERLESS_API_KEY')}"
        )
        context = browser.new_context(
            java_script_enabled=True,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0",
            locale="en-US",
            permissions=[],
            bypass_csp=True,
        )
        page = context.new_page()
        page.set_default_timeout(15000)
        page.goto(url, wait_until="domcontentloaded")

        try:
            page.wait_for_selector(".weekly-ad-item", timeout=10000)
        except Exception as e:
            logging.error(f"Timeout waiting for weekly ad items: {e}")
            browser.close()
            return []

        items = page.query_selector_all(".weekly-ad-item")
        sale_items = []

        for item in items:
            try:
                title = item.query_selector(".item-title").inner_text()
                price = item.query_selector(".item-price").inner_text()
                sale_items.append({"title": title, "price": price})
            except Exception:
                continue

        browser.close()

    elapsed = time.time() - start_time
    logging.debug(f"Scraping completed in {elapsed:.2f} seconds. Found {len(sale_items)} items.")
    return sale_items

import logging
import time
from playwright.sync_api import sync_playwright


def get_weekly_ad(store_id, user=None):
    url = f"https://www.publix.com/savings/weekly-ad/view-all?storeid={store_id}"
    logging.debug(f"Opening weekly ad URL: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
        ])
        context = browser.new_context(
            java_script_enabled=True,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            geolocation={"longitude": -81.4, "latitude": 28.7},
            permissions=["geolocation"],
            bypass_csp=True,
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            with page.expect_response(
                lambda r: "storeproductssavings" in r.url, timeout=60000
            ) as response_info:
                page.goto(url, wait_until="domcontentloaded")

            response = response_info.value
            logging.debug(f"SAVINGS URL: {response.url}")
            logging.debug(f"SAVINGS POST DATA: {response.request.post_data}")
            body = response.body()
            logging.debug(f"SAVINGS BODY: {body[:3000].decode('utf-8', errors='replace')}")
        except Exception as e:
            logging.error(f"Failed to capture savings response: {e}")

        browser.close()
        return []

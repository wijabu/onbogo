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
            "--disable-infobars",
            "--window-size=1280,800",
        ])
        context = browser.new_context(
            java_script_enabled=True,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            geolocation={"longitude": -81.4, "latitude": 28.7},
            permissions=["geolocation"],
            bypass_csp=True,
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            },
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)
        page = context.new_page()
        page.set_default_timeout(60000)

        def on_response(response):
            try:
                if "storeproductssavings" in response.url and response.status == 200:
                    logging.debug(f"SAVINGS URL: {response.url}")
                    logging.debug(f"SAVINGS HEADERS: {dict(response.request.headers)}")
                    body = response.body()
                    logging.debug(f"SAVINGS BODY: {body[:3000].decode('utf-8', errors='replace')}")
            except Exception as e:
                logging.debug(f"Response capture error: {e}")

        page.on("response", on_response)
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(15)

        browser.close()
        return []

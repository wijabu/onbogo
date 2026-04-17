import logging
import time
from playwright.sync_api import sync_playwright


def get_weekly_ad(store_id, user=None):
    url = f"https://www.publix.com/savings/weekly-ad/view-all?storeid={store_id}"
    logging.debug(f"Opening weekly ad URL: {url}")

    start_time = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ])
        context = browser.new_context(
            java_script_enabled=True,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            locale="en-US",
            geolocation={"longitude": -81.4, "latitude": 28.7},
            permissions=["geolocation"],
            bypass_csp=True,
        )
        page = context.new_page()
        page.set_default_timeout(30000)
        page.goto(url, wait_until="domcontentloaded")

        # Wait for Vue to render product cards, not just the HTML shell
        try:
            page.wait_for_selector("li.p-grid-item", timeout=30000, state="attached")
        except Exception as e:
            logging.error(f"Timeout waiting for product cards: {e}")
            html = page.content()
            logging.debug("Page HTML snapshot:\n" + html[:5000])
            browser.close()
            return []

        # Scroll to trigger lazy loading of remaining cards
        for _ in range(3):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            time.sleep(1.5)

        # Brief pause for any newly-loaded cards to settle
        time.sleep(2)

        items = page.query_selector_all("li.p-grid-item")

        if not items:
            logging.warning("No product cards found in .p-grid-item elements.")

        sale_items = []
        for item in items:
            try:
                title = item.query_selector("[data-qa-automation='prod-title']").inner_text().strip()
                badge = item.query_selector(".p-savings-badge__text")
                price_info = item.query_selector(".additional-info")
                valid_dates = item.query_selector(".valid-dates")

                sale_items.append({
                    "title": title,
                    "deal": badge.inner_text().strip() if badge else "",
                    "price_info": price_info.inner_text().strip() if price_info else "",
                    "valid_dates": valid_dates.inner_text().strip() if valid_dates else "",
                })
            except Exception:
                continue

        browser.close()

    elapsed = time.time() - start_time
    logging.debug(f"Scraping completed in {elapsed:.2f} seconds. Found {len(sale_items)} items.")
    return sale_items

from playwright.sync_api import sync_playwright
import logging
import glob
import os

def log_chromium_install_tree():
    print("🔍 Chromium install tree:")
    for root, dirs, files in os.walk("/app/playwright-browsers"):
        for name in files:
            print(os.path.join(root, name))

log_chromium_install_tree()


def find_chromium_executable():
    pattern = "/app/playwright-browsers/chromium-*/chrome-linux/chrome"
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    else:
        raise FileNotFoundError("Chromium executable not found in custom install path.")

def get_weekly_ad(store_id, user=None):
    url = f"https://www.publix.com/savings/weekly-ad/view-all?storeid={store_id}"
    logging.debug(f"Opening weekly ad URL: {url}")

    sale_items = []

    with sync_playwright() as p:
        executable_path = find_chromium_executable()

        browser = p.chromium.launch(
            headless=True,
            executable_path=executable_path
        )


        page = browser.new_page()
        page.goto(url)

        page.wait_for_selector(".weekly-ad-item", timeout=10000)
        items = page.query_selector_all(".weekly-ad-item")

        for item in items:
            try:
                title = item.query_selector(".item-title").inner_text()
                price = item.query_selector(".item-price").inner_text()
                sale_items.append({"title": title, "price": price})
            except Exception:
                continue

        browser.close()

    logging.debug(f"Found {len(sale_items)} sale items for store {store_id}")
    return sale_items

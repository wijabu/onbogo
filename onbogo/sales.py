import logging
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def _init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    # Add this to avoid port conflicts
    chrome_options.add_argument("--remote-debugging-port=0")

    # Create a unique temporary directory for user data
    user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_weekly_ad(store_id, user=None):
    """
    Fetch weekly ad items from Publix for a given store.
    """
    weekly_ad_url = f"https://www.publix.com/savings/weekly-ad/view-all?storeid={store_id}"
    logging.debug(f"Opening weekly ad URL: {weekly_ad_url}")

    driver = _init_driver()
    sale_items = []

    try:
        driver.get(weekly_ad_url)
        # Wait for the page to load (adjust selector to actual sale item container)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".weekly-ad-item"))
        )

        items = driver.find_elements(By.CSS_SELECTOR, ".weekly-ad-item")
        for item in items:
            try:
                title = item.find_element(By.CSS_SELECTOR, ".item-title").text
                price = item.find_element(By.CSS_SELECTOR, ".item-price").text
                sale_items.append({"title": title, "price": price})
            except Exception:
                continue

        logging.debug(f"Found {len(sale_items)} sale items for store {store_id}")

    except Exception as e:
        logging.error(f"Error fetching weekly ad: {e}", exc_info=True)
    finally:
        driver.quit()

    return sale_items

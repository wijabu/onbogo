import logging
import os
import uuid
import shutil

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


def _init_driver():
    logging.debug(f"Chrome binary found: {shutil.which(os.getenv('CHROME_BIN', '/usr/bin/google-chrome'))}")
    logging.debug(f"ChromeDriver found: {shutil.which('/usr/local/bin/chromedriver')}")
    ...
    chrome_options = Options()

    # Explicitly set Chrome binary location
    chrome_options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/google-chrome")

    # Add Chrome flags for headless operation
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--remote-debugging-port=0")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--no-first-run")

    # Create unique user data directory
    unique_tmp_dir = f"/tmp/chrome-user-data-{uuid.uuid4()}"
    os.makedirs(unique_tmp_dir, exist_ok=True)
    chrome_options.add_argument(f"--user-data-dir={unique_tmp_dir}")

    # Set desired capabilities
    caps = DesiredCapabilities.CHROME.copy()
    chrome_options.set_capability("browserName", "chrome")

    # Initialize ChromeDriver with explicit path
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
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

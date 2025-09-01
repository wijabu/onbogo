import logging
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _init_driver():
    """Initialize a headless Chrome WebDriver (Render-compatible)."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_weekly_ad(store_id: str):
    """
    Opens the Publix Weekly Ad page for a given store_id.
    Returns a WebDriver object positioned at the weekly ad.
    """
    url = f"https://www.publix.com/savings/weekly-ad/view-all?storeid={store_id}"
    logging.debug(f"Opening weekly ad URL: {url}")

    driver = _init_driver()
    driver.get(url)

    try:
        # Wait for product cards to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".weekly-ad__product"))
        )
        logging.debug("Weekly ad products loaded successfully.")
    except Exception as e:
        logging.error(f"Weekly ad failed to load: {e}")
        driver.quit()
        return None

    return driver


def get_pages(user, driver):
    """
    Detect how many pages of products exist.
    Returns int number of pages (defaults to 1 if no pagination).
    """
    try:
        pagination = driver.find_elements(By.CSS_SELECTOR, ".pagination__page")
        if pagination:
            pages = len(pagination)
            logging.debug(f"Found {pages} pages in weekly ad.")
            return pages
        else:
            logging.debug("No pagination found, defaulting to 1 page.")
            return 1
    except Exception as e:
        logging.error(f"Error detecting pages: {e}")
        return 1


def find_sales(user, page: int, driver):
    """
    Scrape a single page of the weekly ad for sales matching user's favorites.
    Returns a list of dicts {title, price, details}.
    """
    sale_items = []

    try:
        # If pagination exists, click to page
        if page > 1:
            try:
                page_button = driver.find_element(
                    By.XPATH, f"//button[contains(@class,'pagination__page') and text()='{page}']"
                )
                page_button.click()
                time.sleep(2)  # wait for products to load
            except Exception as e:
                logging.warning(f"Could not navigate to page {page}: {e}")

        products = driver.find_elements(By.CSS_SELECTOR, ".weekly-ad__product")

        favs = [f.lower() for f in user.get("favs", [])]

        for product in products:
            try:
                title = product.find_element(By.CSS_SELECTOR, ".weekly-ad__product-title").text.strip()
            except:
                title = "Unknown Item"

            try:
                price = product.find_element(By.CSS_SELECTOR, ".weekly-ad__product-price").text.strip()
            except:
                price = "No Price"

            try:
                details = product.find_element(By.CSS_SELECTOR, ".weekly-ad__product-promo").text.strip()
            except:
                details = ""

            # Only include if matches user favorites
            if any(fav in title.lower() for fav in favs):
                sale_items.append({
                    "title": title,
                    "price": price,
                    "details": details,
                })

        logging.debug(f"Found {len(sale_items)} sale items on page {page}.")
    except Exception as e:
        logging.error(f"Error scraping page {page}: {e}")

    return sale_items

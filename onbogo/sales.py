import logging
import tempfile
import uuid
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


def _init_driver():
    """Initialize a headless Chrome WebDriver with a unique temp profile."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    unique_dir = tempfile.mkdtemp(prefix=f"chrome-user-{uuid.uuid4()}-")
    logging.debug(f"Using unique Chrome user data dir: {unique_dir}")
    chrome_options.add_argument(f"--user-data-dir={unique_dir}")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_weekly_ad(store_id: str, user: dict, max_retries: int = 3):
    """
    Scrape all pages of Publix Weekly Ad for a given store_id and user favorites.
    Returns a list of dicts {title, price, details}.
    Driver automatically quits after scraping.
    """
    url = f"https://www.publix.com/savings/weekly-ad/view-all?storeid={store_id}"
    logging.debug(f"Opening weekly ad URL: {url}")

    sale_items = []
    driver = _init_driver()

    try:
        driver.get(url)

        # Wait for the first page of products to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".weekly-ad__product"))
        )
        logging.debug("Weekly ad first page loaded successfully.")

        # Determine total pages
        try:
            pagination = driver.find_elements(By.CSS_SELECTOR, ".pagination__page")
            total_pages = len(pagination) if pagination else 1
            logging.debug(f"Total pages detected: {total_pages}")
        except Exception as e:
            logging.warning(f"Pagination detection failed, defaulting to 1 page: {e}")
            total_pages = 1

        favs = [f.lower() for f in user.get("favs", [])]

        # Scrape each page
        for page in range(1, total_pages + 1):
            retries = 0
            while retries < max_retries:
                try:
                    if page > 1:
                        try:
                            page_button = driver.find_element(
                                By.XPATH, f"//button[contains(@class,'pagination__page') and text()='{page}']"
                            )
                            page_button.click()

                            # Wait for the new products to load
                            WebDriverWait(driver, 15).until(
                                EC.staleness_of(driver.find_elements(By.CSS_SELECTOR, ".weekly-ad__product")[0])
                            )
                            WebDriverWait(driver, 15).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".weekly-ad__product"))
                            )
                        except Exception as e:
                            logging.warning(f"Navigation to page {page} failed: {e}")

                    products = driver.find_elements(By.CSS_SELECTOR, ".weekly-ad__product")
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

                        if any(fav in title.lower() for fav in favs):
                            sale_items.append({
                                "title": title,
                                "price": price,
                                "details": details,
                            })

                    logging.debug(f"Page {page}: Found {len(products)} products, {len(sale_items)} matched favorites so far.")
                    break  # page succeeded, move to next
                except (TimeoutException, StaleElementReferenceException) as e:
                    retries += 1
                    logging.warning(f"Retry {retries}/{max_retries} for page {page} due to error: {e}")
                    time.sleep(2)  # short wait before retry
                except Exception as e:
                    logging.error(f"Unexpected error on page {page}: {e}")
                    break  # skip this page

            else:
                logging.error(f"Failed to scrape page {page} after {max_retries} retries.")

    except Exception as e:
        logging.error(f"Error scraping weekly ad: {e}")

    finally:
        driver.quit()
        logging.debug("Chrome driver quit successfully after scraping all pages.")

    return sale_items

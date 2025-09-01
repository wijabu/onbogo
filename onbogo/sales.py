import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

def _init_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    # let Selenium Manager find the driver automatically
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_weekly_ad(store_id: str, user: dict, max_retries: int = 3):
    url = f"https://www.publix.com/savings/weekly-ad/view-all?storeid={store_id}"
    logging.debug(f"Opening weekly ad URL: {url}")

    sale_items = []
    driver = _init_driver()
    favs = [f.lower() for f in user.get("favs", [])]

    try:
        driver.get(url)

        # Wait for products to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".weekly-ad__product"))
        )
        logging.debug("Weekly ad first page loaded successfully.")

        # Detect total pages
        try:
            pagination = driver.find_elements(By.CSS_SELECTOR, ".pagination__page")
            total_pages = len(pagination) if pagination else 1
        except Exception as e:
            logging.warning(f"Pagination detection failed, defaulting to 1 page: {e}")
            total_pages = 1

        for page in range(1, total_pages + 1):
            retries = 0
            while retries < max_retries:
                try:
                    if page > 1:
                        try:
                            # Navigate to next page
                            page_button = driver.find_element(
                                By.XPATH, f"//button[contains(@class,'pagination__page') and text()='{page}']"
                            )
                            old_products = driver.find_elements(By.CSS_SELECTOR, ".weekly-ad__product")
                            page_button.click()
                            if old_products:
                                WebDriverWait(driver, 15).until(EC.staleness_of(old_products[0]))
                            WebDriverWait(driver, 15).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".weekly-ad__product"))
                            )
                        except Exception as e:
                            logging.warning(f"Navigation to page {page} failed: {e}")

                    # Scrape products
                    products = driver.find_elements(By.CSS_SELECTOR, ".weekly-ad__product")
                    for product in products:
                        try:
                            title = product.find_element(By.CSS_SELECTOR, ".weekly-ad__product-title").text.strip()
                        except NoSuchElementException:
                            title = "Unknown Item"
                        try:
                            price = product.find_element(By.CSS_SELECTOR, ".weekly-ad__product-price").text.strip()
                        except NoSuchElementException:
                            price = "No Price"
                        try:
                            details = product.find_element(By.CSS_SELECTOR, ".weekly-ad__product-promo").text.strip()
                        except NoSuchElementException:
                            details = ""

                        if any(fav in title.lower() for fav in favs):
                            sale_items.append({
                                "title": title,
                                "price": price,
                                "details": details,
                            })

                    logging.debug(f"Page {page}: Found {len(products)} products, {len(sale_items)} matched favorites so far.")
                    break  # success, next page
                except (TimeoutException, StaleElementReferenceException) as e:
                    retries += 1
                    logging.warning(f"Retry {retries}/{max_retries} for page {page} due to: {e}")
                    time.sleep(2)
                except Exception as e:
                    logging.error(f"Unexpected error on page {page}: {e}")
                    break
            else:
                logging.error(f"Failed to scrape page {page} after {max_retries} retries.")

    except Exception as e:
        logging.error(f"Error scraping weekly ad: {e}")

    finally:
        driver.quit()
        logging.debug("Chrome driver quit successfully after scraping all pages.")

    return sale_items

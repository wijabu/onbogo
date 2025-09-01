# sales.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Publix weekly ad URL
PUBLIX_WEEKLY_AD_URL = "https://www.publix.com/savings/weekly-ad/view-all"

def get_weekly_ad_products():
    """
    Scrapes Publix weekly ad products using Selenium.
    Returns a list of dictionaries with keys: title, price, savings.
    """

    # Configure headless Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Initialize WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(PUBLIX_WEEKLY_AD_URL)

    # Wait for product cards to appear
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".card-product")))

    # Scroll to bottom to load lazy-loaded products
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Extract products
    products = driver.find_elements(By.CSS_SELECTOR, ".card-product")
    ad_items = []

    for product in products:
        try:
            title = product.find_element(By.CSS_SELECTOR, ".card-product__title").text
        except:
            title = ""
        try:
            price = product.find_element(By.CSS_SELECTOR, ".card-product__price").text
        except:
            price = ""
        try:
            savings = product.find_element(By.CSS_SELECTOR, ".card-product__savings").text
        except:
            savings = ""
        ad_items.append({
            "title": title,
            "price": price,
            "savings": savings
        })

    driver.quit()
    return ad_items

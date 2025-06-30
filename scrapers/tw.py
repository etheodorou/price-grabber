import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from core.selectors import load_selectors

def clean_price(price_str):
    if price_str is None:
        return ""
    price = re.findall(r"\d+[.,]?\d*", price_str.replace(",", "."))
    return price[0] if price else ""

def scrape_tw(brand, url):
    selectors = load_selectors("TennisWarehouse", "tennis-racquets")
    products = []

    # --- HEADLESS Chrome options for robust scraping ---
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Accept cookies
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
    except:
        pass

    # Language/country selection (English, Greece)
    try:
        selects = driver.find_elements(By.ID, "vat_lang")
        if len(selects) >= 2:
            Select(selects[0]).select_by_value("en")
            Select(selects[1]).select_by_value("GR")
            driver.find_element(By.ID, "lang_vat_form").submit()
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.ID, "lang_vat_form"))
            )
            # HEADLESS: longer wait for full JS render after reload
            time.sleep(8)
    except:
        pass

    # Wait for product blocks to appear
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".cattable-wrap-cell-tagline_info"))
    )

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    cards = soup.select(".cattable-wrap-cell-tagline_info")
    for card in cards:
        # Product name
        name_tag = card.select_one(selectors["name"])
        name = name_tag.get_text(strip=True) if name_tag else ""

        # Badge (clean: only 'Sale', 'Reduced', etc.)
        badge_tag = card.select_one(selectors["badge"])
        badge = badge_tag.get_text(strip=True) if badge_tag else ""
        if badge:
            badge = re.split(r"[\-\d%]+", badge)[0].strip()

        # Discount (from badge)
        discount = ""
        match = re.search(r'-(\d+)%', badge_tag.get_text(strip=True)) if badge_tag else None
        discount = match.group(1) if match else ""

        # Price (current)
        price_tag = card.select_one(selectors["price"])
        price = clean_price(price_tag.get_text(strip=True)) if price_tag else ""

        # Old price (if discounted)
        old_price_tag = card.select_one(selectors["old_price"])
        old_price = clean_price(old_price_tag.get_text(strip=True)) if old_price_tag else ""

        # Product URL
        url_tag = card.select_one(selectors["product_url"])
        product_url = url_tag['href'] if url_tag and url_tag.has_attr("href") else ""

        # Filter out unwanted links
        if (
            not product_url
            or "/catpage-" in product_url
            or "/categoryvideo.html" in product_url
            or "/learning_center/gear_guides/" in product_url
        ):
            continue

        products.append({
            "name": name,
            "badge": badge,
            "discount": discount,
            "old_price": old_price,
            "price": price,
            "product_url": product_url
        })

    return pd.DataFrame(products)

if __name__ == "__main__":
    from core.brands_urls import TENNIS_WAREHOUSE_BRANDS
    all_dfs = []
    for brand, url in TENNIS_WAREHOUSE_BRANDS["tennis-racquets"].items():
        df = scrape_tw(brand, url)
        df["brand"] = brand
        all_dfs.append(df)
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.to_csv("tenniswarehouse_racquets.csv", index=False)
    print(final_df.head())

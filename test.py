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

    # Initialize Selenium WebDriver
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Handle cookie consent
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
    except:
        pass  # If the cookie banner doesn't appear

    # Select language and country
    try:
        language_select = Select(driver.find_element(By.ID, "vat_lang"))
        language_select.select_by_value("en")  # English

        country_select = Select(driver.find_elements(By.ID, "vat_lang")[1])
        country_select.select_by_value("GR")  # Greece

        driver.find_element(By.ID, "lang_vat_form").submit()
    except:
        pass  # If the language/VAT form doesn't appear

    # Wait for the page to load after form submission
    time.sleep(5)

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Extract product information
    cards = soup.select(".cattable-wrap-cell-tagline_info")
    for card in cards:
        # Product name
        name_tag = card.select_one(selectors["name"])
        name = name_tag.get_text(strip=True) if name_tag else ""

        # Badge/flag (Sale, New, etc)
        badge_tag = card.select_one(selectors["badge"])
        badge = badge_tag.get_text(strip=True) if badge_tag else ""

        # Discount (parse from badge)
        discount = ""
        if badge:
            match = re.search(r'-(\d+)%', badge)
            discount = match.group(1) if match else ""

        # Price (current)
        price_block = card.select_one(".cattable-wrap-cell-info-price")
        price = ""
        if price_block:
            for span in price_block.find_all('span', recursive=False):
                if not span.has_attr('class'):
                    price = clean_price(span.get_text(strip=True))
                    break

        # Old price (if discounted)
        old_price = ""
        old_price_tag = price_block.select_one(".is-crossout") if price_block else None
        if old_price_tag:
            old_price = clean_price(old_price_tag.get_text(strip=True))

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

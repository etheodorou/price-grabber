import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from core.selectors import load_selectors
from core.brands_urls import PADEL_NUESTRO_BRANDS

def clean_price(price_str):
    if price_str is None:
        return ""
    price = re.findall(r"\d+[.,]?\d*", price_str.replace(",", "."))
    return price[0] if price else ""

def scrape_pn(brand, url, category="padel-rackets"):
    selectors = load_selectors("PadelNuestro", category)
    products = []
    session = requests.Session()
    next_url = url
    while next_url:
        r = session.get(next_url)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("li.item.product.product-item")
        for card in cards:
            # Name
            name_tag = card.select_one(selectors["name"])
            name = name_tag.get_text(strip=True) if name_tag else ""
            # Badge
            badge = ""
            badge_tag = card.select_one(selectors["badge"])
            if badge_tag:
                badge = badge_tag.get_text(strip=True)
            # Discount
            discount = ""
            discount_tag = card.select_one(selectors["discount"])
            if discount_tag:
                discount = clean_price(discount_tag.get_text(strip=True))
            # Price
            price_tag = card.select_one(selectors["price"])
            price = clean_price(price_tag.get_text(strip=True)) if price_tag else ""
            # Old price
            old_price_tag = card.select_one(selectors["old_price"])
            old_price = clean_price(old_price_tag.get_text(strip=True)) if old_price_tag else ""
            # Product URL
            url_tag = card.select_one(selectors["product_url"])
            product_url = url_tag["href"] if url_tag and url_tag.has_attr("href") else ""
            products.append({
                "name": name,
                "badge": badge,
                "discount": discount,
                "old_price": old_price,
                "price": price,
                "product_url": product_url
            })
        # Pagination
        next_page = soup.select_one(selectors.get("next_page", "li.item.pages-item-next a.action.next"))
        next_url = next_page["href"] if next_page and next_page.has_attr("href") else None

    return pd.DataFrame(products)

if __name__ == "__main__":
    all_dfs = []
    for brand, url in PADEL_NUESTRO_BRANDS["padel-rackets"].items():
        df = scrape_pn(brand, url)
        df["brand"] = brand
        all_dfs.append(df)
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.to_csv("padelnuestro_padelrackets.csv", index=False)
    print(final_df.head())

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from core.selectors import load_selectors
from core.brands_urls import PADEL_NUESTRO_RACKETS_BRANDS

def clean_price(price_str):
    if price_str is None:
        return ""
    price = re.findall(r"\d+[.,]?\d*", price_str.replace(",", "."))
    return price[0] if price else ""

def scrape_pn(brand, url):
    # Generate selector key from brand & category slug
    slug = url.rstrip('/').split('/')[-1]
    category = url.rstrip('/').split('/')[-2]
    selectors = load_selectors("PadelNuestro", category)

    products = []
    category_url = url
    session = requests.Session()

    while category_url:
        print(f"Scraping: {category_url}")
        r = session.get(category_url)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("li.item.product.product-item")
        for card in cards:
            name_tag = card.select_one(selectors["name"])
            name = name_tag.get_text(strip=True) if name_tag else ""

            badge = ""
            badge_tag = card.select_one(selectors["badge"])
            if badge_tag:
                badge = badge_tag.get_text(strip=True)

            old_price = ""
            old_price_tag = card.select_one(selectors["old_price"])
            if old_price_tag:
                old_price = clean_price(old_price_tag.get_text(strip=True))
            else:
                old_price = ""

            price = ""
            price_tag = card.select_one(selectors["price"])
            if price_tag:
                price = clean_price(price_tag.get_text(strip=True))

            url_tag = card.select_one(selectors["product_url"])
            product_url = url_tag["href"] if url_tag and url_tag.has_attr("href") else ""

            # Discount: Calculate from prices if possible, else fallback to badge
            discount = "0"
            try:
                old_price_val = float(old_price.replace(",", "."))
                price_val = float(price.replace(",", "."))
                if old_price_val > 0 and price_val < old_price_val:
                    discount = str(round(100 * (old_price_val - price_val) / old_price_val))
                else:
                    discount_tag = card.select_one(selectors["discount"])
                    if discount_tag:
                        badge_val = re.findall(r"\d+", discount_tag.get_text(strip=True))
                        discount = badge_val[0] if badge_val else "0"
                    else:
                        discount = "0"
            except Exception:
                discount_tag = card.select_one(selectors["discount"])
                if discount_tag:
                    badge_val = re.findall(r"\d+", discount_tag.get_text(strip=True))
                    discount = badge_val[0] if badge_val else "0"
                else:
                    discount = "0"

            products.append({
                "name": name,
                "badge": badge,
                "discount": discount,
                "price": price,
                "old_price": old_price,
                "product_url": product_url
            })

        # Pagination: find next page link
        next_page = soup.select_one("li.item.pages-item-next a.action.next")
        if next_page and next_page.has_attr("href"):
            category_url = next_page["href"]
        else:
            category_url = None

    return pd.DataFrame(products)

# For quick batch test:
if __name__ == "__main__":
    all_dfs = []
    for brand, url in PADEL_NUESTRO_RACKETS_BRANDS.items():
        df = scrape_pn(brand, url)
        all_dfs.append(df)
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.to_csv("all_padelnuestro_rackets.csv", index=False)
    print(final_df.head())

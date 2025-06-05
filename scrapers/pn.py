import requests
from bs4 import BeautifulSoup
import csv
import re
from core.selectors import load_selectors

def clean_price(price_str):
    if price_str is None:
        return ""
    price = re.findall(r"\d+[.,]?\d*", price_str.replace(",", "."))
    return price[0] if price else ""

def scrape_pn_adidas_rackets():
    # Load selectors from YAML config
    selectors = load_selectors("PadelNuestro", "racket_category")
    base_url = "https://www.padelnuestro.com"
    category_url = f"{base_url}/int/padel-rackets/adidas"
    products = []
    session = requests.Session()

    while category_url:
        print(f"Scraping: {category_url}")
        r = session.get(category_url)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("li.item.product.product-item")
        for card in cards:
            # Use config selectors
            name = card.select_one(selectors["name"])
            name = name.get_text(strip=True) if name else ""

            badge = ""
            badge_tag = card.select_one(selectors["badge"])
            if badge_tag:
                badge = badge_tag.get_text(strip=True)

            discount = ""
            discount_tag = card.select_one(selectors["discount"])
            if discount_tag:
                discount = clean_price(discount_tag.get_text(strip=True))
            else:
                discount = "0"

            price = ""
            price_tag = card.select_one(selectors["price"])
            if price_tag:
                price = clean_price(price_tag.get_text(strip=True))

            old_price = ""
            old_price_tag = card.select_one(selectors["old_price"])
            if old_price_tag:
                old_price = clean_price(old_price_tag.get_text(strip=True))

            url_tag = card.select_one(selectors["product_url"])
            product_url = url_tag["href"] if url_tag and url_tag.has_attr("href") else ""

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

    # Write CSV (no image_url)
    with open("padelnuestro_adidas_rackets.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "badge", "discount", "price", "old_price", "product_url"])
        writer.writeheader()
        for p in products:
            writer.writerow(p)

if __name__ == "__main__":
    scrape_pn_adidas_rackets()

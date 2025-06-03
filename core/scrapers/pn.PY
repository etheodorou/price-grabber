import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def scrape_padelnuestro_adidas_rackets(base_url, output_csv="padelnuestro_adidas_rackets.csv", max_pages=50):
    all_products = []
    session = requests.Session()

    for page in range(1, max_pages+1):
        # Pagination URL (first page has no "?p=", next are "?p=2", etc)
        url = base_url if page == 1 else f"{base_url}?p={page}"
        print(f"Scraping page: {url}")

        resp = session.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"Error fetching {url} (status {resp.status_code})")
            break

        soup = BeautifulSoup(resp.content, "html.parser")

        # Select all product cards
        product_cards = soup.select("li.item.product.product-item")
        if not product_cards:
            print("No more products found on this page.")
            break

        for card in product_cards:
            # Product Name
            name_tag = card.select_one("strong.product.name.product-item-name a.product-item-link")
            name = name_tag.text.strip() if name_tag else ""

            # Product URL
            product_url = name_tag["href"] if name_tag and name_tag.has_attr("href") else ""

            # Price - "div.price-box.price-final_price"
            price_tag = card.select_one("span.price")
            price = price_tag.text.strip() if price_tag else ""

            # Old Price (if present)
            old_price_tag = card.select_one("span.old-price span.price")
            old_price = old_price_tag.text.strip() if old_price_tag else ""

            # Discount badge (like "-68%")
            discount_tag = card.select_one("span.product-label-discount")
            discount = discount_tag.text.strip() if discount_tag else ""

            # Badge (exclusive, out of stock, etc.)
            badge_tag = card.select_one("span.product-label span")
            badge = badge_tag.text.strip() if badge_tag else ""

            # Out of stock (explicit badge)
            out_of_stock = ""
            out_of_stock_tag = card.select_one("span.product-label-outstock")
            if out_of_stock_tag:
                out_of_stock = out_of_stock_tag.text.strip()
                badge = out_of_stock  # Override badge if out of stock

            # Product Image
            img_tag = card.select_one("span.product-image-wrapper img")
            image_url = ""
            if img_tag:
                if img_tag.has_attr("data-src"):
                    image_url = img_tag["data-src"]
                elif img_tag.has_attr("src"):
                    image_url = img_tag["src"]

            # If discount is empty but there is no old price, set discount to "0%"
            if not discount:
                if old_price:
                    # Could possibly calculate discount, but site usually lists this
                    pass
                else:
                    discount = "0%"

            all_products.append({
                "name": name,
                "badge": badge,
                "discount": discount,
                "price": price,
                "old_price": old_price,
                "product_url": product_url,
                "image_url": image_url,
            })

        # Pagination: Check if there is a "next" link, otherwise break
        pagination_next = soup.select_one("li.item.pages-item-next a.action.next")
        if not pagination_next:
            break
        time.sleep(1.1)  # Be kind to their server

    # Save as UTF-8 CSV
    df = pd.DataFrame(all_products)
    df.to_csv(output_csv, encoding="utf-8", index=False)
    print(f"Saved {len(df)} products to {output_csv}")

if __name__ == "__main__":
    # EXAMPLE: Adidas padel rackets
    base_url = "https://www.padelnuestro.com/int/padel-rackets/adidas"
    scrape_padelnuestro_adidas_rackets(base_url)

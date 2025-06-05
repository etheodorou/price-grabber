import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def parse_number(text):
    # Remove all but digits, dot, and comma, then replace comma with dot for decimals
    return float(re.sub(r'[^\d,\.]', '', text.replace('.', '').replace(',', '.')))

def get_product_info(product):
    # --- NAME ---
    name_tag = product.select_one('strong.product.name.product-item-name')
    name = name_tag.get_text(strip=True) if name_tag else ""

    # --- PRODUCT URL ---
    url_tag = product.select_one('a.product-item-link')
    product_url = url_tag['href'] if url_tag and url_tag.has_attr('href') else ""

    # --- IMAGE URL ---
    img_tag = product.select_one('img.product-image-photo')
    image_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else ""

    # --- PRICE ---
    price_tag = product.select_one('span.price')
    price = ""
    if price_tag:
        try:
            price = parse_number(price_tag.get_text())
        except:
            price = ""

    # --- OLD PRICE (if exists) ---
    old_price_tag = product.select_one('span.old-price .price')
    old_price = ""
    if old_price_tag:
        try:
            old_price = parse_number(old_price_tag.get_text())
        except:
            old_price = ""

    # --- DISCOUNT (if exists, just number, else 0) ---
    discount_tag = product.select_one('.product-label__percent')
    discount = 0
    if discount_tag:
        try:
            # Match e.g. '-65%' and extract just number
            discount_text = discount_tag.get_text(strip=True)
            discount_match = re.search(r'(\d+)', discount_text)
            if discount_match:
                discount = int(discount_match.group(1))
        except:
            discount = 0

    # If there is only a price (no old_price), then discount should be 0
    if not old_price:
        discount = 0

    # --- BADGE ---
    badge = ""
    if product.select_one('.product-label__outstock'):
        badge = "Out of stock"
    elif product.select_one('.product-label__exclusive'):
        badge = "Exclusive"

    # --- Compose HYPERLINK formulas for Excel ---
    product_link = f'=HYPERLINK("{product_url}","View")' if product_url else ""
    image_link = f'=HYPERLINK("{image_url}","Img")' if image_url else ""

    return {
        "name": name,
        "badge": badge,
        "discount": discount,
        "price": price,
        "old_price": old_price,
        "product_url": product_url,
        "product_link": product_link,
        "image_url": image_url,
        "image_link": image_link
    }

def scrape_all_pages(start_url):
    products = []
    page = 1
    next_url = start_url
    headers = {"User-Agent": "Mozilla/5.0"}
    while next_url:
        print(f"Scraping page {page}: {next_url}")
        resp = requests.get(next_url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        product_list = soup.select('li.item.product.product-item')
        for prod in product_list:
            products.append(get_product_info(prod))
        next_btn = soup.select_one('a.action.next')
        if next_btn and next_btn.has_attr('href'):
            next_url = next_btn['href']
            page += 1
        else:
            break
    return products

if __name__ == "__main__":
    url = "https://www.padelnuestro.com/int/padel-rackets/adidas"
    all_data = scrape_all_pages(url)
    df = pd.DataFrame(all_data)
    # Save as UTF-8, no index
    df.to_csv("padelnuestro_adidas_rackets.csv", index=False, encoding="utf-8-sig")
    print("Done! Saved as padelnuestro_adidas_rackets.csv")

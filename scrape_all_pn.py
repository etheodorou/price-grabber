from core.brands_urls import PADEL_NUESTRO_BRANDS
from scrapers.pn import scrape_pn
import pandas as pd

all_dfs = []

for category, brands in PADEL_NUESTRO_BRANDS.items():
    for brand, url in brands.items():
        print(f"Scraping {category} - {brand}")
        df = scrape_pn(brand, url)  # scrape_pn figures out category from URL
        df["category"] = category   # optional: tag output with category
        df["brand"] = brand         # optional: tag output with brand
        all_dfs.append(df)

final_df = pd.concat(all_dfs, ignore_index=True)
final_df.to_csv("all_padelnuestro_products.csv", index=False)
print(final_df.head())

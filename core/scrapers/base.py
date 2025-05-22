from abc import ABC, abstractmethod
from typing import Optional, Tuple

class BaseScraper(ABC):
    """Common interface all competitor-site scrapers must follow."""

    #: unique short name you’ll use as the column prefix in reports
    site_name: str = "example"

    @abstractmethod
    async def fetch_price(
        self, lookup_key: str
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Return (price, product_url) for the given barcode/SKU/title.

        * price:  float in store currency, or None if not found
        * product_url: direct URL of the matched listing, or None
        """
        ...

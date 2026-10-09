"""USD/EGP official exchange rates collector (Central Bank of Egypt - CBE)."""

import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .base import FXData, CollectorError
from ..utils.arabic_date import CAIRO_TZ

CBE_URL = "https://www.cbe.org.eg/en/economic-research/statistics/exchange-rates"


class FXCollector:
    NAME = "البنك المركزي المصري (CBE)"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def fetch(self) -> FXData:
        """Fetches the official USD/EGP buy and sell rates and their publication date from CBE."""
        try:
            r = requests.get(CBE_URL, headers=self.headers, timeout=self.timeout)
            r.raise_for_status()
        except requests.RequestException as e:
            raise CollectorError(f"CBE request failed: {e}") from e

        text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)

        # e.g. "Currency Buy Sell US Dollar 52.3378 52.4378"
        m = re.search(r"US Dollar\s+([\d.]+)\s+([\d.]+)", text)
        if not m:
            raise CollectorError("CBE: could not find the US Dollar row")
        buy, sell = float(m.group(1)), float(m.group(2))

        # e.g. "Last Updated: 07 Oct 2026"
        d = re.search(r"Last Updated:\s*(\d{1,2} \w{3} \d{4})", text)
        if not d:
            raise CollectorError("CBE: could not find the last-updated date")
        updated = datetime.strptime(d.group(1), "%d %b %Y").replace(tzinfo=CAIRO_TZ)

        return FXData(buy=buy, sell=sell, source=self.NAME, updated_at=updated, date_only=True)

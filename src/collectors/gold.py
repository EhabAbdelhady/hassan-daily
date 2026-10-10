"""Gold in Egypt data collector (iSagha prices page)."""

import re
from datetime import datetime

import requests
from typing import Dict, Optional

from bs4 import BeautifulSoup

from .base import GoldData, CollectorError
from ..utils.arabic_date import ARABIC_MONTHS, CAIRO_TZ

PRICES_URL = "https://market.isagha.com/prices"
MONTH_NUMBERS = {name: num for num, name in ARABIC_MONTHS.items()}


class GoldCollector:
    NAME = "iSagha"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def fetch(self) -> GoldData:
        """Fetches the 24k, 21k, 18k shop sell prices in Egypt from iSagha."""
        try:
            r = requests.get(PRICES_URL, headers=self.headers, timeout=self.timeout)
            r.raise_for_status()
        except requests.RequestException as e:
            raise CollectorError(f"iSagha request failed: {e}") from e

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        prices = self._parse_table(soup) or self._parse_prices(text)
        return GoldData(
            price_24k=prices["24k"],
            price_21k=prices["21k"],
            price_18k=prices["18k"],
            source=self.NAME,
            updated_at=self._parse_updated_at(text),
        )

    def _parse_table(self, soup: BeautifulSoup) -> Optional[Dict[str, float]]:
        """Reads the detailed price table by its column names (العيار / بيع): survives layout changes
        better than text patterns. Returns None if the table isn't there."""
        for table in soup.find_all("table"):
            headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
            karat_col = next((i for i, h in enumerate(headers) if h.startswith("العيار")), None)
            sell_col = next((i for i, h in enumerate(headers) if h.startswith("بيع")), None)
            if karat_col is None or sell_col is None:
                continue
            found = {}
            for tr in table.find_all("tr"):
                cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                if len(cells) <= max(karat_col, sell_col):
                    continue
                m = re.fullmatch(r"عيار (24|21|18)", cells[karat_col])
                price = re.match(r"([\d,.]+)\s*ج\.م", cells[sell_col])
                if m and price:
                    found[f"{m.group(1)}k"] = float(price.group(1).replace(",", ""))
            if len(found) == 3:
                return found
        return None

    def _parse_prices(self, text: str) -> dict:
        # e.g. "عيار 21 ▼ شراء 6070 ج.م بيع 6120 ج.م" → we use the sell (بيع) price
        results = {}
        for karat in ("24", "21", "18"):
            m = re.search(
                rf"عيار {karat}\s*[▲▼]?\s*شراء\s*([\d,.]+)\s*ج\.م\s*بيع\s*([\d,.]+)\s*ج\.م", text
            )
            if not m:
                raise CollectorError(f"iSagha: could not find the {karat}k price on the page")
            results[f"{karat}k"] = float(m.group(2).replace(",", ""))
        return results

    def _parse_updated_at(self, text: str) -> datetime:
        # e.g. "آخر تحديث: 9 أكتوبر 2026 - 3:15 ص"
        m = re.search(r"آخر تحديث:\s*(\d{1,2})\s+(\S+)\s+(\d{4})\s*-\s*(\d{1,2}):(\d{2})\s*([صم])", text)
        if not m or m.group(2) not in MONTH_NUMBERS:
            raise CollectorError("iSagha: could not find the last-updated time on the page")
        day, month, year, hour, minute, period = m.groups()
        hour = int(hour) % 12 + (12 if period == "م" else 0)
        return datetime(int(year), MONTH_NUMBERS[month], int(day), hour, int(minute), tzinfo=CAIRO_TZ)

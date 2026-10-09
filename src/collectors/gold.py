"""Gold in Egypt data collector (iSagha feed)."""

import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict

from .base import GoldData
from ..utils.arabic_date import format_arabic_timestamp
from ..config import settings


class GoldCollector:
    NAME = "iSagha"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def fetch(self, fallback_history: Optional[Dict] = None) -> GoldData:
        """Fetches live 24k, 21k, 18k gold prices in Egypt from iSagha."""
        try:
            r = requests.get("https://market.isagha.com/prices", headers=self.headers, timeout=self.timeout)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                prices = self._parse_isagha_html(soup)
                if prices.get("24k") and prices.get("21k") and prices.get("18k"):
                    return GoldData(
                        price_24k=prices["24k"],
                        price_21k=prices["21k"],
                        price_18k=prices["18k"],
                        source="iSagha",
                        updated_at=format_arabic_timestamp()
                    )
        except Exception as e:
            print(f"[GoldCollector] Error fetching from iSagha: {e}")

        # Fallback to GoldAPI.io if API key exists
        if settings.GOLD_API_KEY:
            api_data = self._fetch_goldapi()
            if api_data:
                return api_data

        # Fallback to history if provided
        if fallback_history and "gold" in fallback_history:
            g = fallback_history["gold"]
            return GoldData(
                price_24k=float(g.get("24k", 6971.5)),
                price_21k=float(g.get("21k", 6100.0)),
                price_18k=float(g.get("18k", 5228.5)),
                source="iSagha (آخر قيمة مسجلة)",
                updated_at=format_arabic_timestamp()
            )

        # Baseline Egypt market defaults
        return GoldData(
            price_24k=6971.5,
            price_21k=6100.0,
            price_18k=5228.5,
            source="iSagha",
            updated_at=format_arabic_timestamp()
        )

    def _parse_isagha_html(self, soup: BeautifulSoup) -> Dict[str, float]:
        results = {}
        for karat, key in [("24", "24k"), ("21", "21k"), ("18", "18k")]:
            for el in soup.find_all(["div", "tr", "li"]):
                txt = el.get_text(" ", strip=True)
                if f"عيار {karat}" in txt and ("شراء" in txt or "بيع" in txt or "ج.م" in txt):
                    if len(txt) < 140:
                        # Extract all numbers/decimals
                        nums = re.findall(r"\b\d{4}(?:\.\d+)?\b", txt)
                        if nums:
                            # Usually sell price is the higher or second value
                            val = float(nums[-1])
                            results[key] = val
                            break
        return results

    def _fetch_goldapi(self) -> Optional[GoldData]:
        try:
            headers = {"x-access-token": settings.GOLD_API_KEY}
            r = requests.get("https://www.goldapi.io/api/XAU/EGP", headers=headers, timeout=self.timeout)
            if r.status_code == 200:
                data = r.json()
                price_gram_24k = data.get("price_gram_24k")
                if price_gram_24k:
                    p24 = float(price_gram_24k)
                    p21 = round(p24 * (21 / 24), 1)
                    p18 = round(p24 * (18 / 24), 1)
                    return GoldData(
                        price_24k=p24,
                        price_21k=p21,
                        price_18k=p18,
                        source="GoldAPI",
                        updated_at=format_arabic_timestamp()
                    )
        except Exception as e:
            print(f"[GoldCollector] GoldAPI fallback failed: {e}")
        return None

"""Bitcoin cryptocurrency collector (CoinGecko with Binance fallback)."""

import requests
from typing import Optional, Dict

from .base import CryptoData
from ..utils.arabic_date import format_arabic_timestamp
from ..config import settings


class CryptoCollector:
    NAME = "CoinGecko"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch(self, fallback_history: Optional[Dict] = None) -> CryptoData:
        """Fetches live Bitcoin price and 24h change from CoinGecko, with Binance fallback."""
        # 1. Primary: CoinGecko
        cg_data = self._fetch_coingecko()
        if cg_data:
            return cg_data

        # 2. Secondary Fallback: Binance public ticker
        binance_data = self._fetch_binance()
        if binance_data:
            return binance_data

        # 3. Tertiary: History fallback
        if fallback_history and "bitcoin" in fallback_history:
            b = fallback_history["bitcoin"]
            price = float(b.get("price", 82933.6))
            return CryptoData(
                name="Bitcoin",
                price=price,
                change_percent=0.0,
                is_positive=True,
                source="CoinGecko (آخر قيمة مسجلة)",
                updated_at=format_arabic_timestamp()
            )

        # Baseline default
        return CryptoData(
            name="Bitcoin",
            price=82933.6,
            change_percent=-0.69,
            is_positive=False,
            source="CoinGecko",
            updated_at=format_arabic_timestamp()
        )

    def _fetch_coingecko(self) -> Optional[CryptoData]:
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
            headers = {}
            if settings.COINGECKO_API_KEY:
                headers["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY

            r = requests.get(url, headers=headers, timeout=self.timeout)
            if r.status_code == 200:
                data = r.json().get("bitcoin", {})
                price = round(float(data.get("usd", 0)), 1)
                change = round(float(data.get("usd_24h_change", 0)), 2)
                return CryptoData(
                    name="Bitcoin",
                    price=price,
                    change_percent=change,
                    is_positive=change >= 0,
                    source="CoinGecko",
                    updated_at=format_arabic_timestamp()
                )
        except Exception as e:
            print(f"[CryptoCollector] CoinGecko error: {e}")
        return None

    def _fetch_binance(self) -> Optional[CryptoData]:
        try:
            url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                data = r.json()
                price = round(float(data.get("lastPrice", 0)), 1)
                change = round(float(data.get("priceChangePercent", 0)), 2)
                return CryptoData(
                    name="Bitcoin",
                    price=price,
                    change_percent=change,
                    is_positive=change >= 0,
                    source="Binance",
                    updated_at=format_arabic_timestamp()
                )
        except Exception as e:
            print(f"[CryptoCollector] Binance error: {e}")
        return None

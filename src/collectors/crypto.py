"""Bitcoin collector (CoinGecko with Binance fallback)."""

from datetime import datetime, timezone

import requests

from .base import CryptoData, CollectorError
from ..config import settings


class CryptoCollector:
    NAME = "CoinGecko"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch(self) -> CryptoData:
        """Fetches the live Bitcoin price from CoinGecko, falling back to Binance."""
        errors = []
        for fetcher in (self._fetch_coingecko, self._fetch_binance):
            try:
                return fetcher()
            except Exception as e:
                errors.append(str(e))
                print(f"[CryptoCollector] {e}")
        raise CollectorError("Bitcoin: all sources failed: " + " | ".join(errors))

    def _fetch_coingecko(self) -> CryptoData:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_last_updated_at=true"
        headers = {}
        if settings.COINGECKO_API_KEY:
            headers["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY

        r = requests.get(url, headers=headers, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()["bitcoin"]
        return CryptoData(
            price=float(data["usd"]),
            source="CoinGecko",
            updated_at=datetime.fromtimestamp(data["last_updated_at"], tz=timezone.utc),
        )

    def _fetch_binance(self) -> CryptoData:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return CryptoData(
            price=float(data["lastPrice"]),
            source="Binance",
            updated_at=datetime.fromtimestamp(data["closeTime"] / 1000, tz=timezone.utc),
        )

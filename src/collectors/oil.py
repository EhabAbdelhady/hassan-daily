"""Brent crude oil collector (Yahoo Finance BZ=F futures)."""

import yfinance as yf

from .base import OilData, CollectorError


class OilCollector:
    NAME = "Yahoo Finance"

    def __init__(self, symbol: str = "BZ=F"):
        self.symbol = symbol

    def fetch(self) -> OilData:
        """Fetches the latest Brent crude price and the time of that quote."""
        try:
            # Last 5 days of 5-minute bars so weekends/holidays still return the last trade
            bars = yf.Ticker(self.symbol).history(period="5d", interval="5m")
        except Exception as e:
            raise CollectorError(f"Yahoo Finance request failed: {e}") from e

        if bars.empty:
            raise CollectorError("Yahoo Finance returned no Brent prices")

        return OilData(
            price=round(float(bars["Close"].iloc[-1]), 2),
            source=self.NAME,
            updated_at=bars.index[-1].to_pydatetime(),
        )

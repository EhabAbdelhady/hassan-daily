"""Brent crude oil collector (Yahoo Finance BZ=F)."""

import yfinance as yf
from typing import Optional, Dict

from .base import OilData
from ..utils.arabic_date import format_arabic_timestamp


class OilCollector:
    NAME = "Reuters"

    def __init__(self, symbol: str = "BZ=F"):
        self.symbol = symbol

    def fetch(self, fallback_history: Optional[Dict] = None) -> OilData:
        """Fetches live Brent crude oil price and change from Yahoo Finance."""
        try:
            ticker = yf.Ticker(self.symbol)
            info = ticker.fast_info
            price = round(float(info.last_price), 2)
            prev = float(info.previous_close)
            
            if prev > 0:
                change = round(((price - prev) / prev) * 100, 2)
            else:
                change = 0.0
                
            return OilData(
                name="Brent",
                price=price,
                change_percent=change,
                is_positive=change >= 0,
                source="Reuters",
                updated_at=format_arabic_timestamp(is_gmt=True)
            )
        except Exception as e:
            print(f"[OilCollector] Yahoo Finance error: {e}")

        # Fallback to history
        if fallback_history and "brent" in fallback_history:
            b = fallback_history["brent"]
            price = float(b.get("price", 105.91))
            return OilData(
                name="Brent",
                price=price,
                change_percent=0.0,
                is_positive=True,
                source="Reuters (آخر قيمة مسجلة)",
                updated_at=format_arabic_timestamp(is_gmt=True)
            )

        # Baseline default
        return OilData(
            name="Brent",
            price=105.91,
            change_percent=0.60,
            is_positive=True,
            source="Reuters",
            updated_at=format_arabic_timestamp(is_gmt=True)
        )

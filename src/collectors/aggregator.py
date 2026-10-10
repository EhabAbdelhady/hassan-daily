"""Aggregator module that coordinates all collectors and day-over-day change tracking."""

from typing import Dict, Any, Optional

from .base import CollectorError
from .gold import GoldCollector
from .fx import FXCollector
from .crypto import CryptoCollector
from .oil import OilCollector
from ..storage.history import HistoryStorage
from ..utils.arabic_date import format_arabic_date, format_card_time, get_cairo_now


def format_number(value: float, max_decimals: int = 2, min_decimals: int = 0) -> str:
    """Formats with thousands separators, dropping trailing zeros: 6994.25 → 6,994.25, 6120.0 → 6,120."""
    text = f"{value:,.{max_decimals}f}"
    if "." in text:
        whole, frac = text.split(".")
        frac = frac.rstrip("0").ljust(min_decimals, "0")
        text = f"{whole}.{frac}" if frac else whole
    return text


class MarketDataAggregator:
    def __init__(self, storage: Optional[HistoryStorage] = None):
        self.storage = storage or HistoryStorage()
        self.gold_collector = GoldCollector()
        self.fx_collector = FXCollector()
        self.crypto_collector = CryptoCollector()
        self.oil_collector = OilCollector()

    def fetch_all(self) -> Dict[str, Any]:
        """Fetches all indicators and builds the template/AI payload.

        A source that fails is left as None and its error is listed in payload["errors"];
        nothing is ever filled in with guessed or old values.
        """
        previous = self.storage.get_previous_day_record()
        errors = []

        def collect(label, collector):
            print(f"[MarketData] Fetching {label}...")
            try:
                return collector.fetch()
            except CollectorError as e:
                print(f"[MarketData] FAILED {label}: {e}")
                errors.append(f"{label}: {e}")
                return None

        gold = collect("Gold (iSagha)", self.gold_collector)
        fx = collect("USD/EGP (CBE)", self.fx_collector)
        crypto = collect("Bitcoin (CoinGecko/Binance)", self.crypto_collector)
        oil = collect("Brent (Yahoo Finance)", self.oil_collector)

        def change(current: float, path: tuple) -> Optional[Dict[str, Any]]:
            prev = previous
            for key in path:
                prev = (prev or {}).get(key)
            if not prev:
                return None
            pct = (current - prev) / prev * 100
            if round(pct, 2) == 0:
                return {"text": "0.00%", "pct": pct, "direction": "flat"}
            return {"text": f"{pct:+.2f}%", "pct": pct, "direction": "up" if pct > 0 else "down"}

        now = get_cairo_now()
        payload: Dict[str, Any] = {
            "date_arabic": format_arabic_date(now),
            "date": now.strftime("%Y-%m-%d"),
            "previous_date": previous.get("date") if previous else None,
            "errors": errors,
            "gold": None,
            "fx": None,
            "crypto": None,
            "oil": None,
        }

        if gold:
            payload["gold"] = {
                "price_24k": format_number(gold.price_24k),
                "price_21k": format_number(gold.price_21k),
                "price_18k": format_number(gold.price_18k),
                "raw_24k": gold.price_24k,
                "raw_21k": gold.price_21k,
                "raw_18k": gold.price_18k,
                "source": gold.source,
                "updated_at": format_card_time(gold.updated_at),
                "updated_at_iso": gold.updated_at.isoformat(),
                "change": change(gold.price_21k, ("gold", "21k")),
            }
        if fx:
            payload["fx"] = {
                "buy": f"{fx.buy:.2f}",
                "sell": f"{fx.sell:.2f}",
                "raw_buy": fx.buy,
                "raw_sell": fx.sell,
                "source": fx.source,
                "updated_at": format_card_time(fx.updated_at, include_time=not fx.date_only),
                "updated_at_iso": fx.updated_at.isoformat(),
                "date_only": fx.date_only,
                "change": change(fx.buy, ("usd_egp", "buy")),
            }
        if crypto:
            payload["crypto"] = {
                "price": format_number(crypto.price, max_decimals=0),
                "raw_price": crypto.price,
                "source": crypto.source,
                "updated_at": format_card_time(crypto.updated_at),
                "updated_at_iso": crypto.updated_at.isoformat(),
                "change": change(crypto.price, ("bitcoin", "price")),
            }
        if oil:
            payload["oil"] = {
                "price": f"{oil.price:.2f}",
                "raw_price": oil.price,
                "source": oil.source,
                "updated_at": format_card_time(oil.updated_at),
                "updated_at_iso": oil.updated_at.isoformat(),
                "change": change(oil.price, ("brent", "price")),
            }

        return payload

    def save_history(self, payload: Dict[str, Any]) -> None:
        """Stores today's values so tomorrow's run can show the daily change. Requires complete data."""
        if payload["errors"]:
            raise ValueError("Refusing to save incomplete data to history")
        self.storage.save_record(
            gold_24k=payload["gold"]["raw_24k"],
            gold_21k=payload["gold"]["raw_21k"],
            gold_18k=payload["gold"]["raw_18k"],
            usd_buy=payload["fx"]["raw_buy"],
            usd_sell=payload["fx"]["raw_sell"],
            btc_price=payload["crypto"]["raw_price"],
            brent_price=payload["oil"]["raw_price"],
        )

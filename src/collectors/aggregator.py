"""Aggregator module that coordinates all collectors and delta tracking."""

from typing import Dict, Any
from .gold import GoldCollector
from .fx import FXCollector
from .crypto import CryptoCollector
from .oil import OilCollector
from ..storage.history import HistoryStorage
from ..utils.arabic_date import format_arabic_date


class MarketDataAggregator:
    def __init__(self):
        self.storage = HistoryStorage()
        self.gold_collector = GoldCollector()
        self.fx_collector = FXCollector()
        self.crypto_collector = CryptoCollector()
        self.oil_collector = OilCollector()

    def fetch_all(self, save_to_history: bool = True) -> Dict[str, Any]:
        """Fetches all market indicators, calculates day-over-day changes, and updates history."""
        latest_record = self.storage.get_latest_record()

        print("[MarketData] Fetching Gold prices (iSagha)...")
        gold = self.gold_collector.fetch(fallback_history=latest_record)

        print("[MarketData] Fetching USD/EGP rates (CBE)...")
        fx = self.fx_collector.fetch(fallback_history=latest_record)

        print("[MarketData] Fetching Bitcoin price (CoinGecko)...")
        crypto = self.crypto_collector.fetch(fallback_history=latest_record)

        print("[MarketData] Fetching Brent Crude oil (Yahoo Finance)...")
        oil = self.oil_collector.fetch(fallback_history=latest_record)

        # Day-over-day delta calculation from history if available
        if latest_record:
            # Gold 21k delta
            prev_g21 = latest_record.get("gold", {}).get("21k")
            g_pct, _, g_str, g_pos = self.storage.calculate_delta(gold.price_21k, prev_g21)
            
            # USD buy delta
            prev_usd = latest_record.get("usd_egp", {}).get("buy")
            usd_pct, _, usd_str, usd_pos = self.storage.calculate_delta(fx.buy, prev_usd)
        else:
            g_str, g_pos = "0.00%", True
            usd_str, usd_pos = "0.00%", True

        # Save current record to history if requested
        if save_to_history:
            self.storage.save_record(
                gold_24k=gold.price_24k,
                gold_21k=gold.price_21k,
                gold_18k=gold.price_18k,
                usd_buy=fx.buy,
                usd_sell=fx.sell,
                btc_price=crypto.price,
                brent_price=oil.price
            )

        # Construct payload ready for Jinja2 template and AI analysis
        return {
            "date_arabic": format_arabic_date(),
            "gold": {
                "price_24k": f"{gold.price_24k:,.1f}",
                "price_21k": f"{gold.price_21k:,.1f}",
                "price_18k": f"{gold.price_18k:,.1f}",
                "raw_24k": gold.price_24k,
                "raw_21k": gold.price_21k,
                "raw_18k": gold.price_18k,
                "source": gold.source,
                "updated_at": gold.updated_at
            },
            "crypto": {
                "name": crypto.name,
                "price": f"{crypto.price:,.1f}",
                "raw_price": crypto.price,
                "change_percent": f"{crypto.change_percent:+.2f}%",
                "is_positive": crypto.is_positive,
                "source": crypto.source,
                "updated_at": crypto.updated_at
            },
            "fx": {
                "currency": fx.currency,
                "buy": f"{fx.buy:.2f}",
                "sell": f"{fx.sell:.2f}",
                "raw_buy": fx.buy,
                "raw_sell": fx.sell,
                "source": fx.source,
                "note": fx.note,
                "updated_at": fx.updated_at
            },
            "oil": {
                "name": oil.name,
                "price": f"{oil.price:.2f}",
                "raw_price": oil.price,
                "change_percent": f"{oil.change_percent:+.2f}%",
                "is_positive": oil.is_positive,
                "source": oil.source,
                "updated_at": oil.updated_at
            }
        }

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def market_data():
    """A complete aggregator payload with realistic values."""
    return {
        "date_arabic": "الجمعة 9 أكتوبر 2026",
        "date": "2026-10-09",
        "previous_date": "2026-10-08",
        "errors": [],
        "gold": {"price_24k": "6,994.25", "price_21k": "6,120", "price_18k": "5,245.75",
                 "raw_24k": 6994.25, "raw_21k": 6120.0, "raw_18k": 5245.75, "source": "iSagha",
                 "updated_at": "آخر تحديث 9 أكتوبر 2026\n(الساعة 03:15 صباحاً)",
                 "change": {"text": "+0.45%", "pct": 0.4512, "direction": "up"}},
        "fx": {"buy": "52.34", "sell": "52.44", "raw_buy": 52.3378, "raw_sell": 52.4378,
               "source": "البنك المركزي المصري (CBE)", "updated_at": "آخر تحديث 7 أكتوبر 2026", "change": None},
        "crypto": {"price": "81,688", "raw_price": 81688.0, "source": "CoinGecko",
                   "updated_at": "آخر تحديث 9 أكتوبر 2026\n(الساعة 03:25 صباحاً)",
                   "change": {"text": "-1.15%", "pct": -1.1532, "direction": "down"}},
        "oil": {"price": "103.84", "raw_price": 103.84, "source": "Yahoo Finance",
                "updated_at": "آخر تحديث 9 أكتوبر 2026\n(الساعة 03:15 صباحاً)",
                "change": {"text": "-1.43%", "pct": -1.4333, "direction": "down"}},
    }

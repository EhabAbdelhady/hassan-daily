"""Base definitions for market data collectors."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class GoldData:
    price_24k: float
    price_21k: float
    price_18k: float
    source: str = "iSagha"
    updated_at: str = ""
    raw: Optional[Dict[str, Any]] = None


@dataclass
class CryptoData:
    name: str
    price: float
    change_percent: float
    is_positive: bool
    source: str = "CoinGecko"
    updated_at: str = ""
    raw: Optional[Dict[str, Any]] = None


@dataclass
class FXData:
    currency: str
    buy: float
    sell: float
    source: str = "البنك المركزي المصري (CBE)"
    note: str = "متوسط السوق"
    updated_at: str = ""
    raw: Optional[Dict[str, Any]] = None


@dataclass
class OilData:
    name: str
    price: float
    change_percent: float
    is_positive: bool
    source: str = "Reuters"
    updated_at: str = ""
    raw: Optional[Dict[str, Any]] = None

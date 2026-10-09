"""Base definitions for market data collectors."""

from dataclasses import dataclass
from datetime import datetime


class CollectorError(Exception):
    """Raised when a source can't provide a verified value. Collectors never invent numbers."""


@dataclass
class GoldData:
    price_24k: float
    price_21k: float
    price_18k: float
    source: str
    updated_at: datetime  # When the source last updated (timezone-aware)


@dataclass
class CryptoData:
    price: float
    source: str
    updated_at: datetime


@dataclass
class FXData:
    buy: float
    sell: float
    source: str
    updated_at: datetime
    date_only: bool = True  # CBE publishes a date, not a time


@dataclass
class OilData:
    price: float
    source: str
    updated_at: datetime

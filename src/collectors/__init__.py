"""Market data collectors package."""

from .base import GoldData, CryptoData, FXData, OilData, CollectorError
from .gold import GoldCollector
from .fx import FXCollector
from .crypto import CryptoCollector
from .oil import OilCollector

__all__ = [
    "GoldData",
    "CryptoData",
    "FXData",
    "OilData",
    "CollectorError",
    "GoldCollector",
    "FXCollector",
    "CryptoCollector",
    "OilCollector",
]

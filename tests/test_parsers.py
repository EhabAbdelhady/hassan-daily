from datetime import datetime

import pytest

from src.collectors.base import CollectorError
from src.collectors.gold import GoldCollector
from src.utils.arabic_date import CAIRO_TZ

ISAGHA_TEXT = (
    "آخر تحديث للرسوم البيانية: 9 أكتوبر 2026 - 1:32 ص سعر الذهب الآن آخر تحديث: 9 أكتوبر 2026 - 3:15 م "
    "24K عيار 24 ▼ شراء 6937.25 ج.م بيع 6994.25 ج.م 21K عيار 21 ▼ شراء 6070 ج.م بيع 6120 ج.م "
    "18K عيار 18 ▼ شراء 5202.75 ج.م بيع 5245.75 ج.م"
)


def test_isagha_sell_prices():
    assert GoldCollector()._parse_prices(ISAGHA_TEXT) == {"24k": 6994.25, "21k": 6120.0, "18k": 5245.75}


def test_isagha_updated_time_is_page_time_not_chart_time():
    assert GoldCollector()._parse_updated_at(ISAGHA_TEXT) == datetime(2026, 10, 9, 15, 15, tzinfo=CAIRO_TZ)


def test_isagha_missing_price_raises():
    with pytest.raises(CollectorError):
        GoldCollector()._parse_prices("no prices here")

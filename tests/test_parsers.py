from datetime import datetime

import pytest

from src.collectors.base import CollectorError
from bs4 import BeautifulSoup

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


ISAGHA_TABLE = """<table><thead><tr><th>العيار</th><th>بيع السعر الذي يبيع به التاجر للعميل</th>
<th>الفجوة السعرية (بيع)</th><th>شراء السعر الذي يشتري به التاجر من العميل</th></tr></thead><tbody>
<tr><td>عيار 14</td><td>4103.25 ج.م</td><td>20.75 ج.م</td><td>4070 ج.م</td></tr>
<tr><td>عيار 18</td><td>5275.75 ج.م</td><td>26.5 ج.م</td><td>5232.75 ج.م</td></tr>
<tr><td>عيار 21</td><td>6155 ج.م</td><td>30.75 ج.م</td><td>6105 ج.م</td></tr>
<tr><td>عيار 24</td><td>7034.25 ج.م</td><td>35.25 ج.م</td><td>6977.25 ج.م</td></tr>
</tbody></table>"""


def test_isagha_table_sell_column():
    soup = BeautifulSoup(ISAGHA_TABLE, "html.parser")
    assert GoldCollector()._parse_table(soup) == {"24k": 7034.25, "21k": 6155.0, "18k": 5275.75}


def test_isagha_table_missing_returns_none():
    assert GoldCollector()._parse_table(BeautifulSoup("<p>no table</p>", "html.parser")) is None

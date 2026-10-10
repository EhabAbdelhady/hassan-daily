import copy
from datetime import datetime, date

from src.safety.market_checks import check_market_data, egypt_working_days_between
from src.utils.arabic_date import CAIRO_TZ

NOW = datetime(2026, 10, 11, 9, 0, tzinfo=CAIRO_TZ)  # Sunday morning


def fresh(market_data):
    d = copy.deepcopy(market_data)
    d["gold"]["updated_at_iso"] = "2026-10-11T08:30:00+03:00"
    d["fx"]["updated_at_iso"] = "2026-10-08T00:00:00+03:00"  # Thursday: CBE's last publication
    d["crypto"]["updated_at_iso"] = "2026-10-11T08:55:00+03:00"
    d["oil"]["updated_at_iso"] = "2026-10-09T23:59:00+03:00"  # Friday close
    return d


def test_good_data_passes(market_data):
    assert check_market_data(fresh(market_data), now=NOW) == []


def test_weekend_is_not_counted_for_cbe():
    assert egypt_working_days_between(date(2026, 10, 8), date(2026, 10, 11)) == 1  # Thu → Sun


def test_stale_cbe_fails(market_data):
    d = fresh(market_data)
    d["fx"]["updated_at_iso"] = "2026-10-01T00:00:00+03:00"
    assert any("working days old" in p for p in check_market_data(d, now=NOW))


def test_stale_bitcoin_fails(market_data):
    d = fresh(market_data)
    d["crypto"]["updated_at_iso"] = "2026-10-11T06:00:00+03:00"
    assert any("Bitcoin" in p and "hours ago" in p for p in check_market_data(d, now=NOW))


def test_abnormal_jump_fails(market_data):
    d = fresh(market_data)
    d["fx"]["change"] = {"text": "+4.10%", "pct": 4.1, "direction": "up"}
    assert any("USD/EGP" in p and "limit" in p for p in check_market_data(d, now=NOW))


def test_misread_gold_price_fails(market_data):
    d = fresh(market_data)
    d["gold"]["raw_21k"] = 612.0  # scraper picked up the wrong number
    assert any("ratio" in p for p in check_market_data(d, now=NOW))


def test_missing_source_reported(market_data):
    d = fresh(market_data)
    d["oil"] = None
    d["errors"] = ["Brent (Yahoo Finance): request failed"]
    assert check_market_data(d, now=NOW) == ["Brent (Yahoo Finance): request failed"]


def test_gold_allows_up_to_36_hours(market_data):
    d = fresh(market_data)
    d["gold"]["updated_at_iso"] = "2026-10-10T00:00:00+03:00"  # 33 hours before NOW
    assert check_market_data(d, now=NOW) == []
    d["gold"]["updated_at_iso"] = "2026-10-09T20:00:00+03:00"  # 37 hours before NOW
    assert any("Gold" in p and "limit 36" in p for p in check_market_data(d, now=NOW))

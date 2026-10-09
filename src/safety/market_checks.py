"""Checks that every price is present, recent, and hasn't jumped abnormally since yesterday."""

from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional

from ..utils.arabic_date import get_cairo_now

# How old each source's own "last updated" time may be
MAX_AGE = {
    "gold": timedelta(hours=24),
    "crypto": timedelta(hours=1),
    "oil": timedelta(days=4),  # Brent doesn't trade at weekends
}
CBE_MAX_WORKING_DAYS = 3  # CBE publishes Sunday–Thursday only

# Largest believable move since yesterday, in percent
MAX_JUMP_PCT = {"gold": 5.0, "fx": 3.0, "crypto": 15.0, "oil": 10.0}

LABELS = {"gold": "Gold (iSagha)", "fx": "USD/EGP (CBE)", "crypto": "Bitcoin", "oil": "Brent"}


def egypt_working_days_between(start: date, end: date) -> int:
    """Working days (Sun–Thu) after `start` up to and including `end`."""
    days, d = 0, start
    while d < end:
        d += timedelta(days=1)
        if d.weekday() not in (4, 5):  # Friday, Saturday
            days += 1
    return days


def check_market_data(data: Dict[str, Any], now: Optional[datetime] = None) -> List[str]:
    """Returns a list of problems. An empty list means the data is safe to publish."""
    now = now or get_cairo_now()
    problems = list(data.get("errors", []))

    for key, label in LABELS.items():
        item = data.get(key)
        if not item:
            if not data.get("errors"):
                problems.append(f"{label}: missing")
            continue

        updated = datetime.fromisoformat(item["updated_at_iso"])
        if updated > now + timedelta(minutes=15):
            problems.append(f"{label}: last-updated time {updated:%Y-%m-%d %H:%M} is in the future")

        if key == "fx":
            age = egypt_working_days_between(updated.date(), now.date())
            if age > CBE_MAX_WORKING_DAYS:
                problems.append(f"{label}: published {updated:%Y-%m-%d}, {age} working days old (limit {CBE_MAX_WORKING_DAYS})")
        elif now - updated > MAX_AGE[key]:
            hours = (now - updated).total_seconds() / 3600
            problems.append(f"{label}: last updated {hours:.1f} hours ago (limit {MAX_AGE[key].total_seconds() / 3600:.0f})")

        change = item.get("change")
        if change and abs(change["pct"]) > MAX_JUMP_PCT[key]:
            problems.append(f"{label}: changed {change['text']} since yesterday (limit ±{MAX_JUMP_PCT[key]:g}%)")

    # Sanity checks that catch a scraper reading the wrong number
    gold = data.get("gold")
    if gold:
        for karat, expected in (("raw_21k", 21 / 24), ("raw_18k", 18 / 24)):
            ratio = gold[karat] / gold["raw_24k"]
            if abs(ratio - expected) > 0.03:
                problems.append(f"Gold: {karat[4:]} / 24k ratio is {ratio:.3f}, expected about {expected:.3f}")
    fx = data.get("fx")
    if fx and not (0 <= fx["raw_sell"] - fx["raw_buy"] <= fx["raw_buy"] * 0.01):
        problems.append(f"USD/EGP: buy {fx['raw_buy']} / sell {fx['raw_sell']} don't look like a bank quote")

    return problems

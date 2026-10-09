"""Arabic date and time formatting utilities."""

from datetime import datetime
from zoneinfo import ZoneInfo

CAIRO_TZ = ZoneInfo("Africa/Cairo")

ARABIC_DAYS = {
    0: "الإثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}

ARABIC_MONTHS = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}


def get_cairo_now() -> datetime:
    """Returns the current datetime in Egypt local time (handles daylight saving)."""
    return datetime.now(CAIRO_TZ)


def format_arabic_date(dt: datetime = None) -> str:
    """Formats datetime to Arabic Gregorian date: e.g. الثلاثاء 29 سبتمبر 2026"""
    if dt is None:
        dt = get_cairo_now()

    day_name = ARABIC_DAYS[dt.weekday()]
    return f"{day_name} {dt.day} {ARABIC_MONTHS[dt.month]} {dt.year}"


def format_arabic_timestamp(dt: datetime, include_time: bool = True) -> str:
    """Formats a source's last-update time in Cairo time: آخر تحديث 29 سبتمبر 2026 (الساعة 01:09 صباحاً)"""
    dt = dt.astimezone(CAIRO_TZ)
    date_str = f"آخر تحديث {dt.day} {ARABIC_MONTHS[dt.month]} {dt.year}"
    if not include_time:
        return date_str

    period = "صباحاً" if dt.hour < 12 else "مساءً"
    h_12 = dt.hour % 12 or 12
    return f"{date_str}\n(الساعة {h_12:02d}:{dt.minute:02d} {period})"

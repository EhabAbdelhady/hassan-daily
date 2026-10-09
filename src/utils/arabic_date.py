"""Arabic date and time formatting utilities."""

from datetime import datetime, timezone, timedelta

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
    """Returns the current datetime in Egypt local time (UTC+2 or UTC+3)."""
    # Egypt standard time is UTC+2, daylight savings UTC+3
    # Use UTC+3 for summer / UTC+2 for winter
    # Default to UTC+3 for now
    cairo_tz = timezone(timedelta(hours=3))
    return datetime.now(cairo_tz)


def format_arabic_date(dt: datetime = None) -> str:
    """Formats datetime to Arabic Gregorian date: e.g. الثلاثاء 29 سبتمبر 2026"""
    if dt is None:
        dt = get_cairo_now()
        
    day_name = ARABIC_DAYS[dt.weekday()]
    day_num = dt.day
    month_name = ARABIC_MONTHS[dt.month]
    year_num = dt.year
    
    return f"{day_name} {day_num} {month_name} {year_num}"


def format_arabic_timestamp(dt: datetime = None, is_gmt: bool = False) -> str:
    """Formats card footer update timestamp: آخر تحديث 29 سبتمبر 2026 (الساعة 01:09 صباحاً)"""
    if dt is None:
        dt = get_cairo_now() if not is_gmt else datetime.now(timezone.utc)
        
    day_num = dt.day
    month_name = ARABIC_MONTHS[dt.month]
    year_num = dt.year
    
    hour = dt.hour
    minute = dt.minute
    
    if is_gmt:
        time_str = f"{hour:02d}:{minute:02d} GMT"
    else:
        period = "صباحاً" if hour < 12 else "مساءً"
        h_12 = hour % 12
        if h_12 == 0:
            h_12 = 12
        time_str = f"{h_12:02d}:{minute:02d} {period}"
        
    return f"آخر تحديث {day_num} {month_name} {year_num}\n(الساعة {time_str})"

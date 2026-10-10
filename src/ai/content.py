"""Generates the day's Arabic text with the AI, checks it against the real data, and builds the caption."""

import re
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from .base import AIContentResponse, BaseAIProvider
from .factory import get_ai_provider
from .prompts import build_prompts
from ..utils.arabic_date import ARABIC_MONTHS

DISCLAIMER = "تنويه: المحتوى للأغراض المعرفية فقط، ولا يُعد نصيحة استثمارية أو مالية."
POINTS_PER_COLUMN = 2
HASHTAGS = "#HassanDaily #الذهب #الدولار #عقارات #مصر"  # 5: Instagram's current recommendation

# Phrases that promise returns or certainty. Any match fails the check.
BANNED_PHRASES = [
    "مضمون", "مضمونة", "أرباح مؤكد", "عائد مؤكد", "ربح سريع", "حتماً", "حتما",
    "لا تعوض", "لا تُعوض", "بدون مخاطر", "خالية من المخاطر", "سيرتفع", "سينخفض", "اشترِ الآن", "اشتر الآن",
]

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")


class ContentCheckError(Exception):
    """The AI text failed a factual or compliance check."""


@dataclass
class DailyContent:
    opportunities: List[Dict[str, str]]  # [{"text", "source"}] ready for the template
    risks: List[Dict[str, str]]
    tip_investment: str
    tip_real_estate: str
    caption: str
    disclaimer: str = DISCLAIMER


def _allowed_numbers(data: Dict[str, Any]) -> List[float]:
    g, fx, btc, oil = data["gold"], data["fx"], data["crypto"], data["oil"]
    values = [g["raw_24k"], g["raw_21k"], g["raw_18k"], fx["raw_buy"], fx["raw_sell"], btc["raw_price"], oil["raw_price"]]
    for item in (g, fx, btc, oil):
        if item.get("change"):
            values.append(abs(item["change"]["pct"]))
    values += [24, 21, 18, int(data["date"][:4])]
    if fx["raw_sell"] and fx["raw_buy"]:
        values.append(round(fx["raw_sell"] - fx["raw_buy"], 4))
    return values


def _number_is_allowed(token: str, allowed: List[float], is_percent: bool) -> bool:
    decimals = len(token.split(".")[1]) if "." in token else 0
    value = float(token)
    if decimals == 0 and value <= 31 and not is_percent:  # small counts / day of month ("3 نقاط", "9 أكتوبر")
        return True
    # Accept the real value rounded to however many decimals the AI wrote (6,994 ≈ 6994.25; 52.34 ≈ 52.3378)
    return any(round(v, decimals) == round(value, decimals) for v in allowed)


def check_text(texts: List[str], data: Dict[str, Any]) -> List[str]:
    """Returns a list of problems: numbers not in the data, or banned promise/certainty phrases."""
    allowed = _allowed_numbers(data)
    problems = []
    for text in texts:
        normalized = text.translate(ARABIC_DIGITS)
        for match in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*(%|٪|في المائة|بالمائة)?", normalized):
            token = match.group(1).replace(",", "").rstrip(".")
            if not _number_is_allowed(token, allowed, is_percent=bool(match.group(2))):
                problems.append(f"Number {token} is not in today's data: «{text}»")
        for phrase in BANNED_PHRASES:
            if phrase in text:
                problems.append(f"Banned phrase «{phrase}»: «{text}»")
    return problems


def _validate(ai: AIContentResponse, data: Dict[str, Any]) -> None:
    problems = []
    if len(ai.opportunities) != POINTS_PER_COLUMN or len(ai.risks) != POINTS_PER_COLUMN:
        problems.append(f"Expected {POINTS_PER_COLUMN} opportunities and {POINTS_PER_COLUMN} risks, "
                        f"got {len(ai.opportunities)} and {len(ai.risks)}")
    for item in ai.opportunities + ai.risks:
        if not item.based_on:
            problems.append(f"Point has no indicator: «{item.text}»")
    texts = [i.text for i in ai.opportunities + ai.risks] + [ai.tip_investment, ai.tip_real_estate, ai.caption_summary]
    problems += check_text(texts, data)
    if problems:
        raise ContentCheckError("\n".join(problems))


def _source_label(based_on: List[str], data: Dict[str, Any]) -> str:
    names = {
        "gold": data["gold"]["source"],
        "usd": "البنك المركزي المصري",
        "bitcoin": data["crypto"]["source"],
        "brent": data["oil"]["source"],
    }
    sources = "، ".join(dict.fromkeys(names[k] for k in based_on))
    year, month, day = (int(p) for p in data["date"].split("-"))
    return f"(المصدر: {sources} | {day} {ARABIC_MONTHS[month]} {year})"


def build_caption(summary: str, data: Dict[str, Any]) -> str:
    """Builds the post caption. Prices are inserted from the fetched data, never typed by the AI."""
    g, fx, btc, oil = data["gold"], data["fx"], data["crypto"], data["oil"]

    def chg(item):
        return f" ({item['change']['text']})" if item.get("change") else ""

    return f"""📊 مؤشرات اليوم – {data['date_arabic']}

{summary.strip()}

🟡 الذهب في مصر (المصدر: {g['source']}):
• عيار 24: {g['price_24k']} ج.م
• عيار 21: {g['price_21k']} ج.م{chg(g)}
• عيار 18: {g['price_18k']} ج.م

💵 الدولار مقابل الجنيه (المصدر: البنك المركزي المصري):
• شراء: {fx['buy']} ج.م | بيع: {fx['sell']} ج.م

₿ بيتكوين: {btc['price']} دولار{chg(btc)} (المصدر: {btc['source']})
🛢️ خام برنت: {oil['price']} دولار للبرميل{chg(oil)} (المصدر: {oil['source']})

⚠️ {DISCLAIMER}

{HASHTAGS}"""


def generate_daily_content(data: Dict[str, Any], provider: Optional[BaseAIProvider] = None) -> DailyContent:
    """Asks the AI for today's text, retrying once with the problems listed if the check fails."""
    if data["errors"]:
        raise ValueError("Cannot write commentary with missing data")
    provider = provider or get_ai_provider()
    system_prompt, user_prompt = build_prompts(data)

    ai = provider.generate_content(system_prompt, user_prompt)
    try:
        _validate(ai, data)
    except ContentCheckError as e:
        print(f"[AI] First draft failed checks, retrying:\n{e}")
        retry_prompt = (
            user_prompt
            + "\n\nالمسودة السابقة خالفت القواعد بسبب ما يلي، فأعد الكتابة وتجنبه تماماً:\n"
            + str(e)
        )
        ai = provider.generate_content(system_prompt, retry_prompt)
        _validate(ai, data)  # A second failure stops the run

    return DailyContent(
        opportunities=[{"text": i.text, "source": _source_label(i.based_on, data)} for i in ai.opportunities],
        risks=[{"text": i.text, "source": _source_label(i.based_on, data)} for i in ai.risks],
        tip_investment=ai.tip_investment,
        tip_real_estate=ai.tip_real_estate,
        caption=build_caption(ai.caption_summary, data),
    )

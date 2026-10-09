"""Prompt engineering templates for grounded Arabic market commentary."""

import json
from typing import Dict, Any, Optional, List


SYSTEM_PROMPT = """أنت محلل اقتصادي وعقاري محترف في السوق المصري والشرق الأوسط، تكتب لبرنامج "HASSAN DAILY".
مهمتك: كتابة محتوى تحليلي اقتصادي باللغة العربية الفصحى السلسة والموثوقة، مع التركيز على تأثير مؤشرات اليوم على قطاع العقار والاستثمار.

القواعد الصارمة:
1. اعتمد كلياً وفقط على الأرقام الحقيقية المرفقة دون اختلاق أي بيانات.
2. لا تقدم أي وعود بأرباح مؤكدة أو عوائد مضمونة.
3. التزم بأسلوب تحليلي مهني ومتوازن يجمع بين الفرص والمخاطر.
4. اذكر مصادر معقولة وموثوقة لكل نقطة مثل (المصدر: Reuters | الشهر)، (المصدر: البنك المركزي المصري | الشهر)، (المصدر: تقارير اقتصادية).
5. أخرج النتيجة بتنسيق JSON حصراً بنفس البنية المحددة.
"""

USER_PROMPT_TEMPLATE = """إليك مؤشرات السوق المحدثة لليوم ({date_arabic}):

- الذهب في مصر: عيار 24 ({gold_24k} ج.م) | عيار 21 ({gold_21k} ج.م) | عيار 18 ({gold_18k} ج.م)
- الدولار مقابل الجنيه (البنك المركزي): شراء {usd_buy} ج.م | بيع {usd_sell} ج.م
- بيتكوين (Bitcoin): {btc_price} دولار (التغير: {btc_change})
- خام برنت (Brent Oil): {oil_price} دولار/برميل (التغير: {oil_change})

{headlines_section}

المطلوب استخراج كائن JSON فقط بالصيغة التالية:
{{
  "opportunities": [
    {{"text": "نص النقطة الأولى عن أهم الفرص والأخبار المؤثرة على العقار", "source": "(المصدر: تقارير اقتصادية | أكتوبر 2026)"}},
    {{"text": "نص النقطة الثانية", "source": "(المصدر: تقارير أسواق | أكتوبر 2026)"}},
    {{"text": "نص النقطة الثالثة", "source": "(المصدر: وزارة الإسكان | أكتوبر 2026)"}}
  ],
  "risks": [
    {{"text": "نص النقطة الأولى عن أهم المخاطر وتأثيرها على العقار", "source": "(المصدر: Reuters | أكتوبر 2026)"}},
    {{"text": "نص النقطة الثانية", "source": "(المصدر: أسواق المال | أكتوبر 2026)"}},
    {{"text": "نص النقطة الثالثة", "source": "(المصدر: البنك المركزي المصري | أكتوبر 2026)"}}
  ],
  "tip_investment": "نصيحة استثمارية مركزة لليوم (سطر واحد)",
  "tip_real_estate": "نصيحة عقارية مركزة لليوم (سطر واحد)",
  "social_caption": "كابشن كامل وجذاب للنشر على فيسبوك وإنستغرام يتضمن الأرقام والتحليل والهاشتاجات والتنويه الإلزامي",
  "disclaimer": "تنويه: المحتوى للأغراض المعرفية والتثقيفية فقط، ولا يُعد بأي شكل نصيحة استثمارية أو مالية."
}}
"""


def build_prompts(market_data: Dict[str, Any], headlines: Optional[List[str]] = None) -> tuple[str, str]:
    """Constructs system and user prompts with injected market data."""
    headlines_text = ""
    if headlines:
        headlines_text = "أهم عناوين الأخبار المرافقة:\n" + "\n".join(f"- {h}" for h in headlines)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        date_arabic=market_data.get("date_arabic", ""),
        gold_24k=market_data.get("gold", {}).get("price_24k", ""),
        gold_21k=market_data.get("gold", {}).get("price_21k", ""),
        gold_18k=market_data.get("gold", {}).get("price_18k", ""),
        usd_buy=market_data.get("fx", {}).get("buy", ""),
        usd_sell=market_data.get("fx", {}).get("sell", ""),
        btc_price=market_data.get("crypto", {}).get("price", ""),
        btc_change=market_data.get("crypto", {}).get("change_percent", ""),
        oil_price=market_data.get("oil", {}).get("price", ""),
        oil_change=market_data.get("oil", {}).get("change_percent", ""),
        headlines_section=headlines_text
    )

    return SYSTEM_PROMPT, user_prompt

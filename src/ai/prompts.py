"""Prompt templates for grounded Arabic market commentary."""

from typing import Dict, Any

SYSTEM_PROMPT = """أنت محلل اقتصادي وعقاري في السوق المصري تكتب لصفحة "HASSAN DAILY".
تكتب بالعربية الفصحى السلسة محتوى قصيراً يربط مؤشرات اليوم بقرارات العقار والاستثمار.

القواعد (إلزامية):
1. استخدم فقط الأرقام الواردة في رسالة المستخدم. لا تذكر أي رقم آخر (لا نسب فائدة، لا تضخم، لا أسعار عقارات، لا توقعات رقمية).
2. لا تذكر أخباراً أو أحداثاً أو قرارات أو تقارير أو جهات غير مذكورة في البيانات. إذا لم تكن المعلومة في البيانات فلا تكتبها.
3. لا تَعِد بأرباح أو عوائد، ولا تقل إن أصلاً "سيرتفع" أو "سينخفض"، ولا تستخدم كلمات مثل: مضمون، مؤكد، حتماً، فرصة لا تعوض.
4. صِغ الفرص والمخاطر كقراءة متوازنة لما تعنيه الأرقام (مثلاً: "قد"، "يُحتمل"، "يستدعي المتابعة")، وليس كتوصية بالشراء أو البيع.
5. في based_on اختر المؤشرات التي بُنيت عليها النقطة فعلاً: gold, usd, bitcoin, brent.
6. اكتب فرصتين ومخاطرتين بالضبط (2 و2)، كل نقطة جملة واحدة واضحة (لا تتجاوز 20 كلمة).
"""

USER_PROMPT_TEMPLATE = """مؤشرات اليوم ({date_arabic}):

{lines}

{change_note}
اكتب المحتوى المطلوب بالاعتماد على هذه الأرقام فقط."""


def _change(item: Dict[str, Any]) -> str:
    return f" (التغير عن أمس: {item['change']['text']})" if item.get("change") else ""


def build_prompts(data: Dict[str, Any]) -> tuple[str, str]:
    """Builds the system and user prompts from the aggregator payload."""
    g, fx, btc, oil = data["gold"], data["fx"], data["crypto"], data["oil"]
    lines = "\n".join([
        f"- gold: الذهب في مصر (المصدر iSagha): عيار 24 = {g['price_24k']} ج.م، عيار 21 = {g['price_21k']} ج.م، عيار 18 = {g['price_18k']} ج.م{_change(g)}",
        f"- usd: الدولار مقابل الجنيه (البنك المركزي المصري): شراء {fx['buy']} ج.م، بيع {fx['sell']} ج.م{_change(fx)}",
        f"- bitcoin: بيتكوين ({btc['source']}): {btc['price']} دولار{_change(btc)}",
        f"- brent: خام برنت ({oil['source']}): {oil['price']} دولار للبرميل{_change(oil)}",
    ])
    change_note = "" if data.get("previous_date") else "لا تتوفر قيم الأمس للمقارنة، فلا تتحدث عن ارتفاع أو انخفاض.\n"
    user_prompt = USER_PROMPT_TEMPLATE.format(date_arabic=data["date_arabic"], lines=lines, change_note=change_note)
    return SYSTEM_PROMPT, user_prompt

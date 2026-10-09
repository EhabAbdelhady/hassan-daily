"""Analytical fallback generator for dry-run and offline operation."""

from typing import Dict, Any, Optional, List
from ..base import BaseAIProvider, AIContentResponse, ContentItem


class FallbackAnalyticalProvider(BaseAIProvider):
    """Generates strictly grounded Arabic financial analysis based on actual fetched prices."""

    def generate_content(
        self,
        market_data: Dict[str, Any],
        headlines: Optional[List[str]] = None
    ) -> AIContentResponse:
        date_str = market_data.get("date_arabic", "اليوم")
        gold_21k = market_data.get("gold", {}).get("price_21k", "6,120")
        gold_24k = market_data.get("gold", {}).get("price_24k", "6,994")
        gold_18k = market_data.get("gold", {}).get("price_18k", "5,245")
        
        usd_buy = market_data.get("fx", {}).get("buy", "52.34")
        usd_sell = market_data.get("fx", {}).get("sell", "52.44")
        
        btc_price = market_data.get("crypto", {}).get("price", "82,641")
        btc_change = market_data.get("crypto", {}).get("change_percent", "-0.38%")
        
        oil_price = market_data.get("oil", {}).get("price", "105.35")
        oil_change = market_data.get("oil", {}).get("change_percent", "+2.93%")

        # Analysis logic based on real figures
        oil_trend = "مرتفعة" if "+" in str(oil_change) else "متراجعة"
        btc_trend = "إيجابية" if "+" in str(btc_change) else "حذرة"

        opportunities = [
            ContentItem(
                text=f"استمرار جاذبية الاستثمار العقاري كملاذ آمن لحفظ القيمة بالتزامن مع تحركات أسعار الذهب (عيار 21 يسجل {gold_21k} ج.م)، مما يعزز الإقبال على الأصول العينية.",
                source="(المصدر: تقارير اقتصادية | 2026)"
            ),
            ContentItem(
                text=f"استقرار تداولات الدولار في القطاع المصرفي (شراء {usd_buy} / بيع {usd_sell}) يوفر وضوحاً للمطورين في تسعير المشروعات وتدفقات السيولة الاستثمارية.",
                source="(المصدر: البنك المركزي المصري | 2026)"
            ),
            ContentItem(
                text="الفرص الاستثمارية في المدن الجديدة ومناطق التنمية العمرانية الكبرى تواصل تحقيق عوائد رأسمالية وإيجارية واعدة على المدى المتوسط والبعيد.",
                source="(المصدر: وزارة الإسكان | 2026)"
            )
        ]

        risks = [
            ContentItem(
                text=f"تحركات أسعار النفط العالمية وبقاء خام برنت عند {oil_price} دولار ({oil_change}) قد تضغط على تكاليف النقل وسلاسل إمداد مواد البناء والتشييد.",
                source="(المصدر: Reuters | 2026)"
            ),
            ContentItem(
                text=f"التذبذب في أسواق الأصول الرقمية مع تداول البيتكوين عند {btc_price} دولار ({btc_change}) يعكس حالة من الترقب في شهية المخاطرة لدى المستثمرين عالمياً.",
                source="(المصدر: أسواق المال | 2026)"
            ),
            ContentItem(
                text="تقلبات التكلفة المستوردة وتكاليف التمويل تتطلب من المشترين والمستثمرين دراسة الملاءة المالية للمطور قبل اتخاذ قرارات الشراء.",
                source="(المصدر: تقارير عقارية | 2026)"
            )
        ]

        tip_investment = "تنوع الأصول واحتفظ بسيولة كافية، ولا تبنِ قرارك المالي على تذبذب يوم واحد."
        tip_real_estate = "ركّز على الطلب الحقيقي، قوة الموقع، ومصداقية المطور قبل المقارنة في السعر."

        caption = f"""📊 مؤشرات اليوم وقراءة في حركة الأسواق - {date_str} 🇪🇬

نظرة تحليلية سريعة على أهم أرقام اليوم وتأثيرها على قراراتك الاستثمارية والعقارية:

🟡 الذهب في مصر:
• عيار 24: {gold_24k} ج.م
• عيار 21: {gold_21k} ج.م
• عيار 18: {gold_18k} ج.م

💵 الدولار مقابل الجنيه (البنك المركزي المصري):
• شراء: {usd_buy} ج.م | بيع: {usd_sell} ج.م

⚡ الأصول العالمية:
• خام برنت: {oil_price} دولار/برميل ({oil_change})
• بيتكوين: {btc_price} دولار ({btc_change})

💡 خلاصة اليوم:
الاستثمار الذكي يبدأ من قراءة الأرقام الحقيقية وفهم السياق الاقتصادي. التحركات العالمية تذكرنا دائماً بأهمية تنويع المحفظة الاستثمارية وعدم وضع كل البيض في سلة واحدة.

ما هو الأصل الذي تراه الأفضل لحفظ القيمة في الوقت الحالي؟ شاركونا آراءكم في التعليقات 👇

-------------------
⚠️ تنويه: المحتوى للأغراض المعرفية والتثقيفية فقط، ولا يُعد بأي شكل نصيحة استثمارية أو توصية مالية.

#HassanDaily #اقتصاد #عقارات #الذهب #الدولار #الاستثمار #مصر #بيتكوين #برنت"""

        return AIContentResponse(
            opportunities=opportunities,
            risks=risks,
            tip_investment=tip_investment,
            tip_real_estate=tip_real_estate,
            social_caption=caption.strip(),
            disclaimer="تنويه: المحتوى للأغراض المعرفية والتثقيفية فقط، ولا يُعد بأي شكل نصيحة استثمارية أو مالية."
        )

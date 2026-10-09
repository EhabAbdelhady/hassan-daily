"""Test script for Phase 1: renders the reference mock infographic."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.render.renderer import InfographicRenderer

mock_data = {
    "date_arabic": "الثلاثاء 29 سبتمبر 2026",
    "gold": {
        "price_24k": "6,971.5",
        "price_21k": "6,100",
        "price_18k": "5,228.5",
        "source": "iSagha",
        "updated_at": "آخر تحديث 29 سبتمبر 2026 (الساعة 01:09 صباحاً)"
    },
    "crypto": {
        "name": "Bitcoin",
        "price": "82,933.6",
        "change_percent": "-0.69%",
        "is_positive": False,
        "source": "Investing.com",
        "updated_at": "آخر تحديث 29 سبتمبر 2026 (الساعة 00:05 صباحاً)"
    },
    "fx": {
        "buy": "52.03",
        "sell": "52.13",
        "source": "البنك المركزي المصري (CBE)",
        "note": "متوسط السوق",
        "updated_at": "آخر تحديث 28 سبتمبر 2026"
    },
    "oil": {
        "name": "Brent",
        "price": "105.91",
        "change_percent": "+0.60%",
        "is_positive": True,
        "source": "Reuters",
        "updated_at": "آخر تحديث 29 سبتمبر 2026 (الساعة 00:02 GMT)"
    },
    "risks": [
        {
            "text": "استمرار التوترات الجيوسياسية في المنطقة وقد يؤدي إلى بقاء أسعار النفط مرتفعة، مما قد يؤثر على تكاليف التشغيل والمواد الخام.",
            "source": "(المصدر: Reuters | سبتمبر 2026)"
        },
        {
            "text": "رغم وجود مؤشرات على تعافي صادرات الخام من المنطقة، إلا أن استمرار المخاطر الجيوسياسية يظل عاملاً مؤثراً على الأسواق العالمية.",
            "source": "(المصدر: Reuters | سبتمبر 2026)"
        },
        {
            "text": "تقلبات سعر الصرف عالمياً قد تؤثر على تكلفة الواردات في السوق المحلي، مما قد ينعكس على بعض القطاعات.",
            "source": "(المصدر: البنك المركزي المصري | سبتمبر 2026)"
        }
    ],
    "opportunities": [
        {
            "text": "استمرار الاهتمام بالاستثمارات العقارية في مصر مع توقع تعزيز الطلب من السوق المحلي والإقليمي على المشروعات السكنية والسياحية.",
            "source": "(المصدر: تقارير اقتصادية | سبتمبر 2026)"
        },
        {
            "text": "مؤشرات إيجابية على تعافي بعض القطاعات المرتبطة بالعقار، بدعم من تحسن النشاط الاستثماري في المنطقة.",
            "source": "(المصدر: تقارير أسواق | سبتمبر 2026)"
        },
        {
            "text": "المدن الجديدة والمناطق ذات البنية التحتية المتطورة تظل من أهم الفرص طويلة المدى للمستثمرين.",
            "source": "(المصدر: وزارة الاستثمار | سبتمبر 2026)"
        }
    ],
    "tip_investment": "تنوع الأصول واحتفظ بسيولة مناسبة، ولا تبنِ قرارك على حركة يوم واحد.",
    "tip_real_estate": "ركّز على الطلب الحقيقي، قوة الموقع، وسجل المطور قبل تقييم السعر."
}

def main():
    renderer = InfographicRenderer()
    print("Rendering HTML and capturing PNG with Playwright...")
    out_path = renderer.render_to_png(mock_data, output_filename="phase1_preview.png")
    print(f"Successfully generated infographic PNG at: {out_path}")
    print(f"File exists: {out_path.exists()} (size: {out_path.stat().st_size} bytes)")

if __name__ == "__main__":
    main()

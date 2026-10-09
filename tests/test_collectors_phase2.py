"""Phase 2 verification test script: live data fetching, history tracking, and live infographic rendering."""

import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collectors.aggregator import MarketDataAggregator
from src.render.renderer import InfographicRenderer

def main():
    print("=" * 60)
    print("PHASE 2: LIVE MARKET DATA FETCHING & HISTORY TRACKING")
    print("=" * 60)

    aggregator = MarketDataAggregator()
    data = aggregator.fetch_all(save_to_history=True)

    print("\n--- Fetched Live Market Data ---")
    print(f"Date: {data['date_arabic']}")
    print(f"Gold (24k / 21k / 18k): {data['gold']['price_24k']} / {data['gold']['price_21k']} / {data['gold']['price_18k']} EGP ({data['gold']['source']})")
    print(f"USD/EGP: Buy {data['fx']['buy']} | Sell {data['fx']['sell']} ({data['fx']['source']})")
    print(f"Bitcoin: ${data['crypto']['price']} ({data['crypto']['change_percent']}) ({data['crypto']['source']})")
    print(f"Brent Crude: ${data['oil']['price']} ({data['oil']['change_percent']}) ({data['oil']['source']})")

    # Verify history.json
    history_file = Path("data/history.json")
    print(f"\nChecking history file: {history_file.exists()}")
    if history_file.exists():
        with open(history_file, "r", encoding="utf-8") as f:
            hist_content = json.load(f)
            print(f"Total historical records: {len(hist_content.get('records', []))}")
            print(f"Latest record: {hist_content.get('records', [])[-1]}")

    # Now render infographic with LIVE fetched prices
    # Include sample analysis commentary for full visual check
    data["risks"] = [
        {
            "text": "استمرار التوترات الجيوسياسية في المنطقة قد يبقي أسعار النفط متذبذبة، مما يضغط على تكاليف النقل ومواد البناء.",
            "source": "(المصدر: Reuters | أكتوبر 2026)"
        },
        {
            "text": "تغيرات وتذبذبات أسواق العملة والذهب عالمياً تدعو المستثمرين للحذر وتجنب المضاربات قصيرة الأجل.",
            "source": "(المصدر: أسواق المال | أكتوبر 2026)"
        },
        {
            "text": "ارتفاع معدلات التضخم المستوردة قد يؤثر على وتيرة التسعير في بعض المشروعات تحت الإنشاء.",
            "source": "(المصدر: تقارير اقتصادية | أكتوبر 2026)"
        }
    ]
    data["opportunities"] = [
        {
            "text": "الطلب الاستثماري على العقار في مصر يحافظ على جاذبيته كمخزن استراتيجي للقيمة وحماية للسيولة.",
            "source": "(المصدر: تقارير عقارية | أكتوبر 2026)"
        },
        {
            "text": "الفرص العقارية في مناطق التوسع العمراني والمدن الجديدة تمنح عوائد إيجارية ورأسمالية واعدة.",
            "source": "(المصدر: تقارير السوق | أكتوبر 2026)"
        },
        {
            "text": "استقرار أسعار الصرف الرسمي يوفر رؤية أوضح للمطورين في تسعير الوحدات وجدولة التدفقات.",
            "source": "(المصدر: وزارة الإسكان | أكتوبر 2026)"
        }
    ]
    data["tip_investment"] = "تنوع الأصول واحتفظ بسيولة كافية، ولا تبنِ قرارك المالي على تذبذب يوم واحد."
    data["tip_real_estate"] = "ركّز على الطلب الحقيقي، قوة الموقع، ومصداقية المطور قبل المقارنة في السعر."

    renderer = InfographicRenderer()
    out_path = renderer.render_to_png(data, output_filename="phase2_live_preview.png")
    print(f"\nRendered live data infographic to: {out_path}")
    print(f"File size: {out_path.stat().st_size} bytes")

if __name__ == "__main__":
    main()

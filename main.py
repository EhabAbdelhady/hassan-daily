"""HASSAN DAILY: fetch prices → write Arabic text → render the infographic.

Usage:
    python main.py                # full run (posting is added in a later phase)
    python main.py --no-history   # don't save today's prices (use for local testing)
"""

import argparse
import sys

from src.ai import generate_daily_content
from src.collectors.aggregator import MarketDataAggregator
from src.config import settings
from src.render.renderer import InfographicRenderer


def run(save_history: bool = True) -> int:
    aggregator = MarketDataAggregator()
    data = aggregator.fetch_all()

    if data["errors"]:
        print("\n[STOP] Some prices could not be fetched, nothing will be published:")
        for err in data["errors"]:
            print(f"  - {err}")
        return 1

    print(f"\n[AI] Writing commentary with {settings.AI_PROVIDER}...")
    content = generate_daily_content(data)

    data.update(
        opportunities=content.opportunities,
        risks=content.risks,
        tip_investment=content.tip_investment,
        tip_real_estate=content.tip_real_estate,
        disclaimer=content.disclaimer,
    )
    png_path = InfographicRenderer().render_to_png(data, output_filename="daily_infographic.png")
    caption_path = settings.OUTPUT_DIR / "caption.txt"
    caption_path.write_text(content.caption, encoding="utf-8")

    if save_history:
        aggregator.save_history(data)
        print("[History] Saved today's prices to data/history.json")

    print(f"\n[Done] Image:   {png_path}\n[Done] Caption: {caption_path}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-history", action="store_true", help="don't save today's prices to history")
    args = parser.parse_args()
    sys.exit(run(save_history=not args.no_history))

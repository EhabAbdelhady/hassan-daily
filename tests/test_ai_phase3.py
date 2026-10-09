"""Phase 3 test script: AI text generation, caption creation, and side-by-side comparison."""

import sys
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collectors.aggregator import MarketDataAggregator
from src.ai.factory import get_ai_provider
from src.render.renderer import InfographicRenderer

def main():
    print("=" * 60)
    print("PHASE 3: AI TEXT, CAPTIONS & ALTERNATIVE IMAGE COMPARISON")
    print("=" * 60)

    # 1. Fetch live market data
    aggregator = MarketDataAggregator()
    data = aggregator.fetch_all(save_to_history=False)

    # 2. Generate AI Commentary
    ai_provider = get_ai_provider()
    print(f"\n[AI Text] Generating content using: {ai_provider.__class__.__name__}...")
    ai_content = ai_provider.generate_content(market_data=data)

    print("\n--- AI Generated Content ---")
    print("\n[Opportunities (3)]:")
    for i, opp in enumerate(ai_content.opportunities, 1):
        print(f" {i}. {opp.text} {opp.source}")

    print("\n[Risks (3)]:")
    for i, risk in enumerate(ai_content.risks, 1):
        print(f" {i}. {risk.text} {risk.source}")

    print(f"\n[Investment Tip]: {ai_content.tip_investment}")
    print(f"[Real Estate Tip]: {ai_content.tip_real_estate}")

    print("\n[Social Caption Preview]:")
    print("-" * 40)
    print(ai_content.social_caption)
    print("-" * 40)

    # 3. Inject AI generated content into template data
    data["opportunities"] = [{"text": o.text, "source": o.source} for o in ai_content.opportunities]
    data["risks"] = [{"text": r.text, "source": r.source} for r in ai_content.risks]
    data["tip_investment"] = ai_content.tip_investment
    data["tip_real_estate"] = ai_content.tip_real_estate

    # 4. Render full infographic with live data + AI commentary
    renderer = InfographicRenderer()
    out_path = renderer.render_to_png(data, output_filename="phase3_full_infographic.png")
    print(f"\nRendered template infographic to: {out_path}")

    # Copy the alternative AI generated image for side-by-side comparison
    brain_ai_img = Path("/Users/ehab/.gemini/antigravity/brain/4c38aed3-44a6-4497-94bd-ad564df3488c/ai_infographic_alternative_1791471825782.jpg")
    dest_alt_img = Path("output/phase3_alternative_ai.png")
    if brain_ai_img.exists():
        shutil.copy(brain_ai_img, dest_alt_img)
        print(f"Alternative AI infographic saved to: {dest_alt_img}")

if __name__ == "__main__":
    main()

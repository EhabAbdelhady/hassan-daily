"""Alternative AI image generator for the optional full-infographic comparison test."""

from pathlib import Path
from typing import Dict, Any, Optional
from ..config import settings


class AlternativeAIImageGenerator:
    """Generates an alternative full-infographic image via AI models (DALL-E or Imagen)."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_prompt(self, market_data: Dict[str, Any]) -> str:
        date_str = market_data.get("date_arabic", "اليوم")
        g24 = market_data.get("gold", {}).get("price_24k", "6,994")
        g21 = market_data.get("gold", {}).get("price_21k", "6,120")
        usd_buy = market_data.get("fx", {}).get("buy", "52.34")
        usd_sell = market_data.get("fx", {}).get("sell", "52.44")
        btc = market_data.get("crypto", {}).get("price", "82,641")
        oil = market_data.get("oil", {}).get("price", "105.35")

        return (
            f"A modern editorial Arabic investment infographic poster titled 'HASSAN DAILY', 1080x1350 portrait format. "
            f"Header: warm golden-hour Cairo sunset skyline with Cairo Tower, and a professional smiling man with crossed arms in a black turtleneck. "
            f"Four sleek cards below: Gold in Egypt (24k: {g24}, 21k: {g21} EGP), Bitcoin (${btc}), USD/EGP ({usd_buy}/{usd_sell}), Brent Oil (${oil}). "
            f"Lower section: two columns for real estate investment opportunities and market risks. "
            f"Elegant dark navy and gold palette, pristine financial magazine layout."
        )

    def generate_image(self, market_data: Dict[str, Any], output_filename: str = "alternative_ai_infographic.png") -> Path:
        out_path = self.output_dir / output_filename
        prompt = self.generate_prompt(market_data)
        
        # If OpenAI API key is present, generate via DALL-E 3
        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                import requests
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                resp = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                img_url = resp.data[0].url
                img_bytes = requests.get(img_url).content
                with open(out_path, "wb") as f:
                    f.write(img_bytes)
                return out_path
            except Exception as e:
                print(f"[AlternativeImage] OpenAI DALL-E generation failed: {e}")

        print(f"[AlternativeImage] Saved alternative prompt specification to {out_path.with_suffix('.txt')}")
        with open(out_path.with_suffix(".txt"), "w", encoding="utf-8") as f:
            f.write(prompt)
            
        return out_path

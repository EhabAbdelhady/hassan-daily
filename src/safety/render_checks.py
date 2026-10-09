"""Verifies the finished image shows exactly the fetched numbers, fully visible and readable."""

import re
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from PIL import Image, ImageOps


def expected_values(data: Dict[str, Any]) -> Dict[str, str]:
    """The exact strings each tagged element in the template must show."""
    g, fx, btc, oil = data["gold"], data["fx"], data["crypto"], data["oil"]
    expected = {
        "gold_24k": g["price_24k"], "gold_21k": g["price_21k"], "gold_18k": g["price_18k"],
        "usd_buy": fx["buy"], "usd_sell": fx["sell"],
        "bitcoin": btc["price"], "brent": oil["price"],
    }
    for key, item in (("gold_change", g), ("usd_change", fx), ("bitcoin_change", btc), ("brent_change", oil)):
        if item.get("change"):
            expected[key] = item["change"]["text"]
    return expected


_ocr_engine = None


def _ocr(png: Image.Image, box: Dict[str, float]) -> str:
    """Reads the text inside one element's box from the final PNG."""
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = RapidOCR()
    # Tight crop + plain white margin reads every number exactly; enlarging or loose crops cause misreads
    pad = 4
    crop = png.crop((max(box["x"] - pad, 0), max(box["y"] - pad, 0),
                     min(box["x"] + box["w"] + pad, png.width), min(box["y"] + box["h"] + pad, png.height)))
    crop = ImageOps.expand(crop, border=30, fill="white")
    result, _ = _ocr_engine(np.array(crop))
    return " ".join(text for _, text, _ in (result or []))


def _digits(text: str) -> str:
    """Keeps only what matters for comparing numbers: digits, separators, minus, percent."""
    return re.sub(r"[^0-9.,%-]", "", text)


def check_render(png_path: Path, report: Dict[str, Any], data: Dict[str, Any]) -> List[str]:
    """Returns a list of problems with the rendered image. Empty means it's correct."""
    problems = []
    items = {i["key"]: i for i in report["items"]}
    png = Image.open(png_path).convert("RGB")

    for key, want in expected_values(data).items():
        item = items.get(key)
        if not item:
            problems.append(f"{key}: not shown on the image")
            continue
        if item["text"] != want:
            problems.append(f"{key}: page shows '{item['text']}', expected '{want}'")
        if item["clipped"]:
            problems.append(f"{key}: '{want}' is hidden or cut off")
            continue
        read = _ocr(png, item)
        if _digits(want.replace("+", "")) not in _digits(read.replace("+", "")):
            problems.append(f"{key}: image reads '{read}', expected '{want}'")

    for box in report["overflowing"]:
        problems.append(f"Text doesn't fit (overflowing box: {box})")
    for src in report["brokenImages"]:
        problems.append(f"Image failed to load: {src}")
    for font in report["missingFonts"]:
        problems.append(f"Font not loaded: {font}")
    return problems

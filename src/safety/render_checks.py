"""Verifies the finished image shows exactly the fetched numbers, fully visible and readable."""

import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

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


# Crop settings (padding, white margin, scale). The first reads almost everything; very large digits
# (e.g. the story's 72px prices) are sometimes split or doubled by OCR, which the downscaled crops fix.
OCR_VARIANTS = ((4, 30, 1.0), (4, 30, 0.5), (8, 40, 0.75))


def _ocr(png: Image.Image, box: Dict[str, float], pad: int = 4, border: int = 30, scale: float = 1.0) -> str:
    """Reads the text inside one element's box from the final PNG."""
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = RapidOCR()
    crop = png.crop((max(box["x"] - pad, 0), max(box["y"] - pad, 0),
                     min(box["x"] + box["w"] + pad, png.width), min(box["y"] + box["h"] + pad, png.height)))
    if scale != 1.0:
        crop = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.Resampling.LANCZOS)
    crop = ImageOps.expand(crop, border=border, fill="white")
    result, _ = _ocr_engine(np.array(crop))
    return " ".join(text for _, text, _ in (result or []))


def _ocr_matches(png: Image.Image, box: Dict[str, float], want: str) -> Tuple[bool, List[str]]:
    """True if any crop setting reads exactly the expected number. A wrong number on the image
    would have to be misread as exactly the right one to pass, which OCR doesn't do."""
    reads = []
    for pad, border, scale in OCR_VARIANTS:
        read = _ocr(png, box, pad, border, scale)
        reads.append(read)
        if _digits(want.replace("+", "")) in _digits(read.replace("+", "")):
            return True, reads
    return False, reads


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
        ok, reads = _ocr_matches(png, item, want)
        if not ok:
            problems.append(f"{key}: image reads {' / '.join(repr(r) for r in reads)}, expected '{want}'")

    for box in report["overflowing"]:
        problems.append(f"Text doesn't fit (overflowing box: {box})")
    for src in report["brokenImages"]:
        problems.append(f"Image failed to load: {src}")
    for font in report["missingFonts"]:
        problems.append(f"Font not loaded: {font}")
    return problems


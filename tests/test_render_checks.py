from PIL import Image, ImageDraw, ImageFont

import src.safety.render_checks as rc


def test_ocr_falls_back_to_other_crop_settings(monkeypatch):
    reads = iter(["81,5 522", "81,522"])  # first setting splits the digits, second reads them right
    monkeypatch.setattr(rc, "_ocr", lambda png, box, pad, border, scale: next(reads))
    ok, got = rc._ocr_matches(Image.new("RGB", (10, 10)), {"x": 0, "y": 0, "w": 5, "h": 5}, "81,522")
    assert ok and got == ["81,5 522", "81,522"]


def test_wrong_number_never_passes(monkeypatch):
    monkeypatch.setattr(rc, "_ocr", lambda png, box, pad, border, scale: "81,622")
    ok, got = rc._ocr_matches(Image.new("RGB", (10, 10)), {"x": 0, "y": 0, "w": 5, "h": 5}, "81,522")
    assert not ok and len(got) == len(rc.OCR_VARIANTS)

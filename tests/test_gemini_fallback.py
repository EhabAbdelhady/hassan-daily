import pytest
from google.genai import errors

import src.ai.providers.gemini_provider as gp
from src.ai.base import AIContentResponse

GOOD = AIContentResponse(opportunities=[], risks=[], tip_investment="t", tip_real_estate="t", caption_summary="s")


class FakeModels:
    def __init__(self, behaviour):
        self.behaviour, self.calls = behaviour, []

    def generate_content(self, model, contents, config):
        self.calls.append(model)
        code = self.behaviour(model, len(self.calls))
        if code:
            raise errors.APIError(code, {"error": {"code": code, "message": "busy", "status": "UNAVAILABLE"}})
        return type("R", (), {"text": GOOD.model_dump_json()})()


def provider(behaviour, monkeypatch):
    monkeypatch.setattr(gp.time, "sleep", lambda s: None)
    p = gp.GeminiProvider.__new__(gp.GeminiProvider)
    p.model = gp.DEFAULT_MODEL
    p.client = type("C", (), {"models": FakeModels(behaviour)})()
    return p


def test_falls_back_to_lite_when_flash_models_are_busy(monkeypatch):
    # As on 2026-11-05: every "flash" model busy, the lite models fine
    p = provider(lambda m, n: 503 if "lite" not in m else 0, monkeypatch)
    assert p.generate_content("s", "u") == GOOD
    assert p.client.models.calls[-1] == "gemini-3.5-flash-lite"


def test_waits_and_retries_when_everything_is_busy(monkeypatch):
    p = provider(lambda m, n: 503 if n <= 6 else 0, monkeypatch)  # busy for the whole first pass
    assert p.generate_content("s", "u") == GOOD
    assert len(p.client.models.calls) == 7


def test_gives_up_after_all_passes(monkeypatch):
    p = provider(lambda m, n: 503, monkeypatch)
    with pytest.raises(errors.APIError):
        p.generate_content("s", "u")


def test_quota_error_skips_that_model_for_the_rest_of_the_run(monkeypatch):
    p = provider(lambda m, n: 429 if m == gp.DEFAULT_MODEL else 503, monkeypatch)
    with pytest.raises(errors.APIError):
        p.generate_content("s", "u")
    assert p.client.models.calls.count(gp.DEFAULT_MODEL) == 1

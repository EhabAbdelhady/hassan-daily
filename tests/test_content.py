import pytest

from src.ai.base import AIContentResponse, BaseAIProvider, ContentItem
from src.ai.content import DISCLAIMER, ContentCheckError, build_caption, check_text, generate_daily_content


def test_real_numbers_pass(market_data):
    texts = ["عيار 21 عند 6,120 ج.م", "الدولار 52.34 شراء", "برنت 103.84 دولار بتراجع 1.43%", "بيتكوين قرب 81,688", "عيار 24 عند ٦٩٩٤"]
    assert check_text(texts, market_data) == []


def test_invented_number_fails(market_data):
    problems = check_text(["التضخم بلغ 12.5% هذا الشهر"], market_data)
    assert any("12.5" in p for p in problems)


def test_promise_fails(market_data):
    problems = check_text(["العقار يحقق عائد مضمون"], market_data)
    assert any("مضمون" in p for p in problems)


def test_caption_has_exact_prices_and_disclaimer(market_data):
    caption = build_caption("ملخص اليوم.", market_data)
    for value in ["6,994.25", "6,120", "5,245.75", "52.34", "52.44", "81,688", "103.84"]:
        assert value in caption
    assert DISCLAIMER in caption


class StubProvider(BaseAIProvider):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def generate_content(self, system_prompt, user_prompt):
        self.calls += 1
        return self.responses.pop(0)


def _response(first_text):
    item = lambda t, k: ContentItem(text=t, based_on=[k])
    return AIContentResponse(
        opportunities=[item(first_text, "gold"), item("نص", "usd"), item("نص", "brent")],
        risks=[item("نص", "bitcoin"), item("نص", "brent"), item("نص", "usd")],
        tip_investment="نصيحة", tip_real_estate="نصيحة", caption_summary="ملخص",
    )


def test_retries_once_then_succeeds(market_data):
    provider = StubProvider([_response("سعر الفائدة 27%"), _response("عيار 21 عند 6,120")])
    content = generate_daily_content(market_data, provider=provider)
    assert provider.calls == 2
    assert content.opportunities[0]["source"].startswith("(المصدر: iSagha")


def test_two_failures_stop(market_data):
    provider = StubProvider([_response("سعر الفائدة 27%"), _response("سعر الفائدة 27%")])
    with pytest.raises(ContentCheckError):
        generate_daily_content(market_data, provider=provider)

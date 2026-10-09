"""The daily run: fetch → check → write → render → verify → email. Stops and alerts on any problem."""

import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional

from .ai import generate_daily_content, ContentCheckError
from .collectors.aggregator import MarketDataAggregator
from .config import settings
from .notify import send_preview, send_alert
from .render.renderer import InfographicRenderer
from .safety import check_market_data, check_render


class RunStopped(Exception):
    """A safety check failed. Carries what to put in the alert email."""

    def __init__(self, reason: str, problems: List[str], data: Optional[Dict[str, Any]] = None,
                 png: Optional[Path] = None):
        super().__init__(reason)
        self.reason, self.problems, self.data, self.png = reason, problems, data, png


def _steps(save_history: bool, email: bool) -> Dict[str, Any]:
    aggregator = MarketDataAggregator()
    data = aggregator.fetch_all()

    problems = check_market_data(data)
    if problems:
        reason = "a price is missing" if data["errors"] else "a price failed the safety checks"
        raise RunStopped(reason, problems, data)

    print(f"\n[AI] Writing commentary with {settings.AI_PROVIDER}...")
    try:
        content = generate_daily_content(data)
    except ContentCheckError as e:
        raise RunStopped("the AI text failed the fact checks twice", str(e).splitlines(), data)

    data.update(
        opportunities=content.opportunities,
        risks=content.risks,
        tip_investment=content.tip_investment,
        tip_real_estate=content.tip_real_estate,
        disclaimer=content.disclaimer,
    )
    png, report = InfographicRenderer().render(data, output_filename="daily_infographic.png")
    caption_path = settings.OUTPUT_DIR / "caption.txt"
    caption_path.write_text(content.caption, encoding="utf-8")

    problems = check_render(png, report, data)
    if problems:
        raise RunStopped("the image doesn't show the fetched numbers correctly", problems, data, png)
    print("[Checks] Image verified: every number matches the fetched data")

    if save_history:
        aggregator.save_history(data)
        print("[History] Saved today's prices to data/history.json")

    if email:
        send_preview(png, content.caption, data, status="Preview only (posting is not set up yet).")
        print(f"[Email] Preview sent to {settings.ALERT_RECIPIENT_EMAIL}")

    print(f"\n[Done] Image:   {png}\n[Done] Caption: {caption_path}")
    return {"data": data, "png": png, "caption": content.caption}


def _alert(*args) -> None:
    """Sends an alert email; if email itself is broken, says so loudly instead of crashing."""
    try:
        send_alert(*args)
        print(f"[Email] Alert sent to {settings.ALERT_RECIPIENT_EMAIL}")
    except Exception as e:
        print(f"[Email] COULD NOT SEND THE ALERT EMAIL: {type(e).__name__}: {e}")


def run(save_history: bool = True, email: bool = True) -> int:
    """Runs the pipeline. Returns 0 on success, 1 if it stopped (and emailed an alert)."""
    try:
        _steps(save_history, email)
        return 0
    except RunStopped as stop:
        print(f"\n[STOP] Nothing will be published: {stop.reason}")
        for p in stop.problems:
            print(f"  - {p}")
        if email:
            _alert(stop.reason, stop.problems, stop.data, stop.png)
        return 1
    except Exception as e:
        print(f"\n[STOP] Unexpected error: {type(e).__name__}: {e}")
        traceback.print_exc()
        if email:
            _alert("unexpected error", [f"{type(e).__name__}: {e}", traceback.format_exc()[-1500:]])
        return 1

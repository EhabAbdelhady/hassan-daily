"""The daily run in two steps, so a human can approve in between.

prepare: fetch → market checks → AI → render → image checks → token check → save history → preview email
publish: approval-cutoff check → token check → upload image → post (once per platform per day) → result email

Any problem raises RunStopped → alert email; nothing is posted.
"""

import hashlib
import json
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests

from .ai import generate_daily_content, ContentCheckError
from .collectors.aggregator import MarketDataAggregator
from .config import settings
from .notify import send_preview, send_alert, send_published
from .publish import posts_log
from .publish.hosting import upload_image
from .publish.meta import MetaError, check_token, post_facebook, post_instagram, post_link
from .render.renderer import InfographicRenderer
from .safety import check_market_data, check_render
from .utils.arabic_date import CAIRO_TZ, get_cairo_now


class RunStopped(Exception):
    """A safety check failed. Carries what to put in the alert email."""

    def __init__(self, reason: str, problems: List[str], data: Optional[Dict[str, Any]] = None,
                 png: Optional[Path] = None):
        super().__init__(reason)
        self.reason, self.problems, self.data, self.png = reason, problems, data, png


def _platforms() -> List[str]:
    return [p for p, on in (("facebook", settings.POST_TO_FACEBOOK), ("instagram", settings.POST_TO_INSTAGRAM)) if on]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(save_history: bool, email: bool) -> None:
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

    warnings = []
    if _platforms():
        token = check_token()
        if token["errors"] and not settings.DRY_RUN:
            raise RunStopped("the Meta token needs attention, so posting can't work", token["errors"], data, png)
        warnings = token["errors"] + token["warnings"]
        print(f"[Meta] Token check: {'OK' if not warnings else '; '.join(warnings)}")

    if save_history:
        aggregator.save_history(data)
        print("[History] Saved today's prices to data/history.json")

    prepared_at = datetime.now(timezone.utc)
    settings.BUNDLE_FILE.write_text(json.dumps({
        "date": data["date"],
        "prepared_at": prepared_at.isoformat(),
        "png": png.name,  # relative: publish may run on another machine (GitHub job)
        "png_sha256": _sha256(png),
        "caption": content.caption,
        "data": data,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    targets = " and ".join(p.capitalize() for p in _platforms()) or "no platform (both are switched off)"
    if settings.DRY_RUN:
        status = f"DRY RUN: nothing will be posted. With DRY_RUN=false this would go to {targets}."
    elif settings.REQUIRE_APPROVAL:
        deadline = (prepared_at + timedelta(hours=settings.CUTOFF_HOURS)).astimezone(CAIRO_TZ)
        status = (f"Waiting for your approval to post to {targets}. "
                  f"Approve by {deadline:%H:%M} Cairo time ({settings.CUTOFF_HOURS:g} hours), otherwise it won't be posted.")
    else:
        status = f"Approval is off: posting to {targets} now. You'll get a second email with the links."

    if email:
        send_preview(png, content.caption, data, status=status, warnings=warnings)
        print(f"[Email] Preview sent to {settings.ALERT_RECIPIENT_EMAIL}")
    print(f"\n[Prepared] {status}\n[Prepared] Image: {png}\n[Prepared] Caption: {caption_path}")


def publish(email: bool) -> None:
    if not settings.BUNDLE_FILE.exists():
        raise RunStopped("there is no prepared post to publish", ["Run the prepare step first."])
    bundle = json.loads(settings.BUNDLE_FILE.read_text(encoding="utf-8"))
    data, caption, date = bundle["data"], bundle["caption"], bundle["date"]
    png = settings.OUTPUT_DIR / bundle["png"]

    today = get_cairo_now().strftime("%Y-%m-%d")
    if date != today:
        raise RunStopped("the prepared post is from another day", [f"Prepared for {date}, today is {today}."], data)

    prepared_at = datetime.fromisoformat(bundle["prepared_at"])
    waited = datetime.now(timezone.utc) - prepared_at
    if waited > timedelta(hours=settings.CUTOFF_HOURS):
        raise RunStopped(
            "approval came after the cutoff, so today's post was skipped",
            [f"Prepared at {prepared_at.astimezone(CAIRO_TZ):%H:%M} Cairo time, approved "
             f"{waited.total_seconds() / 3600:.1f} hours later (limit {settings.CUTOFF_HOURS:g} hours). "
             "Prices may have moved, so nothing was posted."],
            data, png)

    if not png.exists() or _sha256(png) != bundle["png_sha256"]:
        raise RunStopped("the prepared image is missing or was changed after it was checked", [str(png)], data)

    pending = [p for p in _platforms() if not posts_log.get(date, p)]
    already = [p for p in _platforms() if p not in pending]
    for p in already:
        entry = posts_log.get(date, p)
        print(f"[Publish] {p}: already {entry['status']} today ({entry['id'] or entry['detail']}), skipping")

    if settings.DRY_RUN:
        msg = f"DRY RUN: approval received; would have posted to {', '.join(pending) or 'nothing (already posted)'}."
        print(f"[Publish] {msg}")
        if email:
            send_published(date, [msg], [], data)
        return
    if not pending:
        print("[Publish] Nothing to do: every platform was already posted today.")
        return

    token = check_token()
    if token["errors"]:
        raise RunStopped("the Meta token needs attention, so nothing was posted", token["errors"], data, png)

    image_url = upload_image(png, public_id=date)
    print("[Publish] Image uploaded to Cloudinary")

    done, failed = [], []
    for platform in pending:
        poster = post_facebook if platform == "facebook" else post_instagram
        try:
            post_id = poster(image_url, caption)
        except MetaError as e:  # Meta answered with an error: the post was not created
            failed.append(f"{platform}: {e}")
            continue
        except requests.RequestException as e:  # no answer: it may or may not have posted
            posts_log.record(date, platform, "uncertain", detail=str(e))
            failed.append(f"{platform}: no response from Meta ({type(e).__name__}). It may have posted. "
                          "Check the page; it won't be retried today to avoid a duplicate.")
            continue
        posts_log.record(date, platform, "posted", post_id=post_id)
        done.append(f"{platform.capitalize()}: {post_link(platform, post_id)}")
        print(f"[Publish] Posted to {platform}: {post_id}")

    if failed:
        raise RunStopped("posting failed" + (" on some platforms" if done else ""),
                         failed + [f"Posted OK: {d}" for d in done], data, png)
    if email:
        send_published(date, done, token["warnings"], data)
        print(f"[Email] Confirmation sent to {settings.ALERT_RECIPIENT_EMAIL}")


def _alert(*args) -> None:
    """Sends an alert email; if email itself is broken, says so loudly instead of crashing."""
    try:
        send_alert(*args)
        print(f"[Email] Alert sent to {settings.ALERT_RECIPIENT_EMAIL}")
    except Exception as e:
        print(f"[Email] COULD NOT SEND THE ALERT EMAIL: {type(e).__name__}: {e}")


def _guarded(step, email: bool) -> int:
    try:
        step()
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


def run(step: str = "all", save_history: bool = True, email: bool = True) -> int:
    """step: 'prepare', 'publish', or 'all' (prepare, then publish right away if approval is off)."""
    if step == "publish":
        return _guarded(lambda: publish(email), email)
    code = _guarded(lambda: prepare(save_history, email), email)
    if code == 0 and step == "all" and not settings.REQUIRE_APPROVAL:
        code = _guarded(lambda: publish(email), email)
    return code

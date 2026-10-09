import json
from datetime import datetime, timedelta, timezone

import pytest
import requests

import src.pipeline as pl
from src.config import settings


@pytest.fixture
def env(tmp_path, monkeypatch, market_data):
    """A prepared bundle in a temp folder, with Meta, Cloudinary and email faked out."""
    monkeypatch.setattr(settings, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(settings, "BUNDLE_FILE", tmp_path / "bundle.json")
    monkeypatch.setattr(settings, "POSTS_LOG_FILE", tmp_path / "posts.json")
    monkeypatch.setattr(settings, "DRY_RUN", False)
    monkeypatch.setattr(settings, "POST_TO_FACEBOOK", True)
    monkeypatch.setattr(settings, "POST_TO_INSTAGRAM", False)
    monkeypatch.setattr(settings, "CUTOFF_HOURS", 2.0)
    monkeypatch.setattr(settings, "POST_TO_FACEBOOK_STORY", False)
    monkeypatch.setattr(settings, "POST_TO_INSTAGRAM_STORY", False)
    png = tmp_path / "daily_infographic.png"
    png.write_bytes(b"png-bytes")
    story = tmp_path / "daily_story.png"
    story.write_bytes(b"story-bytes")

    def write_bundle(hours_ago=0.5, with_story=True):
        settings.BUNDLE_FILE.write_text(json.dumps({
            "date": pl.get_cairo_now().strftime("%Y-%m-%d"),
            "prepared_at": (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat(),
            "png": png.name, "png_sha256": pl._sha256(png), "caption": "caption", "data": market_data,
            "story": story.name if with_story else None,
            "story_sha256": pl._sha256(story) if with_story else None,
        }))

    calls = {"facebook": 0, "facebook_story": [], "instagram": [], "alerts": [], "published": []}

    def fake_fb(url, caption):
        calls["facebook"] += 1
        return "123_456"

    monkeypatch.setattr(pl, "check_token", lambda: {"errors": [], "warnings": []})
    monkeypatch.setattr(pl, "upload_image", lambda png, public_id: f"https://example.com/{public_id}.png")
    monkeypatch.setattr(pl, "post_facebook", fake_fb)
    monkeypatch.setattr(pl, "post_facebook_story", lambda url: calls["facebook_story"].append(url) or "story_1")
    monkeypatch.setattr(pl, "post_instagram",
                        lambda url, caption="", story=False: calls["instagram"].append((url, story)) or "ig_1")
    monkeypatch.setattr(pl, "send_alert", lambda reason, *a: calls["alerts"].append(reason))
    monkeypatch.setattr(pl, "send_published", lambda date, results, *a: calls["published"].append(results))
    write_bundle()
    return {"calls": calls, "write_bundle": write_bundle, "monkeypatch": monkeypatch}


def test_posts_once_and_never_twice(env):
    assert pl.run("publish") == 0
    assert pl.run("publish") == 0  # second run: already posted today
    assert env["calls"]["facebook"] == 1
    assert len(env["calls"]["published"]) == 1


def test_late_approval_posts_nothing(env):
    env["write_bundle"](hours_ago=2.5)
    assert pl.run("publish") == 1
    assert env["calls"]["facebook"] == 0
    assert "after the cutoff" in env["calls"]["alerts"][0]


def test_no_response_is_never_retried(env):
    def timeout(url, caption):
        env["calls"]["facebook"] += 1
        raise requests.Timeout("read timed out")
    env["monkeypatch"].setattr(pl, "post_facebook", timeout)
    assert pl.run("publish") == 1
    assert pl.run("publish") == 0  # logged as 'uncertain' → skipped, no duplicate risk
    assert env["calls"]["facebook"] == 1


def test_dry_run_never_posts(env):
    env["monkeypatch"].setattr(settings, "DRY_RUN", True)
    assert pl.run("publish") == 0
    assert env["calls"]["facebook"] == 0
    assert "DRY RUN" in env["calls"]["published"][0][0]


def test_changed_image_is_refused(env):
    (settings.OUTPUT_DIR / "daily_infographic.png").write_bytes(b"tampered")
    assert pl.run("publish") == 1
    assert env["calls"]["facebook"] == 0


def test_feed_and_stories_each_post_once(env):
    mp = env["monkeypatch"]
    for flag in ("POST_TO_FACEBOOK_STORY", "POST_TO_INSTAGRAM", "POST_TO_INSTAGRAM_STORY"):
        mp.setattr(settings, flag, True)
    assert pl.run("publish") == 0
    assert pl.run("publish") == 0
    calls = env["calls"]
    assert calls["facebook"] == 1
    assert len(calls["facebook_story"]) == 1 and calls["facebook_story"][0].endswith("-story.jpg")
    # Instagram gets JPEG links: the feed image for the post, the story image for the story
    assert {(u.rsplit("/", 1)[1], s) for u, s in calls["instagram"]} == {
        (f"{pl.get_cairo_now():%Y-%m-%d}.jpg", False), (f"{pl.get_cairo_now():%Y-%m-%d}-story.jpg", True)}


def test_story_without_prepared_story_image_stops(env):
    env["monkeypatch"].setattr(settings, "POST_TO_FACEBOOK_STORY", True)
    env["write_bundle"](with_story=False)
    assert pl.run("publish") == 1
    assert env["calls"]["facebook"] == 0 and env["calls"]["facebook_story"] == []

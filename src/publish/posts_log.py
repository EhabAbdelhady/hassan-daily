"""Remembers what was posted each day so a repeated run never posts twice."""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..config import settings


def _load() -> Dict[str, Any]:
    f = settings.POSTS_LOG_FILE
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def get(date: str, platform: str) -> Optional[Dict[str, Any]]:
    return _load().get(date, {}).get(platform)


def record(date: str, platform: str, status: str, post_id: str = "", detail: str = "") -> None:
    """status: 'posted', or 'uncertain' when the request failed in a way that may still have posted."""
    log = _load()
    log.setdefault(date, {})[platform] = {
        "status": status, "id": post_id, "detail": detail,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    # Keep the last 400 days
    for old in sorted(log)[:-400]:
        del log[old]
    settings.POSTS_LOG_FILE.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")

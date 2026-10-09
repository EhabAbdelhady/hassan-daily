"""Meta Graph API: token health check, Facebook Page photo post, Instagram Business post.

Posting requests are never retried automatically: a timeout may mean the post went through,
and a blind retry would publish a duplicate.
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, List

import requests

from ..config import settings

TOKEN_WARN_DAYS = 14
REQUIRED_SCOPES = {"pages_manage_posts", "pages_read_engagement", "pages_show_list"}
INSTAGRAM_SCOPES = {"instagram_basic", "instagram_content_publish"}


class MetaError(Exception):
    pass


def _url(path: str) -> str:
    return f"https://graph.facebook.com/{settings.META_GRAPH_VERSION}/{path}"


def _call(method: str, path: str, **params) -> Dict[str, Any]:
    r = requests.request(method, _url(path), data=params if method == "POST" else None,
                         params=params if method == "GET" else None, timeout=60)
    body = r.json() if r.headers.get("content-type", "").startswith(("application/json", "text/javascript")) else {}
    if r.status_code != 200 or "error" in body:
        err = body.get("error", {})
        raise MetaError(f"{method} {path}: {err.get('message', r.text[:200])} (code {err.get('code')})")
    return body


def check_token() -> Dict[str, List[str]]:
    """Checks the Page token. Returns {"errors": [...], "warnings": [...]}; errors mean posting can't work."""
    errors, warnings = [], []
    token = settings.META_PAGE_ACCESS_TOKEN
    missing = [n for n in ("META_PAGE_ACCESS_TOKEN", "FACEBOOK_PAGE_ID", "META_APP_ID", "META_APP_SECRET")
               if not getattr(settings, n)]
    if missing:
        return {"errors": [f"Not set: {', '.join(missing)}"], "warnings": []}

    try:
        info = _call("GET", "debug_token", input_token=token,
                     access_token=f"{settings.META_APP_ID}|{settings.META_APP_SECRET}")["data"]
    except (MetaError, requests.RequestException) as e:
        return {"errors": [f"Could not check the Meta token: {e}"], "warnings": []}

    if not info.get("is_valid"):
        msg = info.get("error", {}).get("message", "token is invalid or expired")
        return {"errors": [f"Meta token is not valid: {msg}. A new token is needed (README: 'Renewing the Meta token')."],
                "warnings": []}

    if str(info.get("profile_id", settings.FACEBOOK_PAGE_ID)) != str(settings.FACEBOOK_PAGE_ID):
        errors.append(f"The token belongs to Page {info.get('profile_id')}, but FACEBOOK_PAGE_ID is {settings.FACEBOOK_PAGE_ID}")

    scopes = set(info.get("scopes", []))
    needed = REQUIRED_SCOPES | (INSTAGRAM_SCOPES if settings.POST_TO_INSTAGRAM else set())
    if needed - scopes:
        errors.append(f"Token is missing permissions: {', '.join(sorted(needed - scopes))}")

    now = datetime.now(timezone.utc).timestamp()
    for field, label in (("expires_at", "The token expires"), ("data_access_expires_at", "Data access expires")):
        ts = info.get(field) or 0  # 0 means never
        if ts:
            days = (ts - now) / 86400
            when = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
            if days <= 0:
                errors.append(f"{label} on {when} (already passed). Renew the token.")
            elif days <= TOKEN_WARN_DAYS:
                warnings.append(f"{label} on {when} ({days:.0f} days). Renew the token soon (README: 'Renewing the Meta token').")
    return {"errors": errors, "warnings": warnings}


def post_facebook(image_url: str, caption: str) -> str:
    """Publishes a photo post on the Page. Returns the post id."""
    body = _call("POST", f"{settings.FACEBOOK_PAGE_ID}/photos",
                 url=image_url, caption=caption, published="true",
                 access_token=settings.META_PAGE_ACCESS_TOKEN)
    return body.get("post_id") or body["id"]


def post_instagram(image_url: str, caption: str) -> str:
    """Publishes to the linked Instagram Professional account (create container → wait → publish)."""
    ig, token = settings.INSTAGRAM_ACCOUNT_ID, settings.META_PAGE_ACCESS_TOKEN
    if not ig:
        raise MetaError("INSTAGRAM_ACCOUNT_ID is not set")
    creation_id = _call("POST", f"{ig}/media", image_url=image_url, caption=caption, access_token=token)["id"]

    for _ in range(30):  # up to ~2.5 minutes for Instagram to fetch and process the image
        status = _call("GET", creation_id, fields="status_code", access_token=token).get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise MetaError(f"Instagram could not process the image (status {status})")
        time.sleep(5)
    else:
        raise MetaError("Instagram took too long to process the image")

    return _call("POST", f"{ig}/media_publish", creation_id=creation_id, access_token=token)["id"]


def post_link(platform: str, post_id: str) -> str:
    if platform == "facebook":
        return f"https://www.facebook.com/{post_id}"
    return "https://www.instagram.com/"  # the media id isn't the public shortcode; the profile shows the post

"""Turns a short-lived Meta user token into a long-lived Page token and saves it in .env.

1. Put META_APP_ID, META_APP_SECRET and META_USER_TOKEN (from Graph API Explorer) in .env
2. Run:  .venv/bin/python scripts/meta_page_token.py              (lists your Pages)
         .venv/bin/python scripts/meta_page_token.py "Page name"  (saves that Page's token)

It writes FACEBOOK_PAGE_ID, META_PAGE_ACCESS_TOKEN and (if linked) INSTAGRAM_ACCOUNT_ID,
then deletes META_USER_TOKEN from .env. Tokens are never printed.
"""

import re
import sys
from pathlib import Path

import requests
from dotenv import dotenv_values

ENV = Path(__file__).resolve().parent.parent / ".env"


def set_env(key: str, value: str) -> None:
    text = ENV.read_text(encoding="utf-8")
    line = f"{key}={value}"
    if re.search(rf"^{key}=.*$", text, flags=re.M):
        text = re.sub(rf"^{key}=.*$", lambda _: line, text, flags=re.M)
    else:
        text = text.rstrip("\n") + f"\n{line}\n"
    ENV.write_text(text, encoding="utf-8")


def main() -> int:
    env = dotenv_values(ENV)
    version = env.get("META_GRAPH_VERSION") or "v26.0"
    app_id, secret, user_token = env.get("META_APP_ID"), env.get("META_APP_SECRET"), env.get("META_USER_TOKEN")
    if not (app_id and secret and user_token):
        print("Missing in .env: " + ", ".join(k for k, v in
              (("META_APP_ID", app_id), ("META_APP_SECRET", secret), ("META_USER_TOKEN", user_token)) if not v))
        return 1
    graph = f"https://graph.facebook.com/{version}"

    r = requests.get(f"{graph}/oauth/access_token", params={
        "grant_type": "fb_exchange_token", "client_id": app_id, "client_secret": secret,
        "fb_exchange_token": user_token}, timeout=30).json()
    if "access_token" not in r:
        print("Could not exchange the user token:", r.get("error", {}).get("message", r))
        return 1
    long_user = r["access_token"]

    pages = requests.get(f"{graph}/me/accounts", params={
        "access_token": long_user, "fields": "id,name,access_token,instagram_business_account"},
        timeout=30).json()
    if "data" not in pages:
        print("Could not list Pages:", pages.get("error", {}).get("message", pages))
        return 1
    if not pages["data"]:
        print("No Pages found. When generating the token, make sure you selected the Page and its permissions.")
        return 1

    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    if not wanted:
        if len(pages["data"]) > 1:
            print("Your Pages (run again with the name in quotes):")
            for p in pages["data"]:
                print(f"  - {p['name']}")
            return 0
        wanted = pages["data"][0]["name"]
    match = [p for p in pages["data"] if p["name"] == wanted]
    if not match:
        print(f"No Page named '{wanted}'. Available: " + ", ".join(p["name"] for p in pages["data"]))
        return 1
    page = match[0]

    set_env("FACEBOOK_PAGE_ID", page["id"])
    set_env("META_PAGE_ACCESS_TOKEN", page["access_token"])
    ig = (page.get("instagram_business_account") or {}).get("id", "")
    set_env("INSTAGRAM_ACCOUNT_ID", ig)
    set_env("META_USER_TOKEN", "")
    print(f"Saved the Page token for '{page['name']}' (Page ID {page['id']}) in .env.")
    print(f"Instagram account: {'linked, ID ' + ig if ig else 'not linked (fine for Facebook-only)'}")
    print("META_USER_TOKEN was cleared from .env.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

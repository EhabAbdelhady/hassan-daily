"""One-time GitHub setup: push the code, copy keys from .env into GitHub Secrets, set Variables,
create the "production" approval environment, and optionally start a test run.

Needs in .env:
  GITHUB_REPO=your-username/hassan-daily
  GITHUB_TOKEN=<fine-grained token for that repo; see README "Connecting GitHub">

Run:  .venv/bin/python scripts/github_setup.py            (push + secrets + variables + environment)
      .venv/bin/python scripts/github_setup.py --test-run (also starts a dry-run of the workflow)
Secret values are never printed. Requires: pip install pynacl
"""

import base64
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import dotenv_values
from nacl import encoding, public

ROOT = Path(__file__).resolve().parent.parent
SECRETS = [
    "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "COINGECKO_API_KEY",
    "GMAIL_USER", "GMAIL_APP_PASSWORD", "ALERT_RECIPIENT_EMAIL", "RESEND_API_KEY", "RESEND_FROM_EMAIL",
    "CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET",
    "META_PAGE_ACCESS_TOKEN", "FACEBOOK_PAGE_ID", "INSTAGRAM_ACCOUNT_ID", "META_APP_ID", "META_APP_SECRET",
]
# Starting values; change them later in GitHub (Settings → Secrets and variables → Actions → Variables)
VARIABLES = {
    "DRY_RUN": "true",
    "REQUIRE_APPROVAL": "true",
    "CUTOFF_HOURS": "2",
    "POST_TO_FACEBOOK": "true",
    "POST_TO_INSTAGRAM": "false",
    "POST_TO_FACEBOOK_STORY": "false",
    "POST_TO_INSTAGRAM_STORY": "false",
    "EMAIL_SERVICE": "gmail",
}
VARIABLES_FROM_ENV = ["AI_PROVIDER", "AI_MODEL"]


def main() -> int:
    env = dotenv_values(ROOT / ".env")
    repo, token = env.get("GITHUB_REPO", "").strip(), env.get("GITHUB_TOKEN", "").strip()
    if not repo or not token:
        print("Set GITHUB_REPO (owner/name) and GITHUB_TOKEN in .env first.")
        return 1
    api = requests.Session()
    api.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"})
    base = f"https://api.github.com/repos/{repo}"

    def check(r, what):
        if r.status_code >= 300:
            raise SystemExit(f"{what} failed ({r.status_code}): {r.json().get('message', r.text[:200])}")
        return r

    info = check(api.get(base), "Reading the repository").json()
    print(f"Repository: {info['full_name']} ({'public' if not info['private'] else 'PRIVATE'})")
    if info["private"]:
        print("Warning: approval reviewers need a public repository on GitHub's free plan.")
    me = check(api.get("https://api.github.com/user"), "Reading your account").json()

    # 1. Push the code (token passed as a header for this one command; never stored in git config)
    auth = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    push = subprocess.run(
        ["git", "-c", f"http.extraHeader=Authorization: Basic {auth}", "push", "-u",
         f"https://github.com/{repo}.git", "main"],
        cwd=ROOT, capture_output=True, text=True)
    if push.returncode:
        print("git push failed:\n" + push.stderr.replace(token, "***"))
        return 1
    subprocess.run(["git", "remote", "remove", "origin"], cwd=ROOT, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", f"https://github.com/{repo}.git"], cwd=ROOT)
    print("Code pushed to main")

    # 2. Secrets (encrypted with the repository's public key, as GitHub requires)
    key = check(api.get(f"{base}/actions/secrets/public-key"), "Reading the secrets key").json()
    box = public.SealedBox(public.PublicKey(key["key"].encode(), encoding.Base64Encoder()))
    for name in SECRETS:
        value = (env.get(name) or "").strip()
        if not value:
            continue
        encrypted = base64.b64encode(box.encrypt(value.encode())).decode()
        check(api.put(f"{base}/actions/secrets/{name}", json={"encrypted_value": encrypted, "key_id": key["key_id"]}),
              f"Saving secret {name}")
        print(f"Secret saved: {name}")

    # 3. Variables
    values = dict(VARIABLES)
    values.update({k: env[k] for k in VARIABLES_FROM_ENV if env.get(k)})
    for name, value in values.items():
        r = api.patch(f"{base}/actions/variables/{name}", json={"name": name, "value": value})
        if r.status_code == 404:
            r = api.post(f"{base}/actions/variables", json={"name": name, "value": value})
        check(r, f"Saving variable {name}")
        print(f"Variable: {name}={value}")

    # 4. Approval environment
    check(api.put(f"{base}/environments/production", json={
        "reviewers": [{"type": "User", "id": me["id"]}], "prevent_self_review": False}),
        "Creating the production environment")
    print(f"Environment 'production' created; required reviewer: {me['login']}")

    if "--test-run" in sys.argv:
        check(api.post(f"{base}/actions/workflows/daily.yml/dispatches",
                       json={"ref": "main", "inputs": {"dry_run": "true"}}), "Starting a test run")
        print(f"Test run started (dry run): https://github.com/{repo}/actions")
    return 0


if __name__ == "__main__":
    sys.exit(main())

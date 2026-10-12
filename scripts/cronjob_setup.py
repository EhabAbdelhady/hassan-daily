"""Creates (or updates) the cron-job.org job that starts the daily run at 12:05 Cairo time.

Needs in .env:
  GITHUB_REPO=owner/hassan-daily
  GITHUB_START_TOKEN=<fine-grained token, this repo only, Actions: Read and write>
  CRONJOB_API_KEY=<cron-job.org Console → Settings → API key>
Run:  .venv/bin/python scripts/cronjob_setup.py
It first checks the start token works (a start outside 12:00–14:00 is skipped silently), then saves the job.
Keys are never printed.
"""

import json
import sys
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
TITLE = "Hassan Daily start"
HOUR, MINUTE, TIMEZONE = 12, 5, "Africa/Cairo"


def main() -> int:
    env = dotenv_values(ROOT / ".env")
    repo = (env.get("GITHUB_REPO") or "").strip()
    start_token = (env.get("GITHUB_START_TOKEN") or "").strip()
    api_key = (env.get("CRONJOB_API_KEY") or "").strip()
    missing = [k for k, v in (("GITHUB_REPO", repo), ("GITHUB_START_TOKEN", start_token), ("CRONJOB_API_KEY", api_key)) if not v]
    if missing:
        print("Missing in .env:", ", ".join(missing))
        return 1

    url = f"https://api.github.com/repos/{repo}/actions/workflows/daily.yml/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {start_token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }
    body = json.dumps({"ref": "main", "inputs": {"trigger": "scheduled"}})

    # 1. Prove the start token can start the workflow (exactly what cron-job.org will send)
    r = requests.post(url, headers=headers, data=body, timeout=30)
    if r.status_code != 204:
        print(f"The start token was rejected by GitHub ({r.status_code}): {r.json().get('message', r.text[:200])}")
        print("Check it has access to this repository and 'Actions: Read and write'.")
        return 1
    print("Start token works (GitHub accepted a test start)")

    # 2. Create or update the cron-job.org job
    api = requests.Session()
    api.headers.update({"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    job = {
        "title": TITLE,
        "url": url,
        "enabled": True,
        "saveResponses": True,
        "requestMethod": 1,  # POST
        "schedule": {"timezone": TIMEZONE, "expiresAt": 0, "hours": [HOUR], "minutes": [MINUTE],
                     "mdays": [-1], "months": [-1], "wdays": [-1]},
        "extendedData": {"headers": headers, "body": body},
        "notification": {"onFailure": True, "onFailureCount": 1, "onSuccess": False, "onDisable": True},
    }
    r = api.get("https://api.cron-job.org/jobs", timeout=30)
    if r.status_code != 200:
        print(f"cron-job.org rejected the API key ({r.status_code}). Check CRONJOB_API_KEY.")
        return 1
    existing = [j for j in r.json().get("jobs", []) if j.get("title") == TITLE]
    if existing:
        job_id = existing[0]["jobId"]
        r = api.patch(f"https://api.cron-job.org/jobs/{job_id}", json={"job": job}, timeout=30)
        action = "updated"
    else:
        r = api.put("https://api.cron-job.org/jobs", json={"job": job}, timeout=30)
        job_id = r.json().get("jobId") if r.status_code == 200 else None
        action = "created"
    if r.status_code != 200:
        print(f"Saving the job failed ({r.status_code}): {r.text[:200]}")
        return 1
    print(f"cron-job.org job {action} (id {job_id}): every day at {HOUR:02d}:{MINUTE:02d} {TIMEZONE}, email on failure")
    return 0


if __name__ == "__main__":
    sys.exit(main())

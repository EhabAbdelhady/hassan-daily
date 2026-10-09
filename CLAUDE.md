# HASSAN DAILY — Arabic investment infographic automation

Generates a daily Arabic (RTL) 1080x1350 PNG infographic with Egyptian gold (24k/21k/18k), Bitcoin, USD/EGP (buy/sell), and Brent prices plus AI-written opportunities, risks, tips, and a social caption. It then emails a preview and posts to a Facebook Page and Instagram Business account.

Started in Google Antigravity (phases 1–3), continued in Claude Code. The original design reference is `/Users/ehab/.gemini/antigravity/brain/4c38aed3-44a6-4497-94bd-ad564df3488c/.user_uploaded/media_1791467956768_716ef27b.jpg`. Antigravity's plan is `implementation_plan.md` in the same folder.

## Phases
1. Template: HTML/CSS → PNG via Playwright (done)
2. Data collectors + `data/history.json` for day-over-day change (done)
3. AI text: configurable provider (gemini / openai / anthropic) (done)
4. Email preview + safety checks (missing/stale/abnormal-jump prices, verify rendered numbers)
5. Posting: Meta Graph API (FB Page + IG Business), image hosted on Cloudinary, token check, DRY_RUN, REQUIRE_APPROVAL
6. GitHub Actions: daily cron (Cairo time), keep-alive, `production` environment approval, approval cutoff (CUTOFF_HOURS)

## Layout
```
src/
  config.py              # Settings from env / .env (python-dotenv); paths
  collectors/            # One collector per asset, plus aggregator.py (builds the template payload)
    gold.py              # iSagha scrape (market.isagha.com/prices), uses the "بيع" (sell) price
    fx.py                # CBE exchange-rates page scrape
    crypto.py            # CoinGecko simple/price → Binance ticker fallback
    oil.py               # yfinance BZ=F
  storage/history.py     # data/history.json (one record per run, max 365)
  ai/                    # base.py (pydantic schema), prompts.py, factory.py, providers/*
  render/renderer.py     # Jinja2 → templates/rendered_infographic.html → Playwright screenshot
  utils/arabic_date.py   # Arabic date/timestamp strings
templates/               # infographic.html (Jinja2) + style.css; rendered_infographic.html is generated
assets/                  # Fixed images (header_bg.jpg, profile.png, card icons, icons/*.svg)
scripts/                 # One-off asset-prep scripts from Antigravity (hardcoded paths, need rembg); not part of the pipeline
tests/                   # Phase demo scripts (not pytest tests); they write to output/ and data/
output/                  # Generated PNGs
```

Template image paths are relative (`../assets/...`) because the rendered HTML is written into `templates/` and loaded via `file://`. Fonts come from Google Fonts over the network.

## Running
Python 3.12 venv at `.venv` (created with uv, so it has no pip; use `uv pip install -r requirements.txt` or `.venv/bin/python -m ...`).
```bash
cp .env.example .env            # fill in keys; never commit .env
.venv/bin/playwright install chromium
.venv/bin/python tests/test_render_phase1.py     # mock data render → output/phase1_preview.png
.venv/bin/python tests/test_collectors_phase2.py # live fetch (WRITES data/history.json) + render
.venv/bin/python tests/test_ai_phase3.py         # live fetch (no history write) + AI + render
```
Without an AI key, `factory.get_ai_provider()` falls back to `FallbackAnalyticalProvider` (canned text).

## Conventions
- All user-facing text is Arabic. Numbers shown on cards are formatted in `aggregator.py`.
- Never put secrets in code. All keys come from env vars (GitHub Secrets in CI).
- The user is not a developer. Docs and messages to them should be plain and step-by-step.
- Ask before choosing paid APIs or new data sources.

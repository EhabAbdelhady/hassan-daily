# HASSAN DAILY — Arabic investment infographic automation

Generates a daily Arabic (RTL) 1080x1350 PNG infographic with Egyptian gold (24k/21k/18k), Bitcoin, USD/EGP (buy/sell), and Brent prices plus AI-written opportunities, risks, tips, and a social caption. It then emails a preview and posts to a Facebook Page and Instagram Business account.

Started in Google Antigravity (phases 1–3), continued in Claude Code. The original design reference is `/Users/ehab/.gemini/antigravity/brain/4c38aed3-44a6-4497-94bd-ad564df3488c/.user_uploaded/media_1791467956768_716ef27b.jpg`. Antigravity's plan is `implementation_plan.md` in the same folder.

## Phases
1. Template: HTML/CSS → PNG via Playwright (done, fixed in Claude Code)
2. Data collectors + `data/history.json` for day-over-day change (done, fixed)
3. AI text: configurable provider (gemini in use, default anthropic / openai) (done, fixed)
4. Email preview + safety checks (missing/stale/abnormal-jump prices, verify rendered numbers) (done)
5. Posting: Meta Graph API (FB Page + IG Business), image hosted on Cloudinary, token check, DRY_RUN, REQUIRE_APPROVAL
6. GitHub Actions: daily cron (Cairo time), keep-alive, `production` environment approval, approval cutoff (CUTOFF_HOURS)

## Layout
```
main.py                  # CLI wrapper around src/pipeline.py (--no-history, --no-email)
src/
  config.py              # Settings from env / .env (python-dotenv); paths
  pipeline.py            # fetch → market checks → AI → render → image checks → save history → email.
                         # Any failure raises RunStopped → alert email; nothing is published
  safety/
    market_checks.py     # missing / stale (CBE in Sun–Thu working days) / jump vs yesterday / scraper sanity
    render_checks.py     # [data-verify] elements: page text, visibility, then RapidOCR on PNG crops
  notify/emailer.py      # Gmail SMTP (16-char app password) or Resend; send_preview / send_alert
  collectors/            # One collector per asset, plus aggregator.py (builds the template/AI payload)
    gold.py              # iSagha scrape (market.isagha.com/prices): "بيع" (sell) price + page's "آخر تحديث" time
    fx.py                # CBE English exchange-rates page: US Dollar buy/sell + "Last Updated" date
    crypto.py            # CoinGecko simple/price → Binance ticker fallback (both real sources)
    oil.py               # yfinance BZ=F 5-minute bars, labelled "Yahoo Finance"
  storage/history.py     # data/history.json, one record per Cairo date; "yesterday" = latest earlier date
  ai/
    base.py              # pydantic schema the model fills (bullets carry `based_on` indicators, not sources)
    prompts.py           # Arabic system/user prompts
    content.py           # Calls provider, checks every number/banned phrase, one retry, attaches real sources,
                         # builds caption with code-inserted prices + fixed DISCLAIMER
    factory.py, providers/*
  render/renderer.py     # Jinja2 → templates/rendered_infographic.html → Playwright screenshot
  utils/arabic_date.py   # Arabic dates; CAIRO_TZ = ZoneInfo("Africa/Cairo")
templates/               # infographic.html (Jinja2) + style.css; rendered_infographic.html is generated (ignored)
assets/                  # Fixed images, icons/*.svg, fonts/ (Cairo, Tajawal, Montserrat, OFL licensed, loaded via @font-face)
tests/                   # pytest (offline: parsers, content checks, history)
output/                  # Generated PNG + caption.txt (ignored)
```

## Rules the code enforces (keep them)
- Collectors never invent or reuse old values. A failed source raises `CollectorError`; the aggregator records it in `payload["errors"]` and the run stops.
- Card "last updated" is the source's own timestamp, not the run time.
- The AI never writes source names or the caption's price list; code adds them. Any number in AI text must match today's data (`check_text`).
- Daily change compares with the latest history record from an earlier Cairo date. History only saves complete data.
- Every number on the image has a `data-verify` attribute and is checked by text and by OCR. New numbers on the template need one.
- Gemini: rules go in the prompt, not system_instruction, and the schema goes in response_json_schema (the other forms get 503 on the free tier). Busy → retry, then gemini-3.5-flash-lite.
- The layout is a flex column. The analysis section absorbs leftover height, so longer AI text shrinks the whitespace, not the cards.

## Running
Python 3.12 venv at `.venv` (created with uv, so it has no pip; use `uv pip install --python .venv/bin/python -r requirements.txt`).
```bash
cp .env.example .env            # fill in keys; never commit .env
.venv/bin/playwright install chromium
.venv/bin/python -m pytest -q
.venv/bin/python main.py --no-history   # full run without writing data/history.json
```

## Conventions
- All user-facing text is Arabic.
- Never put secrets in code. All keys come from env vars (GitHub Secrets in CI).
- The user is not a developer. Docs and messages to them should be plain and step-by-step.
- Ask before choosing paid APIs or new data sources.
- Commit after each working phase.

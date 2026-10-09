# HASSAN DAILY: automatic daily investment infographic

Every day at **12:00 PM Cairo time** this project:

1. Collects today's prices from their real sources:
   - **Gold in Egypt** (24k / 21k / 18k): iSagha
   - **US dollar / Egyptian pound** (buy / sell): Central Bank of Egypt
   - **Bitcoin**: CoinGecko (Binance as backup)
   - **Brent oil**: Yahoo Finance
2. Checks every price: nothing missing, nothing too old, no abnormal jump since yesterday.
3. Asks an AI (Google Gemini) to write the Arabic opportunities, risks, and tips, **using only those numbers**. It checks every number the AI wrote and rejects promises of returns.
4. Builds the 1080×1350 Arabic image, then reads the image back to confirm every number on it is exactly right.
5. Emails you a **preview** (image + caption + the numbers used).
6. Waits for your **approval** on GitHub, then posts to your Facebook Page (and Instagram, when switched on).

If anything is wrong at any step, **nothing is posted** and you get an email explaining why.

---

## Your daily routine

1. Around 12:00 you get an email: **"✅ HASSAN DAILY preview – (date)"**. Check the image and caption.
2. GitHub also emails you: **"Deployment review required"** (or you get a notification in the GitHub mobile app).
3. To post it, open the link (or go to **github.com → your repository → Actions**, click today's run) and click **Review deployments → tick "production" → Approve and deploy**.
   To skip today, click **Reject** (or do nothing).
4. A minute later you get **"📣 HASSAN DAILY posted"** with the link.

You have **2 hours** after the preview to approve. A later approval posts nothing, and you get an email saying so, because prices may have moved.

The GitHub mobile app (iPhone/Android) lets you approve from your phone: open the notification → **Review** → **Approve**.

---

## Changing settings (no code needed)

Settings live on GitHub: **your repository → Settings → Secrets and variables → Actions → Variables tab**. Click a variable's pencil icon to change it.

| Variable | What it does | Values |
|---|---|---|
| `DRY_RUN` | `true`: everything runs and you get the emails, but **nothing is uploaded or posted**. | `true` / `false` |
| `REQUIRE_APPROVAL` | `true`: waits for your approval before posting. `false`: posts automatically right after the checks pass. | `true` / `false` |
| `CUTOFF_HOURS` | How long after the preview an approval still counts. | e.g. `2` |
| `POST_TO_FACEBOOK` | Post to the Facebook Page. | `true` / `false` |
| `POST_TO_INSTAGRAM` | Post to Instagram (needs the Instagram setup below). | `true` / `false` |
| `AI_PROVIDER` | Which AI writes the text. | `gemini` / `anthropic` / `openai` |
| `AI_MODEL` | Optional: a specific model. Leave empty for the default. | e.g. `gemini-3.8-flash` |
| `EMAIL_SERVICE` | How emails are sent. | `gmail` / `resend` |

**Changing the posting time:** edit `.github/workflows/daily.yml`. Change `POST_HOUR_CAIRO: "12"` to the new hour (24-hour clock) and the two `cron:` lines to that hour minus 3 and minus 2 (they're in UTC; for 12:00 Cairo they're `0 9` and `0 10`). Ask for help if unsure.

**Running it now, by hand:** **Actions → Daily infographic → Run workflow**. Leave "Dry run" ticked for a test, untick it for a real run.

---

## Secrets: the complete list

Secrets are stored encrypted on GitHub: **Settings → Secrets and variables → Actions → Secrets tab → New repository secret**. Use these exact names.

| Secret name | Required? | What it is / where to get it |
|---|---|---|
| `GEMINI_API_KEY` | Yes (with `AI_PROVIDER=gemini`) | Google AI Studio key, see [AI key](#1-ai-key-google-gemini-free) |
| `ANTHROPIC_API_KEY` | Only with `AI_PROVIDER=anthropic` | console.anthropic.com → API Keys |
| `OPENAI_API_KEY` | Only with `AI_PROVIDER=openai` | platform.openai.com → API keys |
| `GMAIL_USER` | Yes (with Gmail) | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Yes (with Gmail) | 16-letter app password, see [Email](#2-email-gmail-app-password) |
| `ALERT_RECIPIENT_EMAIL` | Yes | Where previews and alerts are sent |
| `RESEND_API_KEY` | Only with `EMAIL_SERVICE=resend` | resend.com → API Keys |
| `RESEND_FROM_EMAIL` | Only with Resend | A sender address on a domain verified in Resend |
| `CLOUDINARY_CLOUD_NAME` | Yes | Cloudinary dashboard, see [Image hosting](#3-image-hosting-cloudinary-free) |
| `CLOUDINARY_API_KEY` | Yes | Cloudinary → Settings → API Keys |
| `CLOUDINARY_API_SECRET` | Yes | Cloudinary → Settings → API Keys (click the eye icon) |
| `META_APP_ID` | Yes | Meta app → App settings → Basic |
| `META_APP_SECRET` | Yes | Meta app → App settings → Basic → Show |
| `META_PAGE_ACCESS_TOKEN` | Yes | Created by the helper, see [Meta](#4-facebook-page-meta) |
| `FACEBOOK_PAGE_ID` | Yes | Created by the helper |
| `INSTAGRAM_ACCOUNT_ID` | Only for Instagram | Created by the helper once Instagram is linked |
| `COINGECKO_API_KEY` | Optional | Free "Demo" key from coingecko.com; only needed if Bitcoin prices start failing |

The easiest way to set them all is the setup helper (see [GitHub](#5-github)), which copies them from your `.env` file.

---

## One-time setup, step by step

You only do this once. On your computer, the keys go in the file named `.env` in the project folder. It's hidden in Finder; press **Cmd+Shift+.** to show hidden files, then open it with TextEdit. **Never share this file or paste its contents anywhere.**

### 1. AI key (Google Gemini, free)
1. Go to **aistudio.google.com** and sign in with your Google account.
2. Click **Get API key** (bottom of the left menu) → **Create API key** → **Create API key in new project**.
3. Copy the key (it starts with `AQ.` or `AIza`) into `.env` after `GEMINI_API_KEY=`.

The free tier is enough for one post a day. If Google's main model is busy, the program waits and then uses a lighter free model automatically.

### 2. Email (Gmail app password)
1. Turn on 2-Step Verification: **myaccount.google.com/security**.
2. Go to **myaccount.google.com/apppasswords**, create one named `hassan-daily`.
3. Copy the 16-letter code into `.env` after `GMAIL_APP_PASSWORD=`, and put your Gmail address after `GMAIL_USER=` and `ALERT_RECIPIENT_EMAIL=`.

### 3. Image hosting (Cloudinary, free)
Instagram needs the image at a public web address; Cloudinary provides it.
1. Sign up at **cloudinary.com/users/register_free**.
2. In **console.cloudinary.com**, find:
   - **Cloud name**: top-left of the dashboard (or Settings → Product environment). Note: **not** the API key's name such as "Root".
   - **API Key** and **API Secret**: Settings → API Keys (click the eye icon to reveal the secret).
3. Put them in `.env`: `CLOUDINARY_CLOUD_NAME=`, `CLOUDINARY_API_KEY=`, `CLOUDINARY_API_SECRET=`.

### 4. Facebook Page (Meta)
**Create the app (once):**
1. Go to **developers.facebook.com**, log in, and register as a developer if asked.
2. Open **developers.facebook.com/apps/creation/**.
3. Name it `Hassan Daily Poster`, enter your email → **Next**.
4. Use case: **Manage everything on your Page** → **Next**. (Only this one is needed.)
5. Business: **I don't want to connect a business portfolio yet** → **Next** → **Go to dashboard**.
6. **Use cases → Manage everything on your Page → Customize**: make sure `pages_manage_posts` and `pages_read_engagement` are added.
7. **App settings → Basic**: copy **App ID** and **App secret** into `.env` (`META_APP_ID=`, `META_APP_SECRET=`).

**Get the Page token:**
1. Open **developers.facebook.com/tools/explorer**.
2. Meta App: `Hassan Daily Poster`. User or Page: **User Token**. Permissions: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`.
3. Click **Generate Access Token**. When Facebook asks which Pages to allow, **select only the Page you want to post to**.
4. Copy the token into `.env` after `META_USER_TOKEN=` (it's valid for about an hour, so continue right away).
5. In Terminal, in the project folder, run:
   ```bash
   .venv/bin/python scripts/meta_page_token.py
   ```
   It lists your Pages. Then run it again with the Page's name in quotes, for example:
   ```bash
   .venv/bin/python scripts/meta_page_token.py "FAIR DEAL STORE"
   ```
   It saves a Page token that doesn't expire, plus the Page ID, into `.env`, and deletes the temporary token.
6. If GitHub is already set up, copy the new values to GitHub by running the GitHub helper again (step 5).

### 5. GitHub
1. **Create the repository:** **github.com/new** → name `hassan-daily` → **Public** → leave README/.gitignore/license off → **Create repository**. Your `GITHUB_REPO` is the part of the address after `github.com/`, e.g. `YourName/hassan-daily`.
2. **Create a setup token:** **github.com/settings/personal-access-tokens/new**
   - Name `hassan-daily-setup`, expiration 7 days.
   - Repository access: **Only select repositories** → `hassan-daily`.
   - Repository permissions, each **Read and write**: Actions, Administration, Contents, Secrets, Variables, Workflows.
   - **Generate token**, copy it (starts with `github_pat_`).
3. Put both in `.env`: `GITHUB_REPO=` and `GITHUB_TOKEN=`.
4. Run:
   ```bash
   .venv/bin/python scripts/github_setup.py --test-run
   ```
   This uploads the code, copies your keys into GitHub Secrets (encrypted), sets the Variables, creates the **production** approval environment with you as reviewer, and starts a test run (dry run).

**If you'd rather set up the approval environment by hand:** repository → **Settings → Environments → New environment** → name it exactly `production` → tick **Required reviewers** → add your username → **Save protection rules**.

**Why public?** On GitHub's free plan, the approval button (required reviewers) only works on public repositories, and run minutes are unlimited. Anyone can see the code, the price history, and the images in `assets/`; your keys stay hidden in Secrets.

### 6. Instagram (when you're ready)
1. In the Instagram app: **Settings → Account type and tools → Switch to professional account**.
2. Link it to the Facebook Page: on the Page, **Settings → Linked accounts → Instagram → Connect**.
3. In the Meta app dashboard: **Add use cases** → the Instagram use case for managing content, and add the permissions `instagram_basic` and `instagram_content_publish`.
4. Generate a new token as in step 4 (add those two permissions too), run the Page token helper again (it now also saves `INSTAGRAM_ACCOUNT_ID`), then run the GitHub helper again.
5. Set the GitHub variable `POST_TO_INSTAGRAM` to `true`.

---

## Moving from the test Page to your main Page
1. Repeat **"Get the Page token"** in step 4, this time selecting **your main Page** and running the helper with its name.
2. Run `.venv/bin/python scripts/github_setup.py` to copy the new `META_PAGE_ACCESS_TOKEN` and `FACEBOOK_PAGE_ID` to GitHub. (If the setup token has expired, create a new one as in step 5.)
3. Keep `REQUIRE_APPROVAL=true` for the first days on the main Page.

## Renewing the Meta token
The Page token itself never expires, but Meta requires the app to be re-authorized every 90 days ("data access"). You'll get a warning in the preview email **14 days before**. To renew: repeat **"Get the Page token"** (step 4) for the same Page, then run the GitHub helper. It takes about 2 minutes.

---

## When you get an alert email
The subject starts with **"⚠️ HASSAN DAILY: not posted"**. Nothing was posted. Common reasons:

| Reason in the email | What it means | What to do |
|---|---|---|
| *a price is missing* | A source website or API was down. | Usually temporary. Run it again later by hand (Actions → Run workflow). |
| *last updated … ago* / *working days old* | A source hasn't updated (e.g. a holiday). | Wait for the source to update; skip the day if needed. |
| *changed …% since yesterday (limit …)* | A big jump. Could be real news or a wrong reading. | Check the price yourself. If it's real, run the workflow again by hand after checking. |
| *ratio … expected* | A website changed its layout and the price was read wrongly. | Needs a code fix; ask for help. |
| *the AI text failed the fact checks twice* | The AI used a number not in the data, or promised returns. | Run again by hand; it usually passes. |
| *the image doesn't show the fetched numbers correctly* | The image didn't render correctly. | Run again; if it repeats, ask for help. |
| *Meta token needs attention* | The Facebook token expired or lost permissions. | See "Renewing the Meta token". |
| *approval came after the cutoff* | You approved more than 2 hours after the preview. | Nothing; approve sooner next time. |
| *no response from Meta … It may have posted* | Facebook didn't answer. | Check the Page. It won't retry today, to avoid a duplicate post. |

If a run fails before it can email you (for example GitHub itself had a problem), GitHub sends its own **"Run failed"** email.

---

## For a developer (or Claude Code)
See `CLAUDE.md` for the code layout and the rules the code enforces.

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt pynacl
.venv/bin/playwright install chromium
cp .env.example .env                                   # fill in keys
.venv/bin/python -m pytest -q                          # offline tests
.venv/bin/python main.py prepare --no-history --no-email --dry-run   # local test, no side effects
.venv/bin/python main.py publish                       # post the prepared image (the "approve" step)
```

**Rolling back:** every working phase is a separate commit (`git log --oneline`). To undo a change, ask a developer to `git revert` the commit.

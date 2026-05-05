# moodle-tasks-sync

Personal automation that pulls open assignments from Tel Aviv University's
Moodle and creates Google Tasks for them. Runs unattended every day via
GitHub Actions; optional notifications via 4 channels.

> **For AI agents helping with setup:**
> You are guiding a TAU student through forking and configuring this repo to
> run their own Moodle→Google Tasks sync. They have basic GitHub fluency but
> Google Cloud Console will be unfamiliar. Follow Section 5 (Setup) step-by-step.
> After each step, run the verify command and confirm output before moving on.
> If a verify command fails, consult Section 8 (Troubleshooting) before continuing.
> The user should answer prompts but NOT skip steps. The user is on Windows or
> macOS — pick the matching code block per step. Linux users follow the macOS
> blocks.

## What it does

Each daily run:

1. Authenticates to TAU Moodle and fetches upcoming actionable assignments (next 30 days)
2. Compares with the `Uni Assignments` list in Google Tasks
3. Creates a new task for each assignment not yet in the list
4. Marks tasks complete when their assignment disappears from Moodle's Timeline
   (= submitted by you), provided the due date has not yet passed
5. Optionally pings you on any of 4 notification channels (see Section 6)

Re-running on the same day creates nothing new and changes nothing — the sync
is idempotent.

## Prerequisites

- A **TAU student account** whose Google sign-in goes through TAU's SSO
  (Google Workspace tenant). If you can't pick "Internal" in the OAuth consent
  screen later, your account isn't on Workspace and this won't work.
- A **GitHub account** (free tier is fine). If you don't have one, sign up at
  https://github.com first.
- **Python 3.11 or newer** installed locally. Check with `python --version`
  (Windows) or `python3 --version` (macOS/Linux).
- **Windows or macOS.** Linux works too — follow the macOS/bash code blocks.

## Setup

Each step has a verify command at the end. Don't skip ahead until verify passes.

### Step 1: Fork this repo on GitHub

Click the "Fork" button at the top-right of this repo's GitHub page. GitHub
will create your own copy at `https://github.com/<your-username>/moodle-automation`.

**Verify:** open `https://github.com/<your-username>/moodle-automation` in your
browser — it should show the fork.

### Step 2: Clone your fork locally

**Windows (PowerShell):**
```powershell
cd $HOME
git clone https://github.com/<your-username>/moodle-automation.git
cd moodle-automation
```

**macOS / Linux (bash):**
```bash
cd ~
git clone https://github.com/<your-username>/moodle-automation.git
cd moodle-automation
```

**Verify:** running `ls` (or `Get-ChildItem` on PowerShell) shows `src/`,
`tests/`, `scripts/`, and `README.md`.

### Step 3: Create a virtualenv and install dependencies

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux (bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Verify:** run `pytest -v` — you should see `12 passed` in the output. (If
this fails, see Troubleshooting Section 8.)

### Step 4: Set up your Google Cloud project

This is the longest step. Each TAU friend needs their own isolated Google
Cloud project. Follow the clicks exactly. *(As of 2026-05-05; if Google's UI
has changed, screenshot the discrepancy and message the project owner.)*

4a. Sign in to https://console.cloud.google.com/ with your **TAU account**
(not a personal Gmail).

4b. Click the project dropdown at the top → "New Project".

4c. Name it (suggested: `moodle-tasks-sync`) → click "Create". Wait for the
project to be created (a few seconds).

4d. Once created, type **"Tasks API"** in the top search bar → click the
**Tasks API** result → click the blue **"Enable"** button. Wait for it to
finish enabling.

4e. In the left sidebar, click **"APIs & Services"** → **"OAuth consent screen"**.

4f. **Important:** when asked for User Type, choose **"Internal"**.
> If "Internal" is **greyed out**, your account isn't part of Google
> Workspace — this project won't work for you. See Troubleshooting Section 8.

4g. Fill in:
- App name: `moodle-tasks-sync` (or whatever)
- User support email: your TAU email (auto-filled)
- Developer contact email: your TAU email

Click "Save and Continue".

4h. On the "Scopes" screen, click "Save and Continue" without adding any scopes.

4i. On the "Test users" screen, click "Save and Continue" without adding any.

4j. In the left sidebar, click **"Credentials"** → **"Create Credentials"** at
the top → **"OAuth client ID"**.

4k. Application type: **"Desktop app"**. Name it `moodle-tasks-sync-desktop`
(or whatever). Click "Create".

4l. A dialog shows your client ID. Click **"Download JSON"**. Save the file as
`credentials.json` in your `moodle-automation` project root (the folder you
cloned in Step 2).

**Verify:** in your terminal, from the project root:

**Windows:**
```powershell
Get-ChildItem credentials.json
```

**macOS / Linux:**
```bash
ls credentials.json
```

You should see the file listed (a few KB in size).

### Step 5: Run the setup script

This is the one local command that does the rest of the heavy lifting.

**Windows (PowerShell):**
```powershell
python scripts/setup.py
```

**macOS / Linux (bash):**
```bash
python3 scripts/setup.py
```

What happens:
- Your browser opens for Google OAuth — sign in with your TAU account → click
  "Continue" / "Allow"
- Browser shows a "The authentication flow has completed" message — close it
- Back in your terminal, you'll be prompted for your TAU username, ID, and
  password (password is masked as you type)
- The script then prints a long block with 5 secret name/value pairs

**Verify:** the script ends with a banner saying "Done. Now add these 5
secrets to GitHub" followed by 5 numbered secret pairs. Don't close this
terminal yet — you'll copy-paste from it in the next step.

### Step 6: Add the 5 secrets to GitHub

The setup script's output included a URL like:
`https://github.com/<your-username>/moodle-automation/settings/secrets/actions`

Open that URL in your browser. Click **"New repository secret"** five times,
once per pair from the script's output:

1. `TAU_USERNAME` — your TAU username
2. `TAU_ID` — your 9-digit TAU ID
3. `TAU_PASSWORD` — your TAU password
4. `GOOGLE_CREDENTIALS_B64` — long base64 string (paste exactly, no quotes)
5. `GOOGLE_TOKEN_B64` — another long base64 string (paste exactly, no quotes)

After saving each, GitHub redirects back to the secrets list. Confirm all 5
are listed.

**Verify:** the secrets page (`Settings → Secrets and variables → Actions`)
shows all 5 names with green checkmarks. (Values are not displayed by GitHub
once saved — that's normal and intentional.)

### Step 7: Trigger your first sync

Open your fork's "Actions" tab on GitHub:
`https://github.com/<your-username>/moodle-automation/actions`

You may see a yellow banner "Workflows aren't being run on this fork. Enable
them first." — click **"I understand my workflows, go ahead and enable them"**
if it appears.

In the left sidebar, click **"Daily Moodle sync"**. Then click the
**"Run workflow"** dropdown on the right → leave the branch as `master` →
click the green **"Run workflow"** button.

Wait ~30 seconds, then refresh. A new run appears at the top of the list. Wait
for it to finish (about 30-60 seconds).

**Verify:**
- The run shows a **green checkmark** (success)
- Click into the run → click "sync" → click "Run sync" to see the log; you
  should see lines like `[main] starting sync`, `[dedup] N new assignment(s)
  to push`, `[main] done. created=N completed=0`
- Open Google Tasks (https://tasks.google.com or in Gmail's side panel) — a
  list called **"Uni Assignments"** now exists, populated with your upcoming
  TAU assignments

If anything failed, see Troubleshooting Section 8.

## Notifications (optional)

When the daily sync creates a new task or auto-completes one, you can be
notified on any of four channels — all free, all opt-in, all independent.
Skip any channels you don't want; configure only the ones you do.

If you skip ALL channels, the sync runs silently — same as before. You discover
changes by checking Google Tasks.

### GitHub Issues *(recommended for first-time setup)*

Easiest channel — uses your existing GitHub account, no extra signup, no app
install. Each notification creates a closed GitHub issue assigned to you, which
fires **both** an in-app notification (the bell at github.com/notifications)
**and** an email to your GitHub primary email.

Set a repository **variable** (not secret) named `NOTIFY_GITHUB_ISSUES` to
`true`:

```bash
gh variable set NOTIFY_GITHUB_ISSUES --body "true"
```

Or via the web UI: Settings → Secrets and variables → Actions → Variables tab → New variable.

Note: GitHub auto-injects `GITHUB_REPOSITORY_OWNER` per fork, so the issue
auto-assigns to whoever owns the fork. No friend setup needed beyond the
single variable above.

### ntfy.sh — phone push notifications

Free push notifications without an account. Renders the message body cleanly
on the lock screen with a bold title row.

1. Install the **ntfy** app on your phone (iOS App Store or Android Play Store)
2. Pick a hard-to-guess topic name (treat it like a weak password — anyone who
   guesses it can read your messages or send fake ones). On Windows PowerShell:
   `[guid]::NewGuid().ToString()`
3. In the app, tap "+" → "Subscribe to topic" → enter your topic name
4. Set it as a repo **secret**:
   ```bash
   echo "your-topic-name" | gh secret set NTFY_TOPIC
   ```

### Telegram

Rich messages in your Telegram chat.

1. In Telegram, message **@BotFather** and run `/newbot`. Follow the prompts.
   You'll get a **bot token** (looks like `123456789:AB...`)
2. Send any message to your new bot to start a chat
3. Find your **chat ID**: visit
   `https://api.telegram.org/bot<your-bot-token>/getUpdates` in any browser
   and copy the `"chat":{"id":<number>}` value from the JSON response
4. Set both as repo **secrets**:
   ```bash
   echo "your-bot-token" | gh secret set TELEGRAM_BOT_TOKEN
   echo "your-chat-id" | gh secret set TELEGRAM_CHAT_ID
   ```

### Discord

Posts to any Discord server you own.

1. In Discord: Server Settings → Integrations → Webhooks → New Webhook
2. Pick a channel, name the webhook (e.g., "Moodle Sync"), copy the URL
3. Set it as a repo **secret**:
   ```bash
   echo "https://discord.com/api/webhooks/..." | gh secret set DISCORD_WEBHOOK_URL
   ```

### Disabling a channel later

Each channel is controlled by a single secret/variable. To disable:

```bash
gh variable delete NOTIFY_GITHUB_ISSUES   # GitHub Issues
gh secret delete NTFY_TOPIC               # ntfy
gh secret delete TELEGRAM_BOT_TOKEN       # Telegram (also delete TELEGRAM_CHAT_ID)
gh secret delete DISCORD_WEBHOOK_URL      # Discord
```

The next sync picks up the change immediately — no code edit, no redeploy.

### Verifying

After enabling channels, you can test by deleting one task in Google Tasks
and triggering the workflow manually:

```bash
gh workflow run "Daily Moodle sync"
```

The next run will re-create the deleted task and notify all configured channels.

## Daily life (after setup)

Once setup is done, the workflow runs automatically every day at **04:37 UTC**
(= 06:37 IST winter / 07:37 IDT summer). New assignments appear in your "Uni
Assignments" Google Tasks list; tasks for assignments you've submitted get
auto-checked.

To check whether the workflow ran today: visit your fork's Actions tab.

To manually trigger a run (e.g., to test): "Daily Moodle sync" → "Run workflow".

To disable a notification channel later: see Section 6 → "Disabling a channel
later".

To pause the project entirely (e.g., during exam break): in your fork, go to
**Settings → Actions → General** → set "Workflow permissions" to none, or just
delete the secrets (the workflow will fail silently and email you on failure).

## Troubleshooting

If a Setup step's verify command failed, find the symptom below.

### `pytest -v` fails or `pip install` errors out (Step 3)

- **SSL error during pip install** — likely a corporate network proxy. Try a
  different network (mobile hotspot).
- **Permission error / package conflicts** — make sure you activated the
  virtualenv before running pip (your prompt should start with `(.venv)`).
- **`pytest` command not found** — re-activate the venv. On Windows:
  `.venv\Scripts\Activate.ps1`. On macOS/Linux: `source .venv/bin/activate`.

### "Internal" is greyed out in Google Cloud OAuth consent (Step 4)

Your account isn't part of Google Workspace. The project owner's setup relies
on TAU's Workspace tenant — if your TAU account doesn't sign in via TAU's
Google login page, you can't use Internal mode, and the workflow's unattended
runs won't work (External mode tokens expire every 7 days).

Action: confirm with TAU IT, or message the project owner.

### Setup script can't open browser for OAuth (Step 5)

You're probably running on a headless server or over SSH. Run the script on a
machine with a real browser (your laptop), then copy the resulting
`token.json` to wherever you're deploying.

### Setup script says "credentials.json not found" (Step 5)

The downloaded JSON didn't end up in the project root. Check:
- The file is named exactly `credentials.json` (not `client_secret_xxx.json`
  — rename it if needed)
- It's in the same folder as `README.md`, not in a subfolder

### `python scripts/setup.py` fails with import error (Step 5, macOS)

Mac defaults `python` to Python 2.7 in some setups. Use `python3` explicitly:
```bash
python3 scripts/setup.py
```

### Workflow fails on first run with "TAU auth failed" / login error (Step 7)

Your TAU password may have a typo. Re-run the setup script (`python
scripts/setup.py`) and retype the password carefully. Re-update the
`TAU_PASSWORD` secret with the new value (paste the password value again from
the new run).

### Workflow fails with "Tasks API has not been used" (Step 7)

You forgot Step 4d (enabling the Tasks API). Go back to Google Cloud Console
→ search "Tasks API" → click "Enable".

### ntfy notification never arrives (Step 7)

- Confirm the topic name in your `NTFY_TOPIC` secret matches the topic you
  subscribed to in the ntfy phone app exactly (no typos, same case)
- Re-trigger the workflow with `gh workflow run "Daily Moodle sync"` (or via
  the Actions tab)

### GitHub Issues notification never arrives (Step 7)

- Check the in-app notifications bell first
  (https://github.com/notifications) — it usually arrives there even if email
  is delayed
- Check your spam folder for emails from `notifications@github.com`
- Confirm `NOTIFY_GITHUB_ISSUES` is set as a **variable** (not a secret) with
  value `true` — these are different in GitHub's UI

## What this project is not

- Not a calendar sync (uses Google Tasks, not Calendar)
- Not a real-time integration (daily, not push-based)
- Not officially affiliated with Tel Aviv University
- Not maintained on a schedule — best-effort by the project owner. If you
  fork it and it breaks, you may need to fix it yourself or wait
- Not a multi-user service — each fork is a standalone deployment with its
  own credentials

## License / status

Personal automation. Use at your own risk; this is unofficial and may violate
TAU's terms of service.

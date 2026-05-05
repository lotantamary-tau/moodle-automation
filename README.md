# moodle-tasks-sync

Personal automation that pulls open assignments from Tel Aviv University's
Moodle and creates Google Tasks for them. Runs unattended every day via GitHub
Actions; optional notifications via 4 channels.

## What it does

Each run:

1. Authenticates to TAU Moodle and fetches upcoming assignments (next 30 days)
2. Compares with the `Uni Assignments` list in Google Tasks
3. Creates a new task for each assignment not yet in the list
4. Marks tasks complete when their assignment disappears from Moodle's Timeline
   (= submitted by you), provided the due date has not yet passed

Re-running on the same day creates nothing new and changes nothing — the sync
is idempotent.

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

## Requirements

- Python 3.11+
- A TAU student account whose Google sign-in goes through TAU's SSO (Google
  Workspace tenant)
- Tested on Windows 11 (PowerShell)

## Setup

1. Clone this repo
2. Create a virtualenv and install dependencies:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Set up your Google OAuth credentials (one-time). The short version:
   - Sign in to https://console.cloud.google.com with your TAU account
   - Create a new project, enable the Tasks API
   - Configure the OAuth consent screen as **Internal** user type
   - Create OAuth client credentials (Desktop app) and download the JSON
   - Save it as `credentials.json` in the project root
   - Step-by-step instructions are in
     [docs/superpowers/specs/2026-05-03-moodle-tasks-sync-v1-design.md](docs/superpowers/specs/2026-05-03-moodle-tasks-sync-v1-design.md)
4. Copy `.env.example` to `.env` and fill in your TAU credentials:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Run the sync:

   ```powershell
   python -m src.main
   ```

   The first run opens a browser for Google sign-in. Subsequent runs use the
   cached `token.json` (which doesn't expire because the OAuth app is in
   Internal mode).

## Tests

```powershell
pytest
```

## What's not done yet

v1 ships as a local manual run. The following are explicitly deferred:

- Scheduled execution via GitHub Actions (v1.5)
- Friend onboarding via the fork model (v1.5)
- Updating tasks when Moodle due dates change (current logic is create-only;
  date changes are not propagated)

## License / status

Personal automation. Use at your own risk; this is unofficial and may violate
TAU's terms of service.

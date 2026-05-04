# moodle-tasks-sync

Personal automation that pulls open assignments from Tel Aviv University's
Moodle and creates Google Tasks for them. v1 is locally-runnable.

## What it does

Each run:

1. Authenticates to TAU Moodle and fetches upcoming assignments (next 30 days)
2. Compares with the `Uni Assignments` list in Google Tasks
3. Creates a new task for each assignment not yet in the list
4. Marks tasks complete when their assignment disappears from Moodle's Timeline
   (= submitted by you), provided the due date has not yet passed

Re-running on the same day creates nothing new and changes nothing — the sync
is idempotent.

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
- Notifications on completion (Telegram, email, etc.)

## License / status

Personal automation. Use at your own risk; this is unofficial and may violate
TAU's terms of service.

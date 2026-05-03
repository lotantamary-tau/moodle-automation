# PRD: Moodle Assignments → Google Tasks Automation

## Overview

A personal automation that runs weekly, fetches the user's open assignments from Tel Aviv University's Moodle, and adds them to Google Tasks with their due dates. Designed to be shareable with other TAU students via GitHub forks, where each user runs their own independent instance with their own credentials.

This document is the foundation. The architecture decisions below are committed; feature scope and personalization details are intentionally flexible and will be planned together with Claude Code during build.

---

## Goal

The user is a TAU student who wants to stop manually checking each Moodle course for upcoming assignments. Every Saturday morning, the automation should:

1. Authenticate to TAU Moodle programmatically
2. Fetch all upcoming assignments across all enrolled courses
3. Filter out anything already submitted, overdue, or already in Google Tasks
4. Push remaining assignments to Google Tasks with proper due dates
5. Run unattended in the cloud — user's computer can be off

Future features (smart prioritization, AI summaries, multi-app integration) are planned but out of scope for v1.

---

## Architecture Decisions (committed)

### Authentication: `tau-tools` Python library
TAU Moodle uses a custom three-field login (username + ID + password) that the standard Moodle Web Services API cannot reach. The `tau-tools` library (https://github.com/arazimproject/tau-tools, available on PyPI as `tau-tools`) handles this auth flow by mimicking browser-style login, capturing the session cookie, and calling Moodle's internal `block_timeline_extra_local_get_action_events_by_timesort` endpoint — the same one that powers the Timeline widget on the Moodle dashboard.

Key methods used:
- `Moodle(username, id, password, session_file)` — constructor, caches session in JSON file to avoid re-authenticating every run
- `m.get_courses()` — returns list of `CourseInfo` (id, name, is_hidden, is_favourite)
- `m.get_assignments(limit, since, until)` — returns list of `AssignmentInfo` (id, name, course_id, course_name, due_date, is_overdue)

### Scheduler: GitHub Actions
- Free for personal use
- Cloud-hosted, computer can be off
- Deterministic scheduling via cron expression
- Encrypted secrets management built in (per-repo)
- Clear logs for debugging

Rejected alternatives and why:
- **Claude Routines / Cowork**: introduces LLM variance into a deterministic pipeline; consumes Pro plan tokens unnecessarily
- **Make.com**: cannot run arbitrary Python; would still need GitHub Actions underneath
- **Local cron**: requires user's computer to be on
- **Other clouds (AWS Lambda, Google Cloud Scheduler)**: overkill, require credit card and platform-specific learning

### Output: Google Tasks API
- Free within generous personal-use quotas
- Native Google account integration
- Each user authorizes their own Google account via OAuth (one-time browser step)

### LLM usage in runtime: none for v1
The Pro plan does not include API usage. v1 personalization is achieved through plain Python rules (deterministic, free, predictable). The Anthropic API can be added later as a paid add-on if/when features genuinely need reasoning (e.g., assignment description summarization).

### Repository model: public repo, no collaborators, fork-based sharing
- **Repository owner (the original author)** maintains the canonical version. No collaborators are added — only the owner can push to the original repo.
- **Other users (friends, other TAU students)** fork the repo to their own GitHub account. Each fork is an independent repo under the friend's account.
- **Each fork has its own isolated GitHub Secrets** (secrets are stored per-repo, not per-account, and forks do not inherit secrets — this is enforced by GitHub for security).
- **Each fork's GitHub Actions runs independently** using that fork's secrets, on that fork's schedule.
- **When the original is updated**, friends use GitHub's "Sync fork" button to pull the latest code into their fork. Their secrets and schedule are preserved.

Why this model:
- **Credential isolation is automatic**: there is no scenario where one user's secrets are visible to another, because secrets live in each fork independently
- **No write-access risk**: friends cannot accidentally push breaking changes to the canonical repo
- **Standard open-source pattern**: friends know how to use it, GitHub's UI supports it natively
- **Easy updates**: one click for friends to pull in improvements

Naming consideration: the repo should have a generic name (e.g., `moodle-tasks-sync`) rather than something that explicitly references TAU, to reduce discovery by parties who might draw attention to the underlying auth dependency.

---

## Tech Stack

- **Language**: Python 3.11+
- **Core dependencies**: `tau-tools`, `google-api-python-client`, `google-auth-oauthlib`, `python-dotenv` (local dev only)
- **Runtime**: GitHub Actions (`ubuntu-latest`)
- **Scheduling**: cron expression in workflow YAML
- **Secrets storage**: GitHub Secrets per-repo (production), `.env` file (local dev, git-ignored)

---

## Repository Structure (proposed, flexible)

```
moodle-tasks-sync/
├── .github/
│   └── workflows/
│       └── weekly.yml          # GitHub Actions workflow
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── moodle_client.py        # Wraps tau-tools, returns clean assignment list
│   ├── tasks_client.py         # Wraps Google Tasks API, handles auth + writes
│   ├── dedup.py                # Avoids duplicate task creation
│   └── config.py               # Reads env vars, defines user preferences
├── tests/                      # Optional, decided during build
├── .env.example                # Template for local dev — placeholders only
├── .gitignore                  # Must include .env, session.json, token.json, __pycache__
├── requirements.txt
├── README.md                   # Setup instructions for forkers
└── PRD.md                      # This document
```

---

## Credential Handling

### Required secrets (per-fork, per-user)
- `TAU_USERNAME` — TAU Moodle username
- `TAU_ID` — TAU student ID number
- `TAU_PASSWORD` — TAU Moodle password
- `GOOGLE_CREDENTIALS_JSON` — Google OAuth client credentials (JSON, base64-encoded for GitHub Secrets)
- `GOOGLE_TOKEN_JSON` — Google OAuth refresh token (obtained once via local auth flow, stored as secret)

### Local development
A `.env` file at project root, listed in `.gitignore`, never committed. Loaded via `python-dotenv` only when running locally.

### Production (GitHub Actions)
Same variable names, stored in each user's fork's Settings → Secrets and variables → Actions. Workflow YAML injects them as environment variables at runtime.

### Google OAuth flow
First-time setup is local (browser-based consent). After authorization, the resulting `token.json` is stored as a GitHub Secret in the user's fork. Token auto-refreshes during runtime; no further user interaction needed unless revoked.

### Isolation guarantee
Because GitHub Secrets are stored per-repo, and forks do not inherit secrets from their parent, each user's credentials are completely isolated. Nobody (including the original author) can see anyone else's secrets.

---

## Functional Requirements (v1)

### Must have
1. Weekly trigger (default: Saturday 09:00 Israel time, configurable)
2. Authenticate to TAU Moodle, cache session for efficiency
3. Fetch all assignments with due dates in a configurable window (default: next 30 days)
4. Filter out:
   - Assignments marked overdue
   - Assignments already present in target Google Tasks list (deduplication by Moodle assignment ID stored in task notes or task title)
5. Create Google Tasks with:
   - Title format (default, configurable): `[Course Name] Assignment Name`
   - Due date matching Moodle due date
   - Notes field containing Moodle assignment ID (used for dedup)
6. Run idempotently — re-running on the same day must not create duplicates
7. Log clearly to GitHub Actions output

### Should have (v1.1, decided during build)
- Configurable target Google Tasks list (one global list, or per-course lists)
- Configurable task title format via config file
- Course filtering (skip courses by ID or name)
- Manual trigger option (workflow_dispatch) for testing

### Future (out of scope for v1)
- Urgency scoring and prioritization
- AI-generated assignment summaries (would require paid Anthropic API)
- Telegram / WhatsApp / email notifications
- Google Calendar integration alongside Tasks
- Submission status detection (currently `tau-tools` doesn't expose this; would require library extension or DOM scraping)
- Notion / Obsidian integration

---

## Non-Functional Requirements

- **Privacy**: credentials never leave each user's GitHub Secrets or local `.env`; never logged
- **Reliability**: single failed run is acceptable; workflow should not crash on transient errors but log and continue
- **Cost**: zero monthly cost for v1
- **Maintenance**: when `tau-tools` breaks (e.g., TAU changes Moodle), update the dependency version; if endpoint changes, contribute upstream
- **Compliance**: this is unofficial automation. Each user accepts that it may violate TAU's terms of service and that risks (account lockout, etc.) are their own. Public repo naming and documentation should not advertise TAU specifically.

---

## Open Questions to Resolve During Build

1. Should multiple Google Tasks lists be used (one per course), or a single list with course in the title?
2. What happens to a task in Google Tasks if its Moodle due date changes between runs? (Update existing task, or leave alone?)
3. What happens if the user manually completes a task in Google Tasks but the Moodle assignment is still open? (Skip on next run, or recreate?)
4. Should the script send a summary message anywhere (email/Telegram) on completion, or run silently?
5. How to handle session cookie expiration mid-run — retry with fresh login, or fail loudly?
6. Should there be a "dry run" mode that logs intended actions without actually creating tasks?

These are intentionally left open for the build phase with Claude Code.

---

## Setup Steps for a New User (preview, will become README)

1. Click "Fork" on the GitHub repo page → creates your own copy under your GitHub account
2. Clone your fork locally: `git clone <your-fork-url>`
3. Create `.env` from `.env.example` with your personal credentials
4. Set up Google OAuth credentials in Google Cloud Console (one-time)
5. Run local auth flow once to generate `token.json`
6. Test locally: `python -m src.main`
7. Add your credentials to your fork's GitHub Secrets (Settings → Secrets and variables → Actions)
8. Enable Actions in your fork's settings
9. Done — runs every Saturday automatically in your fork

### Pulling future updates
When the original repo is updated, GitHub will show a "This branch is X commits behind" banner on your fork. Click "Sync fork" → "Update branch" to pull the latest code. Your secrets and schedule are preserved.

---

## Success Criteria for v1

- User runs the workflow manually once and sees their upcoming TAU assignments appear in Google Tasks with correct due dates
- The next Saturday, the workflow runs automatically with no user action
- Re-running the workflow on the same day does not create duplicate tasks
- A friend can fork the repo, follow the README, and have it working within 30 minutes

# Project Overview

Personal automation that runs weekly in the cloud, pulls open assignments from
Tel Aviv University's Moodle, and creates Google Tasks for them with correct due
dates. Built so it can be forked by other TAU students who run their own
isolated instance with their own credentials. Exists because manually checking
each course every week is tedious and assignments get missed.

**Status:** Phase 2 complete. The sync runs unattended every day at 04:37 UTC
via GitHub Actions; notifies the user via any configured channels (GitHub
Issues, ntfy.sh, Telegram, Discord); and is forkable by friends via a one-
command bootstrap script (`scripts/setup.py`) and a comprehensive README
walkthrough. Umbrella restructure (a future Phase 3) is deferred until a
second automation actually exists.

## Tech Stack & Environment

- **Language:** Python 3.11+
- **Core libraries (proposed):** `tau-tools`, `google-api-python-client`,
  `google-auth-oauthlib`, `python-dotenv` (local dev only)
- **Runtime:** GitHub Actions, `ubuntu-latest`, cron-scheduled
- **Required env vars** (same names locally and in CI):
  - `TAU_USERNAME`, `TAU_ID`, `TAU_PASSWORD`
  - `GOOGLE_CREDENTIALS_JSON` (base64-encoded for GitHub Secrets)
  - `GOOGLE_TOKEN_JSON` (refresh token from one-time local OAuth flow)

## Key Directories & Architecture

Proposed in [PRD.md:83-103](PRD.md#L83-L103) — none of this exists on disk yet.

| Path | Role |
|---|---|
| `src/main.py` | Entry point: orchestrates fetch → filter → push |
| `src/moodle_client.py` | Wraps `tau-tools`, returns clean assignment list |
| `src/tasks_client.py` | Wraps Google Tasks API: auth + writes |
| `src/dedup.py` | Prevents duplicate task creation across runs |
| `src/config.py` | Reads env vars, defines user preferences |
| `.github/workflows/weekly.yml` | Cron-triggered Actions workflow |
| `tests/` | Optional, decided during build |

The wrapper-per-external-service split is deliberate: it isolates `tau-tools`
breakage from Google Tasks logic and leaves room to add future Moodle
integrations (calendar, grades, etc.) alongside `moodle_client.py` without
touching the orchestrator. See
[.claude/docs/architectural_patterns.md](.claude/docs/architectural_patterns.md).

## Build & Test Commands

```powershell
# Local setup (one-time)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run the sync (loads .env via python-dotenv)
python -m src.main

# Run unit tests
pytest
```

CI runs (v1.5) will use the same `python -m src.main` entry point — the
GitHub Actions workflow is just a thin YAML wrapper that injects secrets as
env vars.

## Architecture quick reference

- [src/main.py](src/main.py) — orchestrator: fetch → dedup → create + complete
- [src/config.py](src/config.py) — env-var loader, returns typed `Config`
- [src/models.py](src/models.py) — `Assignment` and `Task` dataclasses (only
  types crossing module boundaries)
- [src/moodle_client.py](src/moodle_client.py) — wraps `tau-tools`, returns
  `list[Assignment]`. Course-name prefix stripping happens here.
- [src/tasks_client.py](src/tasks_client.py) — wraps Google Tasks API.
  Find-or-create the `Uni Assignments` list; list/create/mark-complete tasks.
- [src/dedup.py](src/dedup.py) — pure functions `find_new` and
  `find_completed`. The only tested module.
- [tests/test_dedup.py](tests/test_dedup.py) — 10 unit tests.
- [src/notifier.py](src/notifier.py) — optional notifications across 4
  channels (GitHub Issues, ntfy.sh, Telegram, Discord); each opt-in via secret
- [tests/test_notifier.py](tests/test_notifier.py) — 2 unit tests for the
  message formatter
- [scripts/setup.py](scripts/setup.py) — friend bootstrap script, run once
  after fork; runs OAuth flow, prompts for TAU credentials, prints all 5
  GitHub Secrets ready to paste
- [.github/workflows/sync.yml](.github/workflows/sync.yml) — daily cron at 05:00 UTC; runs `python -m src.main` with secrets injected as env vars

## Conventions & Anti-patterns

**Naming:** Python `snake_case` for modules, functions, variables; `PascalCase`
for classes. Aim for descriptive names over clever ones.

**Patterns used:**
- Wrapper modules around each external service (`moodle_client`, `tasks_client`)
- 12-factor env-var config: `os.environ["..."]` works identically locally and in CI
- Idempotent sync: re-running on the same day must not create duplicates
- Session caching for `tau-tools` to avoid re-authenticating every run

**Avoid:**
- **Touching downstream code until `tau-tools` is verified end-to-end against a
  real TAU account.** The whole project rests on this dependency working — it
  has not yet been executed by the project owner. A 10-line spike comes before
  any architecture work.
- **LLM calls in the runtime** for v1 — Pro plan does not include API usage and
  v1 personalization is deterministic Python. See
  [DECISIONS.md:54-65](DECISIONS.md#L54-L65).
- **Hardcoded credentials anywhere.** Always env vars. `.env` must stay in
  `.gitignore` alongside `session.json` and `token.json`.
- **User-specific data in committed code** (paths, usernames, course IDs).
  The same code must work in any forker's repo.
- **TAU branding in repo metadata, README headlines, or workflow names.** Use
  generic names like `moodle-tasks-sync` to avoid drawing attention to the
  underlying `tau-tools` dependency. See [DECISIONS.md:85](DECISIONS.md#L85).
- **Scope creep without asking.** Default stance is pragmatic-but-ask: when an
  addition outside [PRD.md:130-145](PRD.md#L130-L145) v1 must-haves looks
  tempting, surface it as a quick proposal with cost/benefit before writing it.
  v1 must-haves first; should-haves and open questions get an explicit decision.
- **Logging credentials** at any level. Workflow logs are visible in Actions UI.
- **Destructive Google Tasks operations** without dry-run / confirmation — this
  writes to a real personal account.

**Open design questions** (deferred from PRD.md:172-181, decide before writing
the affected code, not at runtime): dedup behaviour when user manually
completes a task; behaviour when Moodle due date changes; one-list vs
list-per-course; dry-run mode.

## Maintenance

This file is a living document. Claude must update it automatically — without
being asked — whenever any of the following occur:
- A new file or directory is added that changes the project structure
- A new dependency, library, or tool is introduced
- A build, test, or run command is established or changes
- An architectural pattern or convention is established or changed
- An "open design question" above gets resolved (move it into the relevant
  section, don't leave it dangling)

Update only the affected section(s). Do not rewrite the whole file. Apply the
same updates to `.claude/docs/architectural_patterns.md` when relevant.

When `tau-tools` breaks (TAU changes their Moodle), bump the dependency
version; if the underlying endpoint changed, contribute upstream rather than
forking the library locally.

## Additional Documentation

- [PRD.md](PRD.md) — full product requirements: scope, secrets, success criteria
- [DECISIONS.md](DECISIONS.md) — *why* each architectural choice was made; read
  this before challenging any "committed" decision
- [.claude/docs/architectural_patterns.md](.claude/docs/architectural_patterns.md) —
  proposed patterns and design decisions; will be populated with `file:line`
  references as code is written

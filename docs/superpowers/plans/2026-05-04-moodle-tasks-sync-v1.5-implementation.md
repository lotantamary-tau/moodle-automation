# Moodle → Google Tasks Sync — v1.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> Each task is labeled `[SUBAGENT]`, `[USER]`, or `[SUBAGENT + USER verify]` so the controller knows whether to dispatch or hand off to the user.

**Goal:** Wire the existing v1 sync into a daily GitHub Actions cron at 05:00 UTC so it runs unattended without changing how the script behaves locally.

**Architecture:** One new file (`.github/workflows/sync.yml`), one small code change (Israel-local timezone for `today` in `main.py`), one new dependency (`tzdata` for Windows zoneinfo support), and 5 GitHub Secrets configured in the repo settings. No changes to module structure, no friend onboarding, no notifications.

**Tech Stack:** Python 3.11+, GitHub Actions (`ubuntu-latest`), `actions/checkout@v4`, `actions/setup-python@v5`, `zoneinfo` (stdlib) + `tzdata` (Windows compat), `pip install -r requirements.lock.txt`.

**Spec:** [docs/superpowers/specs/2026-05-04-moodle-tasks-sync-v1.5-design.md](../specs/2026-05-04-moodle-tasks-sync-v1.5-design.md)

---

## File Structure (final state at end of v1.5)

| Path | Change | Responsibility |
|---|---|---|
| `src/main.py` | Modified | Use Israel-local date for `today` (was `date.today()` which returns OS-local; OS in CI is UTC) |
| `requirements.txt` | Modified | Add `tzdata` for Windows zoneinfo compatibility |
| `requirements.lock.txt` | Modified | Re-pin including new transitive deps |
| `.github/workflows/sync.yml` | New | The whole v1.5 deliverable: cron + manual trigger + secret injection |

No restructuring of `src/`. No new modules. No new tests. No README changes (those are for friend onboarding, deferred).

## Working Assumptions Locked In For This Plan

- **Schedule:** daily at 05:00 UTC (= 07:00 IST winter / 08:00 IDT summer)
- **Manual trigger:** `workflow_dispatch` enabled for ad-hoc testing
- **Python version in CI:** 3.11 (lowest supported per requirements; user runs 3.13 locally)
- **Secrets:** 3 plain text + 2 base64 (full list in Task C.1)
- **Notifications:** silent + GitHub's default workflow-failure email
- **Retries:** none (one failed run acceptable; idempotency handles recovery)
- **Timezone library:** `zoneinfo` from stdlib + `tzdata` package for Windows compatibility
- **Working directory** for all subagent tasks: `c:\Users\lotan\UniversityDev\moodleAgent\`
- **Python interpreter** for all subagent tasks: `.venv/Scripts/python.exe`
- **Pytest binary** for all subagent tasks: `.venv/Scripts/pytest.exe`
- **gh CLI**: already authenticated as `lotantamary-tau`; subagent tasks may use `gh` commands freely

If any assumption changes before execution starts, the affected tasks must be revised.

---

## Phase A — Code Preparation

### Task A.1: Add tzdata to dependencies and re-lock  `[SUBAGENT]`

**Files:**
- Modify: `requirements.txt`
- Modify: `requirements.lock.txt`

- [ ] **Step 1: Append `tzdata` to `requirements.txt`**

Open `requirements.txt`. The full final file content should be:

```
tau-tools>=0.1.0
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.2.0
python-dotenv>=1.0.0
pytest>=8.0.0
tzdata>=2024.1
```

- [ ] **Step 2: Install the new dependency in the venv**

Run: `.venv/Scripts/pip.exe install -r requirements.txt`

Expected: `tzdata` is installed (typically zero transitive deps).

- [ ] **Step 3: Verify zoneinfo can resolve Asia/Jerusalem**

Run:
```
.venv/Scripts/python.exe -c "from zoneinfo import ZoneInfo; from datetime import datetime; print(datetime.now(tz=ZoneInfo('Asia/Jerusalem')).strftime('%Y-%m-%d %H:%M %z'))"
```

Expected: prints the current Israel-local date and time with the timezone offset. If it raises `ZoneInfoNotFoundError`, tzdata isn't installed correctly — escalate.

- [ ] **Step 4: Re-lock dependencies**

Use the Write tool to capture pip freeze output and write to the file plain (avoids PowerShell BOM issues):

```
.venv/Scripts/pip.exe freeze
```

Capture the output and use the Write tool to overwrite `requirements.lock.txt` with that exact content (UTF-8, no BOM).

Verify the lockfile contains `tzdata`:

```
.venv/Scripts/python.exe -c "import re; assert re.search(r'^tzdata==', open('requirements.lock.txt').read(), re.M); print('ok')"
```

Expected: `ok`

- [ ] **Step 5: Commit**

```
git add requirements.txt requirements.lock.txt
git commit -m "chore: add tzdata for cross-platform zoneinfo support"
```

### Task A.2: Switch main.py to Israel-local date  `[SUBAGENT]`

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: Read the current `src/main.py`**

The file currently begins with:

```python
"""Entry point: orchestrates fetch -> dedup -> create+complete."""

import sys
from datetime import date

from src import config, dedup, moodle_client, tasks_client
```

And contains this line in `main()`:

```python
    to_complete = dedup.find_completed(assignments, active_existing, today=date.today())
```

- [ ] **Step 2: Update the imports**

Replace:

```python
import sys
from datetime import date
```

with:

```python
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
```

(Remove `date` since we no longer call `date.today()` directly. `datetime` is needed for `.now()`.)

- [ ] **Step 3: Update the `today` line**

Replace:

```python
    to_complete = dedup.find_completed(assignments, active_existing, today=date.today())
```

with:

```python
    israel_today = datetime.now(tz=ZoneInfo("Asia/Jerusalem")).date()
    to_complete = dedup.find_completed(assignments, active_existing, today=israel_today)
```

The two-line form makes the intent (Israel-local date) explicit and easy to grep for.

- [ ] **Step 4: Verify imports and syntax**

Run: `.venv/Scripts/python.exe -c "from src import main; print('ok')"`

Expected: `ok`

- [ ] **Step 5: Run all unit tests to confirm no regression**

Run: `.venv/Scripts/pytest.exe -v`

Expected: 10 passed.

- [ ] **Step 6: Run the script to confirm it still works locally**

Run: `.venv/Scripts/python.exe -m src.main`

Expected: same output as before (likely `created=0 completed=0` since nothing changed in Moodle). No errors.

- [ ] **Step 7: Commit**

```
git add src/main.py
git commit -m "fix: use Israel-local date for find_completed today parameter"
```

---

## Phase B — Create the Workflow YAML

### Task B.1: Write the GitHub Actions workflow  `[SUBAGENT]`

**Files:**
- Create: `.github/workflows/sync.yml`

- [ ] **Step 1: Create the directory and file**

Use the Write tool to create `.github/workflows/sync.yml` with this exact content:

```yaml
name: Daily Moodle sync

on:
  schedule:
    # Daily at 05:00 UTC (= 07:00 IST winter / 08:00 IDT summer)
    - cron: "0 5 * * *"
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: requirements.lock.txt

      - name: Install dependencies
        run: pip install -r requirements.lock.txt

      - name: Decode Google credentials
        env:
          GOOGLE_CREDENTIALS_B64: ${{ secrets.GOOGLE_CREDENTIALS_B64 }}
          GOOGLE_TOKEN_B64: ${{ secrets.GOOGLE_TOKEN_B64 }}
        run: |
          echo "$GOOGLE_CREDENTIALS_B64" | base64 --decode > credentials.json
          echo "$GOOGLE_TOKEN_B64" | base64 --decode > token.json

      - name: Run sync
        env:
          TAU_USERNAME: ${{ secrets.TAU_USERNAME }}
          TAU_ID: ${{ secrets.TAU_ID }}
          TAU_PASSWORD: ${{ secrets.TAU_PASSWORD }}
          GOOGLE_CREDENTIALS_PATH: credentials.json
          GOOGLE_TOKEN_PATH: token.json
        run: python -m src.main
```

Key notes (do not commit these notes; they're context):
- `timeout-minutes: 5` prevents runaway jobs from consuming free-tier minutes if something hangs
- `cache: pip` makes subsequent runs faster
- Secrets pass via `env:` blocks, not as command-line args, to keep them out of shell history
- The workflow has NO user-specific data — fully reusable by any forker

- [ ] **Step 2: Validate YAML syntax**

Run:
```
.venv/Scripts/python.exe -c "import yaml; yaml.safe_load(open('.github/workflows/sync.yml')); print('ok')"
```

Expected: `ok`. If it raises `yaml.YAMLError`, fix the indentation or quoting before continuing.

- [ ] **Step 3: Commit and push**

```
git add .github/workflows/sync.yml
git commit -m "feat: add GitHub Actions workflow for daily Moodle sync"
git push origin master
```

After pushing, GitHub registers the workflow automatically.

- [ ] **Step 4: Verify the workflow appears in GitHub**

Run:
```
gh workflow list
```

Expected output includes a line containing `Daily Moodle sync` with `active` status.

If the workflow shows as **disabled** (some scheduled workflows on quiet repos get auto-disabled on first push), enable it:

```
gh workflow enable "Daily Moodle sync"
```

---

## Phase C — Secret Setup

### Task C.1: Encode credentials and upload all 5 GitHub Secrets  `[SUBAGENT]`

**Files:**
- Reads: `.env`, `credentials.json`, `token.json` (all gitignored, never committed)
- Effects: 5 secrets created in the GitHub repo `lotantamary-tau/moodle-automation`

This task is fully automatable by a subagent because all required values exist locally on disk and `gh` CLI is authenticated. The subagent reads the `.env` file for plaintext TAU credentials, base64-encodes the two JSON files, and sets all 5 secrets via `gh secret set`.

- [ ] **Step 1: Read TAU credentials from `.env`**

Read `.env` and parse out the three values: `TAU_USERNAME`, `TAU_ID`, `TAU_PASSWORD`. They are on lines like `TAU_USERNAME=somevalue`. Do not log the values — only confirm successful parsing.

- [ ] **Step 2: Set the three plaintext TAU secrets**

For each value, run (substituting `<value>`):

```
echo "<value>" | gh secret set TAU_USERNAME
echo "<value>" | gh secret set TAU_ID
echo "<value>" | gh secret set TAU_PASSWORD
```

Use the Bash tool. Avoid printing secret values in your reports. Each command should produce a brief success message from `gh`.

- [ ] **Step 3: Base64-encode `credentials.json` and set the secret**

Run:
```
base64 -w 0 credentials.json | gh secret set GOOGLE_CREDENTIALS_B64
```

(`base64 -w 0` produces a single-line output, which is the safest format for GitHub Secrets.)

- [ ] **Step 4: Base64-encode `token.json` and set the secret**

Run:
```
base64 -w 0 token.json | gh secret set GOOGLE_TOKEN_B64
```

- [ ] **Step 5: Verify all 5 secrets exist**

Run:
```
gh secret list
```

Expected output (order may vary):
```
GOOGLE_CREDENTIALS_B64    Updated <recent>
GOOGLE_TOKEN_B64          Updated <recent>
TAU_ID                    Updated <recent>
TAU_PASSWORD              Updated <recent>
TAU_USERNAME              Updated <recent>
```

If any are missing, re-run the corresponding step. If `gh secret list` errors, check `gh auth status`.

- [ ] **Step 6: Commit a marker (no file changes, just a milestone)**

```
git commit --allow-empty -m "chore: configure GitHub Secrets for v1.5 workflow"
git push origin master
```

(Empty commit because Phase C produces no committed files — the secrets live in GitHub's secret store, not in the repo.)

---

## Phase D — Live Manual Trigger Test

### Task D.1: Trigger the workflow and stream logs  `[SUBAGENT + USER verify]`

The subagent kicks off the run and watches the logs. Once the run completes, the user does a quick visual verification in Google Tasks.

- [ ] **Step 1 (SUBAGENT): Trigger the workflow**

Run:
```
gh workflow run "Daily Moodle sync"
```

Expected: a confirmation that the workflow was triggered. Note the run ID if printed.

- [ ] **Step 2 (SUBAGENT): Wait for completion and capture logs**

Run:
```
gh run list --workflow=sync.yml --limit=1
```

Get the run ID from the first row. Then:

```
gh run watch <run-id>
```

This blocks until the run completes. Then capture the full log:

```
gh run view <run-id> --log
```

Save the log output to include in the report.

- [ ] **Step 3 (SUBAGENT): Check the run result**

Run:
```
gh run view <run-id> --json conclusion,status
```

Expected: `{"conclusion":"success","status":"completed"}`

If `conclusion` is `failure`, the run broke. Do NOT mark this task complete. Diagnose using the log captured in Step 2. Common failure modes:

| Symptom in log | Likely cause | Fix |
|---|---|---|
| `base64: invalid input` | Secret got mangled | Re-encode without newlines: `base64 -w 0 file.json` |
| `FileNotFoundError: credentials.json` | Decode step succeeded but file didn't write | Add `set -e` to decode step |
| `MoodleException: Authentication failed` | Wrong TAU credentials | Re-set TAU_* secrets |
| `RefreshError` | Google token expired or revoked | Run `python -m src.main` locally to refresh, re-encode `token.json`, re-set `GOOGLE_TOKEN_B64` |
| `ZoneInfoNotFoundError: 'Asia/Jerusalem'` | tzdata not installed | Verify Task A.1 was committed and pushed |

- [ ] **Step 4 (USER): Visually verify Google Tasks**

Open https://tasks.google.com in your browser, signed in with your TAU account. Open the `Uni Assignments` list. Confirm:
- The list is in the same state as before the manual trigger (typically: same 3 tasks, no duplicates, no missing).
- No surprises (no test tasks, no malformed titles).

If the run was green AND Google Tasks looks correct, the manual trigger test passed.

- [ ] **Step 5 (SUBAGENT): Mark Phase D complete with an empty commit**

Only after both Step 3 and Step 4 pass:

```
git commit --allow-empty -m "milestone: v1.5 manual workflow_dispatch run succeeded"
git push origin master
```

---

## Phase E — Confirm Scheduled Run

### Task E.1: Wait for and verify the next scheduled execution  `[USER + SUBAGENT verify]`

This task is mostly waiting. The user waits until ~30 minutes after the next 05:00 UTC. Then a subagent verifies the run happened.

- [ ] **Step 1 (USER): Note the next scheduled time**

Israel time is UTC+2 (winter, IST) or UTC+3 (summer, IDT). The next scheduled run is at the next 05:00 UTC = 07:00 IST or 08:00 IDT. Set a calendar reminder for ~30 minutes after.

- [ ] **Step 2 (SUBAGENT, at least 30 minutes after the scheduled time): List recent runs**

Run:
```
gh run list --workflow=sync.yml --limit=5 --json conclusion,event,createdAt,status
```

Expected: at least one row with `event=schedule`, `status=completed`, `conclusion=success`.

- [ ] **Step 3 (SUBAGENT): If no scheduled run appears, debug**

Common causes:
- **Workflow auto-disabled.** Run `gh workflow list` — if disabled, run `gh workflow enable "Daily Moodle sync"` and wait one more cycle.
- **Cron lag.** GitHub Actions cron is best-effort; runs can be 5-15 minutes late during high-load periods. Wait an additional hour and re-check.
- **Repo went quiet for 60+ days.** Some scheduled workflows pause after no activity. Push any commit (even empty) to wake it up.

- [ ] **Step 4 (SUBAGENT): Verify the timing was reasonable**

Run:
```
gh run list --workflow=sync.yml --limit=1 --json createdAt,event
```

The `createdAt` should be within ~15 minutes of 05:00 UTC. Wider drift is acceptable; report it without failing the task.

- [ ] **Step 5 (SUBAGENT): Mark Phase E complete with an empty commit**

```
git commit --allow-empty -m "milestone: v1.5 first scheduled run succeeded"
git push origin master
```

---

## Phase F — Documentation and Close-Out

### Task F.1: Update CLAUDE.md status and architecture map  `[SUBAGENT]`

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the Status line**

Find this paragraph in `CLAUDE.md`:

```
**Status:** v1 complete (local manual run, idempotent sync, auto-complete on
Moodle submission). v1.5 (GitHub Actions schedule) and friend-onboarding polish
are next. ...
```

Replace the entire `**Status:** ...` block (it spans multiple lines, ending before the blank line that precedes the next `## ` heading) with:

```
**Status:** v1.5 complete. The sync runs unattended every day at 05:00 UTC via
GitHub Actions. Friend onboarding (a future Phase 2) and umbrella restructure
(a future Phase 3) are deferred until needed. v2 may add notifications
(Telegram or GitHub Issues) when new tasks are detected.
```

- [ ] **Step 2: Add the workflow to the Architecture quick reference**

Find the "## Architecture quick reference" heading in `CLAUDE.md`. After the last bullet under that heading (currently `tests/test_dedup.py — 10 unit tests.`), add:

```
- [.github/workflows/sync.yml](.github/workflows/sync.yml) — daily cron at 05:00 UTC; runs `python -m src.main` with secrets injected as env vars
```

- [ ] **Step 3: Commit**

```
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md status and architecture map for v1.5"
```

### Task F.2: Update architectural_patterns.md  `[SUBAGENT]`

**Files:**
- Modify: `.claude/docs/architectural_patterns.md`

- [ ] **Step 1: Add a deployment paragraph**

In `.claude/docs/architectural_patterns.md`, find the paragraph that starts with `**Pure-function dedup:**` (it's in the "## Architectural Patterns" section). After that paragraph (and its closing blank line), insert this new paragraph:

```markdown
**Cron deployment via GitHub Actions:** [.github/workflows/sync.yml](../../.github/workflows/sync.yml)
runs the entire script daily at 05:00 UTC on a hosted Ubuntu runner. The
workflow has no application logic — it's a thin wrapper that decodes
secrets to disk and invokes `python -m src.main`. This means local and CI
behavior are byte-identical: any bug reproduces locally, any local fix
works in CI without modification.

```

- [ ] **Step 2: Commit**

```
git add .claude/docs/architectural_patterns.md
git commit -m "docs: document cron deployment pattern in architectural_patterns.md"
```

### Task F.3: Update the v1.5 design spec status  `[SUBAGENT]`

**Files:**
- Modify: `docs/superpowers/specs/2026-05-04-moodle-tasks-sync-v1.5-design.md`

- [ ] **Step 1: Update the Status line**

In the spec file, find:
```
**Status:** Approved, ready for implementation planning
```

Replace with:
```
**Status:** Implemented and verified. Daily 05:00 UTC scheduled runs confirmed working.
```

- [ ] **Step 2: Commit**

```
git add docs/superpowers/specs/2026-05-04-moodle-tasks-sync-v1.5-design.md
git commit -m "docs: mark v1.5 spec as implemented"
```

### Task F.4: Final verification and v1.5 milestone  `[SUBAGENT]`

- [ ] **Step 1: Run all tests**

Run: `.venv/Scripts/pytest.exe -v`

Expected: 10 passed.

- [ ] **Step 2: Run the script locally one more time**

Run: `.venv/Scripts/python.exe -m src.main`

Expected: clean run, `created=0 completed=0` (assuming nothing has changed in Moodle).

- [ ] **Step 3: Verify recent CI runs are healthy**

Run:
```
gh run list --workflow=sync.yml --limit=5 --json conclusion,event,createdAt
```

Expected: most recent runs (including both the manual trigger from Phase D and the scheduled run from Phase E) have `conclusion=success`.

- [ ] **Step 4: Verify no secrets ever entered git history**

Run:
```
git log --all --diff-filter=A --name-only --pretty=format: | sort -u | grep -E '^\.env$|credentials\.json$|token\.json$|session\.json$' || echo "no secrets in history"
```

Expected: `no secrets in history`. If any secret file appears, escalate immediately — the secrets need rotation and the history needs surgery before this is safe to leave public.

- [ ] **Step 5: Mark v1.5 complete with a final empty commit and push**

```
git commit --allow-empty -m "milestone: v1.5 complete; ready for v2 (notifications) or Phase 2 (friend onboarding)"
git push origin master
```

---

## What v1.5 explicitly does NOT include

(Carried over from the spec; surface as a "future phase candidate" rather than building.)

- Friend onboarding documentation (README polish, fork model, sharing credentials.json)
- Umbrella restructure of `src/`
- Notifications (Telegram, email, GitHub Issues)
- Retry logic
- Dry-run mode
- Updates to existing tasks when Moodle due dates change
- Multi-user support beyond fork-based isolation

---

## Subagent dispatch summary

For convenience when the controller dispatches:

| Task | Type | Notes |
|---|---|---|
| A.1 | SUBAGENT | requirements + lockfile + commit |
| A.2 | SUBAGENT | code + tests + commit |
| B.1 | SUBAGENT | workflow YAML + push + verify visible |
| C.1 | SUBAGENT | reads .env, encodes JSON, sets 5 secrets via gh CLI |
| D.1 | SUBAGENT then USER | subagent kicks off + reads logs; user does final visual check in Google Tasks |
| E.1 | USER then SUBAGENT | user waits 24h; subagent verifies after |
| F.1 | SUBAGENT | CLAUDE.md edits |
| F.2 | SUBAGENT | architectural_patterns.md edits |
| F.3 | SUBAGENT | spec status update |
| F.4 | SUBAGENT | final verification + milestone |

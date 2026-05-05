# Phase 2 — Friend Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> Each task is labeled `[SUBAGENT]`, `[USER]`, or `[USER + SUBAGENT verify]` so the controller knows whether to dispatch or hand off to the user.

**Goal:** Make the repo fork-and-go for a mixed-technical TAU friend (and AI agents helping them). Ship a one-command local bootstrap script + a comprehensive README walkthrough + AI-agent meta-context, so a friend can complete fork-to-first-sync in ≤30 minutes using only the README.

**Architecture:** New `scripts/setup.py` handles the local-environment portion of setup (Google OAuth flow, TAU credential capture, base64 encoding) and prints all 5 GitHub Secrets ready to paste into the GitHub web UI. The README is restructured around a 7-step setup walkthrough with per-step verify commands and Win/Mac code blocks, plus a top-of-file callout briefing AI agents on context.

**Tech Stack:** Python 3.11+, existing dependencies only (`google-auth-oauthlib`, `google-api-python-client`, stdlib `getpass` and `base64`). No new dependencies. No new tests (setup script is interactive; README is docs).

**Spec:** [docs/superpowers/specs/2026-05-05-phase-2-friend-onboarding-design.md](../specs/2026-05-05-phase-2-friend-onboarding-design.md)

---

## File Structure (final state at end of Phase 2)

| Path | Change | Responsibility |
|---|---|---|
| `scripts/setup.py` | **New** | One-command local bootstrap |
| `README.md` | **Major rewrite** | Friend walkthrough + AI agent callout |
| `CLAUDE.md` | Status update | "Phase 2 complete" |
| `.claude/docs/architectural_patterns.md` | Small addition | Document the bootstrap pattern |
| `docs/superpowers/specs/2026-05-05-phase-2-friend-onboarding-design.md` | Status update | "Implemented and verified" |

No tests. No new dependencies. No restructuring of `src/`.

## Working Assumptions Locked In

- **Working directory:** `c:\Users\lotan\UniversityDev\moodleAgent\`
- **Python interpreter:** `.venv/Scripts/python.exe`
- **Pytest binary:** `.venv/Scripts/pytest.exe`
- **gh CLI:** authenticated as `lotantamary-tau` for repo `lotantamary-tau/moodle-automation`
- **Branch:** `master` (push directly per existing repo convention)
- **OS for development:** Windows / PowerShell. Bash also available.
- **Existing `credentials.json` and `token.json`** are present in the project root (used to test setup.py without re-running OAuth)

If any assumption changes before execution starts, the affected tasks must be revised.

---

## Phase A — `scripts/setup.py`

### Task A.1: Scaffold the script  `[SUBAGENT]`

**Files:**
- Create: `scripts/setup.py`

- [ ] **Step 1: Create the `scripts/` directory and the script file**

Use the Write tool to create `scripts/setup.py` with this content:

```python
"""scripts/setup.py — friend bootstrap, run once after fork.

Runs the Google OAuth flow, prompts for TAU credentials, and prints all 5
GitHub Secrets ready to paste into the repo's Settings → Secrets → Actions UI.
"""

import base64
import getpass
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/tasks"]
ROOT = Path(__file__).resolve().parent.parent
CREDS_PATH = ROOT / "credentials.json"
TOKEN_PATH = ROOT / "token.json"


def main() -> None:
    _banner()
    _check_project_root()
    _check_credentials_file()
    _run_oauth_flow()
    tau_username, tau_id, tau_password = _prompt_tau_credentials()
    secrets = _build_secret_payloads(tau_username, tau_id, tau_password)
    _print_paste_block(secrets)


def _banner() -> None:
    print("=" * 68)
    print("  Moodle Tasks Sync — local setup")
    print("=" * 68)
    print()


def _check_project_root() -> None:
    raise NotImplementedError


def _check_credentials_file() -> None:
    raise NotImplementedError


def _run_oauth_flow() -> None:
    raise NotImplementedError


def _prompt_tau_credentials() -> tuple[str, str, str]:
    raise NotImplementedError


def _build_secret_payloads(username: str, id_: str, password: str) -> dict[str, str]:
    raise NotImplementedError


def _print_paste_block(secrets: dict[str, str]) -> None:
    raise NotImplementedError


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("Usage: python scripts/setup.py")
        print("  No arguments. Run from the project root after placing credentials.json.")
        sys.exit(0)
    main()
```

- [ ] **Step 2: Verify the file compiles**

Run: `.venv/Scripts/python.exe -m py_compile scripts/setup.py`
Expected: no output (success).

- [ ] **Step 3: Verify the usage path works**

Run: `.venv/Scripts/python.exe scripts/setup.py --help`
Expected: prints two-line usage and exits 0.

- [ ] **Step 4: Verify main() reaches the first stub**

Run: `.venv/Scripts/python.exe scripts/setup.py`
Expected: banner prints, then `NotImplementedError` traceback originating from `_check_project_root`.

- [ ] **Step 5: Commit**

```
git add scripts/setup.py
git commit -m "feat: scaffold scripts/setup.py for friend bootstrap"
```

---

### Task A.2: Implement pre-condition checks  `[SUBAGENT]`

**Files:**
- Modify: `scripts/setup.py`

- [ ] **Step 1: Replace `_check_project_root` and `_check_credentials_file` stubs**

Use Edit to replace the body of `_check_project_root` (currently `raise NotImplementedError`) with:

```python
def _check_project_root() -> None:
    main_py = ROOT / "src" / "main.py"
    if not main_py.exists():
        print("ERROR: src/main.py not found.")
        print("Run this from the moodle-automation/ directory:")
        print("  python scripts/setup.py")
        sys.exit(1)
```

And replace the body of `_check_credentials_file`:

```python
def _check_credentials_file() -> None:
    if not CREDS_PATH.exists():
        print("ERROR: credentials.json not found in the project root.")
        print("Place your downloaded credentials.json there, then re-run.")
        print(f"Expected path: {CREDS_PATH}")
        sys.exit(1)
```

- [ ] **Step 2: Verify the script now reaches the next stub**

Run: `.venv/Scripts/python.exe scripts/setup.py`
Expected: banner prints, both pre-condition checks pass silently (since the project root and credentials.json both exist in this dev environment), then `NotImplementedError` traceback from `_run_oauth_flow`.

- [ ] **Step 3: Verify the project-root check fires when run from elsewhere**

Run: `cd $env:TEMP; .venv/Scripts/python.exe (Resolve-Path c:/Users/lotan/UniversityDev/moodleAgent/scripts/setup.py)` (PowerShell — adjust if shell differs)

Or in bash: `cd /tmp && python c:/Users/lotan/UniversityDev/moodleAgent/scripts/setup.py`

Expected: banner prints, then "ERROR: src/main.py not found..." and exit code 1.

(After this verification, return cwd to the project root before continuing: `cd c:/Users/lotan/UniversityDev/moodleAgent`)

- [ ] **Step 4: Commit**

```
git add scripts/setup.py
git commit -m "feat: setup.py pre-condition checks (project root, credentials.json)"
```

---

### Task A.3: Implement OAuth flow with token reuse  `[SUBAGENT]`

**Files:**
- Modify: `scripts/setup.py`

- [ ] **Step 1: Replace `_run_oauth_flow` stub**

Use Edit to replace the body of `_run_oauth_flow` with:

```python
def _run_oauth_flow() -> None:
    """Run the Google OAuth flow. Reuses existing token.json if valid; otherwise
    opens the browser for sign-in and writes a fresh token.json."""
    if TOKEN_PATH.exists():
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
            if creds.valid:
                print("✓ Reusing valid token.json (no browser needed)")
                return
            if creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
                TOKEN_PATH.write_text(creds.to_json())
                print("✓ Refreshed existing token.json")
                return
        except Exception:
            pass  # fall through to fresh OAuth flow

    print("Opening browser for Google OAuth...")
    print("Sign in with your TAU account when prompted.")
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
    try:
        creds = flow.run_local_server(port=0)
    except Exception as e:
        print(f"ERROR: OAuth was canceled or failed: {e}")
        print("Re-run the script when ready.")
        sys.exit(1)
    TOKEN_PATH.write_text(creds.to_json())
    print("✓ Saved token.json")
```

- [ ] **Step 2: Verify the script now reaches the next stub**

Run: `.venv/Scripts/python.exe scripts/setup.py`
Expected: banner prints, pre-condition checks pass, prints `✓ Reusing valid token.json (no browser needed)` (because the dev env already has a valid token.json), then `NotImplementedError` traceback from `_prompt_tau_credentials`.

- [ ] **Step 3: Commit**

```
git add scripts/setup.py
git commit -m "feat: setup.py OAuth flow with token reuse"
```

---

### Task A.4: Implement TAU credentials prompt and secret payload builder  `[SUBAGENT]`

**Files:**
- Modify: `scripts/setup.py`

- [ ] **Step 1: Replace `_prompt_tau_credentials` stub**

Use Edit to replace the body of `_prompt_tau_credentials` with:

```python
def _prompt_tau_credentials() -> tuple[str, str, str]:
    print()
    print("Enter your TAU credentials (used to sign in to Moodle):")
    while True:
        username = input("  TAU username (e.g., lotantamary): ").strip()
        if username:
            break
        print("  (cannot be empty)")
    while True:
        tau_id = input("  TAU ID (9 digits): ").strip()
        if tau_id:
            break
        print("  (cannot be empty)")
    while True:
        password = getpass.getpass("  TAU password (input hidden): ").strip()
        if password:
            break
        print("  (cannot be empty)")
    return username, tau_id, password
```

- [ ] **Step 2: Replace `_build_secret_payloads` stub**

Use Edit to replace the body of `_build_secret_payloads` with:

```python
def _build_secret_payloads(username: str, id_: str, password: str) -> dict[str, str]:
    creds_b64 = base64.b64encode(CREDS_PATH.read_bytes()).decode("ascii")
    token_b64 = base64.b64encode(TOKEN_PATH.read_bytes()).decode("ascii")
    return {
        "TAU_USERNAME": username,
        "TAU_ID": id_,
        "TAU_PASSWORD": password,
        "GOOGLE_CREDENTIALS_B64": creds_b64,
        "GOOGLE_TOKEN_B64": token_b64,
    }
```

- [ ] **Step 3: Verify the script now reaches the next stub**

Run the script with piped input so the prompts auto-fill (Windows PowerShell):

```
"test_user`ntest_id`ntest_pass" | .venv/Scripts/python.exe scripts/setup.py
```

Or bash:

```
printf "test_user\ntest_id\ntest_pass\n" | .venv/Scripts/python.exe scripts/setup.py
```

Expected: banner prints, pre-condition checks pass, OAuth reuses existing token, prompt prints, then `NotImplementedError` traceback from `_print_paste_block`.

NOTE: `getpass.getpass()` may not read from piped stdin on Windows — it sometimes falls back to reading from the console (TTY). If the script appears to hang waiting for password input, that's the cause. In that case, type the password manually (e.g., `test_pass`) and press Enter to proceed. The verification still works.

- [ ] **Step 4: Commit**

```
git add scripts/setup.py
git commit -m "feat: setup.py TAU prompts and base64 secret payloads"
```

---

### Task A.5: Implement the paste-block printer with repo URL detection  `[SUBAGENT]`

**Files:**
- Modify: `scripts/setup.py`

- [ ] **Step 1: Add `_detect_repo_url` helper above `_print_paste_block`**

Use Edit to replace the entire `_print_paste_block` stub block with this two-function block:

```python
def _detect_repo_url() -> str:
    """Detect the GitHub repo URL from `git remote get-url origin`. Falls back
    to a placeholder if git or remote is missing."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True, cwd=str(ROOT),
        )
        url = result.stdout.strip()
        # Normalize SSH form (git@github.com:user/repo.git) to HTTPS
        if url.startswith("git@github.com:"):
            url = "https://github.com/" + url[len("git@github.com:"):]
        if url.endswith(".git"):
            url = url[:-4]
        return url
    except Exception:
        return "https://github.com/<your-username>/moodle-automation"


def _print_paste_block(secrets: dict[str, str]) -> None:
    repo_url = _detect_repo_url()
    sep = "─" * 68
    print()
    print("╔" + "═" * 66 + "╗")
    print("║  Done. Now add these 5 secrets to GitHub." + " " * 24 + "║")
    print("╚" + "═" * 66 + "╝")
    print()
    print("Open this URL in your browser:")
    print(f"    {repo_url}/settings/secrets/actions")
    print()
    print('Click "New repository secret" five times — once per pair below.')
    print("Copy the NAME and VALUE exactly. Don't add quotes around the value.")
    print()
    items = list(secrets.items())
    for i, (name, value) in enumerate(items, 1):
        print(sep)
        print(f"Secret {i} of {len(items)}")
        print(f"NAME:   {name}")
        print(f"VALUE:  {value}")
    print(sep)
    print()
    print('After adding all 5, go to the "Actions" tab → "Daily Moodle sync" →')
    print('"Run workflow" to trigger your first sync.')
```

- [ ] **Step 2: Verify the script now runs end-to-end without errors**

Run with piped input (PowerShell):
```
"test_user`ntest_id`ntest_pass" | .venv/Scripts/python.exe scripts/setup.py
```

Expected:
- Banner prints
- "✓ Reusing valid token.json"
- TAU prompts (auto-filled from stdin)
- Paste block prints with all 5 secrets
- Repo URL is `https://github.com/lotantamary-tau/moodle-automation` (detected from git remote)
- `GOOGLE_CREDENTIALS_B64` and `GOOGLE_TOKEN_B64` values are long base64 strings on a single line each
- Exit code 0

- [ ] **Step 3: Verify the base64 strings round-trip**

Save the printed `GOOGLE_CREDENTIALS_B64` value to a variable, then verify:

```
.venv/Scripts/python.exe -c "import base64; v = base64.b64decode('<paste-the-b64-string-here>'); import json; d = json.loads(v); print(list(d.keys()))"
```

Expected: prints `['installed']` (or similar — the top-level key of credentials.json).

- [ ] **Step 4: Commit**

```
git add scripts/setup.py
git commit -m "feat: setup.py paste-block printer with repo URL detection"
```

---

### Task A.6: Smoke-test the full script and push  `[SUBAGENT]`

**Files:**
- (No file changes; verification only)

- [ ] **Step 1: Run `python -m py_compile` to confirm no syntax issues**

Run: `.venv/Scripts/python.exe -m py_compile scripts/setup.py`
Expected: no output.

- [ ] **Step 2: Run the existing test suite to confirm no regression**

Run: `.venv/Scripts/pytest.exe -v`
Expected: 12 passed.

- [ ] **Step 3: Run the script one more time end-to-end**

Run with piped input (PowerShell):
```
"test_user`ntest_id`ntest_pass" | .venv/Scripts/python.exe scripts/setup.py
```

Expected: paste block prints with all 5 secrets cleanly. No exceptions. Exit 0.

- [ ] **Step 4: Push all Phase A commits to GitHub**

```
git push origin master
```

Expected: 5 commits pushed (A.1 through A.5).

---

## Phase B — README rewrite

The current README is at the project root. Phase B rewrites it section-by-section. The existing v2 "Notifications (optional)" section is preserved largely as-is (only verifying placement in the new structure). All other sections are replaced or restructured.

### Task B.1: Top-of-file content (header, AI callout, What it does, Prerequisites)  `[SUBAGENT]`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read the current README.md to see existing content**

Use the Read tool on `README.md` to see what's there currently.

- [ ] **Step 2: Replace lines from start through (and including) the "Requirements" section with the new top content**

Find the line `# moodle-tasks-sync` at the top, and the next major section heading after Requirements (it's `## Setup`). Replace everything from `# moodle-tasks-sync` up to (but not including) `## Setup` with this new content:

```markdown
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

```

(NOTE: leave the `## Notifications (optional)` section entirely untouched in this task — that comes later in B.4 placement check.)

- [ ] **Step 3: Verify the markdown renders correctly**

Run: `.venv/Scripts/python.exe -c "import pathlib; t = pathlib.Path('README.md').read_text(encoding='utf-8'); print(t.count('# moodle-tasks-sync')); print(t.count('## What it does')); print(t.count('## Prerequisites'))"`

Expected: prints `1`, `1`, `1` — each heading appears exactly once.

- [ ] **Step 4: Commit**

```
git add README.md
git commit -m "docs: rewrite README header, AI agent callout, prerequisites"
```

---

### Task B.2: Rewrite the entire Setup section (all 7 steps)  `[SUBAGENT]`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read the current README.md `## Setup` section**

Use Read on `README.md` to find the `## Setup` heading and see its current content.

- [ ] **Step 2: Replace the entire current `## Setup` section through the end of step 4 with the new content**

The current Setup section looks roughly like:

```markdown
## Setup

1. Clone this repo
2. Create a virtualenv and install dependencies:
...
```

Replace the entire `## Setup` section (from the `## Setup` heading down through the end of the OLD Setup section, which is the line above `## Tests`) with the new content below. The new content includes the FULL 7-step walkthrough (steps 1-7); we'll preserve `## Tests` and everything after it untouched until task B.3.

NOTE: this single Edit replaces the full Setup section with all 7 steps in one go (rather than splitting B.2 and B.3 across the same section). The other tasks in Phase B insert separate sections after Setup.

Write this Setup section content as the replacement:

````markdown
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

````

- [ ] **Step 3: Verify the section was inserted correctly**

Run: `.venv/Scripts/python.exe -c "import pathlib; t = pathlib.Path('README.md').read_text(encoding='utf-8'); print(t.count('### Step 1:')); print(t.count('### Step 7:')); print(t.count('## Setup'))"`

Expected: prints `1`, `1`, `1`.

- [ ] **Step 4: Commit**

```
git add README.md
git commit -m "docs: rewrite README Setup section as 7-step walkthrough"
```

---

### Task B.3: Daily life + Troubleshooting sections  `[SUBAGENT]`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read the current README.md to find where the Notifications section ends**

Use Read on `README.md`. The current structure now is:
1. Header / What it does / Prerequisites (from B.1)
2. Setup (from B.2)
3. ## Tests (still leftover from old README — replace this in this task)
4. ## Notifications (optional) — from v2, untouched
5. ## What's not done yet — old, replace this in this task
6. ## License / status — keep

You need to:
- **Remove** the old `## Tests` section (testing instructions moved into Step 3 of Setup as the verify command — the dedicated Tests section is redundant)
- **Replace** the old `## What's not done yet` section with new "Daily life", "Troubleshooting", and "What this project is not" sections

The existing `## Notifications (optional)` section stays where it is (between Setup and the new sections).

- [ ] **Step 2: Remove the old `## Tests` section**

Find the lines starting with `## Tests` and ending with the line before `## What's not done yet` (or `## Notifications (optional)` — whichever comes first in the current file). Delete those lines entirely.

- [ ] **Step 3: Replace `## What's not done yet` block with the three new sections**

Find the `## What's not done yet` heading and replace EVERYTHING from that heading down to (but not including) `## License / status` with this content:

```markdown
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

### Step 3: `pytest -v` fails or `pip install` errors out

- **SSL error during pip install** — likely a corporate network proxy. Try a
  different network (mobile hotspot).
- **Permission error / package conflicts** — make sure you activated the
  virtualenv before running pip (your prompt should start with `(.venv)`).
- **`pytest` command not found** — re-activate the venv. On Windows:
  `.venv\Scripts\Activate.ps1`. On macOS/Linux: `source .venv/bin/activate`.

### Step 4: "Internal" is greyed out in Google Cloud OAuth consent

Your account isn't part of Google Workspace. The project owner's setup relies
on TAU's Workspace tenant — if your TAU account doesn't sign in via TAU's
Google login page, you can't use Internal mode, and the workflow's unattended
runs won't work (External mode tokens expire every 7 days).

Action: confirm with TAU IT, or message the project owner.

### Step 5: Setup script can't open browser for OAuth

You're probably running on a headless server or over SSH. Run the script on a
machine with a real browser (your laptop), then copy the resulting
`token.json` to wherever you're deploying.

### Step 5: Setup script says "credentials.json not found"

The downloaded JSON didn't end up in the project root. Check:
- The file is named exactly `credentials.json` (not `client_secret_xxx.json`
  — rename it if needed)
- It's in the same folder as `README.md`, not in a subfolder

### Step 5 (macOS): `python scripts/setup.py` fails with import error

Mac defaults `python` to Python 2.7 in some setups. Use `python3` explicitly:
```bash
python3 scripts/setup.py
```

### Step 7: Workflow fails on first run with "TAU auth failed" / login error

Your TAU password may have a typo. Re-run the setup script (`python
scripts/setup.py`) and retype the password carefully. Re-update the
`TAU_PASSWORD` secret with the new value (paste the password value again from
the new run).

### Step 7: Workflow fails with "Tasks API has not been used"

You forgot Step 4d (enabling the Tasks API). Go back to Google Cloud Console
→ search "Tasks API" → click "Enable".

### Step 7: ntfy notification never arrives

- Confirm the topic name in your `NTFY_TOPIC` secret matches the topic you
  subscribed to in the ntfy phone app exactly (no typos, same case)
- Re-trigger the workflow with `gh workflow run "Daily Moodle sync"` (or via
  the Actions tab)

### Step 7: GitHub Issues notification never arrives

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

```

- [ ] **Step 4: Verify the markdown structure**

Run: `.venv/Scripts/python.exe -c "import pathlib; t = pathlib.Path('README.md').read_text(encoding='utf-8'); print('Daily life:', t.count('## Daily life')); print('Troubleshooting:', t.count('## Troubleshooting')); print('What this project is not:', t.count('## What this project is not')); print('Tests heading:', t.count('## Tests')); print('License heading:', t.count('## License'))"`

Expected: prints `1, 1, 1, 0, 1` — Daily life, Troubleshooting, and What this project is not appear exactly once each; the old `## Tests` heading is gone; License is still present.

- [ ] **Step 5: Commit**

```
git add README.md
git commit -m "docs: add Daily life, Troubleshooting, and 'What this is not' sections"
```

---

### Task B.4: Final README pass and push  `[SUBAGENT]`

**Files:**
- Modify (verification only): `README.md`

- [ ] **Step 1: Read the full README.md end-to-end**

Use Read with no offset/limit on `README.md`. Verify the section order is:

1. Title `# moodle-tasks-sync`
2. 1-line tagline paragraph
3. AI agents callout block
4. `## What it does`
5. `## Prerequisites`
6. `## Setup` (with sub-steps 1-7)
7. `## Notifications (optional)` (preserved from v2)
8. `## Daily life (after setup)`
9. `## Troubleshooting`
10. `## What this project is not`
11. `## License / status`

If any section is out of order, use Edit to swap them. (Most likely they're already in the right order — Read just to verify.)

- [ ] **Step 2: Sanity-check overall length**

Run: `.venv/Scripts/python.exe -c "import pathlib; t = pathlib.Path('README.md').read_text(encoding='utf-8'); lines = t.count(chr(10)); print(f'lines: {lines}')"`

Expected: somewhere between 200 and 500 lines. (If <200, content is missing. If >500, the file has bloated and may need restructuring — flag it as a concern but don't restructure unilaterally.)

- [ ] **Step 3: Push everything from Phase B**

```
git push origin master
```

Expected: 3 commits pushed (B.1, B.2, B.3).

- [ ] **Step 4: Verify the README renders cleanly on GitHub**

Open https://github.com/lotantamary-tau/moodle-automation in a browser and visually scan the rendered README. Confirm:
- AI callout shows as a blockquote (left bar)
- Code blocks render with syntax highlighting (powershell + bash both)
- Section headings stack properly
- No obvious markdown syntax errors

(This is a manual visual check; report any issues to the controller.)

---

## Phase C — Self-validation

### Task C.1: USER walks through the README from scratch  `[USER]`

This is the heart of Phase 2 quality. The project owner pretends to be a friend who has never seen the repo, and follows the README from top to bottom. The validation should ideally happen on a *different* machine from the development one, to catch path / environment assumptions that snuck in.

- [ ] **Step 1 (USER): Set up a clean test environment**

Pick a fresh directory outside the dev project — e.g. `C:\test-fresh\` (Windows) or `/tmp/test-fresh/` (macOS). Open a new terminal there. (You don't need to actually fork the repo — clone it as if you were a friend who has forked.)

```
cd C:\
mkdir test-fresh
cd test-fresh
git clone https://github.com/lotantamary-tau/moodle-automation.git
cd moodle-automation
```

- [ ] **Step 2 (USER): Open README.md in your editor (or read it on GitHub)**

Read it from the top. Pretend you don't already know the project.

- [ ] **Step 3 (USER): Try to follow Setup Steps 1-7 literally**

Note (don't fix yet — just write down):
- Steps where you needed knowledge not in the docs
- Commands that don't work as written
- Verify commands that gave unexpected output
- Spots where you weren't sure if something succeeded
- Anywhere the AI agent callout's instructions don't match the actual flow

You can stop after any failed step — you don't need to actually push secrets or run a real sync (you've already done that earlier). The goal is to surface gaps in docs.

- [ ] **Step 4 (USER): Report findings to the controller**

Write up the gaps in plain English. The controller will dispatch C.2 to fix them.

If there are no gaps, tell the controller "no gaps found" and Phase D begins.

---

### Task C.2: SUBAGENT fixes any reported documentation gaps  `[SUBAGENT, conditional]`

**Files:** depend on what gaps were reported. Almost always `README.md`; sometimes `scripts/setup.py`.

- [ ] **Step 1: Receive the gap list from the user via the controller**

The controller passes the list of gaps as part of dispatching this subagent.

- [ ] **Step 2: Apply targeted fixes**

For each gap:
- If it's a missing instruction → add the instruction in the relevant Setup step or Troubleshooting entry
- If it's an inaccurate command → correct it (test the corrected command from a fresh clone)
- If it's an unclear verify step → rewrite to be more explicit

- [ ] **Step 3: Commit each fix as its own commit**

```
git add README.md
git commit -m "docs: fix <specific gap> reported during self-validation"
```

(Multiple commits is fine and preferred — easier to revert one if a fix overcorrects.)

- [ ] **Step 4: Push and ask the user to re-validate**

```
git push origin master
```

If the user re-validates and finds new gaps, dispatch C.2 again. Iterate until the user reports "no gaps found".

---

## Phase D — Close-out

### Task D.1: Update CLAUDE.md  `[SUBAGENT]`

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the Status paragraph**

Find this paragraph in `CLAUDE.md`:

```
**Status:** v2 complete. The sync runs unattended every day at 04:37 UTC via
GitHub Actions and notifies the user via any configured channels (GitHub
Issues, ntfy.sh, Telegram, Discord). Friend onboarding (a future Phase 2)
and umbrella restructure (a future Phase 3) are deferred until needed.
```

Replace with:

```
**Status:** Phase 2 complete. The sync runs unattended every day at 04:37 UTC
via GitHub Actions; notifies the user via any configured channels (GitHub
Issues, ntfy.sh, Telegram, Discord); and is forkable by friends via a one-
command bootstrap script (`scripts/setup.py`) and a comprehensive README
walkthrough. Umbrella restructure (a future Phase 3) is deferred until a
second automation actually exists.
```

- [ ] **Step 2: Add `scripts/setup.py` to the Architecture quick reference**

Find the line:
```
- [src/notifier.py](src/notifier.py) — optional notifications across 4
```
(somewhere in the `## Architecture quick reference` section)

After the existing `tests/test_notifier.py` line, add:

```
- [scripts/setup.py](scripts/setup.py) — friend bootstrap script, run once
  after fork; runs OAuth flow, prompts for TAU credentials, prints all 5
  GitHub Secrets ready to paste
```

- [ ] **Step 3: Commit**

```
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md status and architecture map for Phase 2"
```

---

### Task D.2: Update architectural_patterns.md  `[SUBAGENT]`

**Files:**
- Modify: `.claude/docs/architectural_patterns.md`

- [ ] **Step 1: Add a bootstrap-script paragraph**

Find the `## Architectural Patterns` section. After the existing **Opt-in notifications** paragraph (which mentions `_try()` and tests/test_notifier.py), add:

```markdown
**One-command friend bootstrap:** [scripts/setup.py](../../scripts/setup.py)
collapses the local-environment portion of fork-based setup into a single
command. It runs the Google OAuth flow (with token.json reuse if valid),
prompts for TAU credentials with masked password input, base64-encodes the
two JSON files, and prints all 5 GitHub Secrets in a paste-ready block.
Deliberately does NOT call `gh secret set` — friends paste into the GitHub
web UI to keep the script's prerequisites minimal (no gh CLI required, no
gh auth setup). Per-fork repo URL detection via `git remote get-url origin`
means friends never have to type their username.

```

- [ ] **Step 2: Commit**

```
git add .claude/docs/architectural_patterns.md
git commit -m "docs: document one-command bootstrap pattern"
```

---

### Task D.3: Update Phase 2 spec status  `[SUBAGENT]`

**Files:**
- Modify: `docs/superpowers/specs/2026-05-05-phase-2-friend-onboarding-design.md`

- [ ] **Step 1: Update the Status line**

Find:
```
**Status:** Approved, ready for implementation planning
```

Replace with:
```
**Status:** Implemented and verified.
```

- [ ] **Step 2: Commit**

```
git add docs/superpowers/specs/2026-05-05-phase-2-friend-onboarding-design.md
git commit -m "docs: mark Phase 2 spec as implemented"
```

---

### Task D.4: Final verification and Phase 2 milestone  `[SUBAGENT]`

- [ ] **Step 1: Run all tests one more time**

Run: `.venv/Scripts/pytest.exe -v`
Expected: 12 passed.

- [ ] **Step 2: Run the script one more time end-to-end**

Run with piped input (PowerShell):
```
"test_user`ntest_id`ntest_pass" | .venv/Scripts/python.exe scripts/setup.py
```

Expected: paste block prints with all 5 secrets cleanly. Exit 0.

- [ ] **Step 3: Run the local sync to confirm no regression**

Run: `.venv/Scripts/python.exe -m src.main`
Expected: clean run, no errors, exit 0.

- [ ] **Step 4: Verify recent CI runs are healthy**

Run:
```
gh run list --workflow=sync.yml --limit=5 --json conclusion,event,createdAt --repo lotantamary-tau/moodle-automation
```

Expected: most recent runs have `conclusion=success`.

- [ ] **Step 5: Verify no secrets ever entered git history**

Run:
```
git log --all --diff-filter=A --name-only --pretty=format: | sort -u | grep -E '^\.env$|credentials\.json$|token\.json$|session\.json$' || echo "no secrets in history"
```

Expected: `no secrets in history`.

- [ ] **Step 6: Mark Phase 2 complete with a milestone commit and push**

```
git commit --allow-empty -m "milestone: Phase 2 complete; ready for friend onboarding"
git push origin master
```

---

## What Phase 2 explicitly does NOT include

(From the spec, surfaced here for the implementer to avoid scope creep.)

- ❌ No `gh secret set` automation in `scripts/setup.py`
- ❌ No notification channel wizard in `scripts/setup.py`
- ❌ No screenshots in the README — text labels only
- ❌ No friend-specific support documentation (e.g., a per-friend troubleshooting log)
- ❌ No multi-language docs — English only
- ❌ No umbrella restructure of `src/` (= future Phase 3)
- ❌ No real-friend test in this plan — that's an optional out-of-band activity after Phase D

---

## Subagent dispatch summary

| Task | Type | Notes |
|---|---|---|
| A.1 | SUBAGENT | Scaffold setup.py with stubs |
| A.2 | SUBAGENT | Pre-condition checks |
| A.3 | SUBAGENT | OAuth flow with token reuse |
| A.4 | SUBAGENT | TAU prompts + base64 builder |
| A.5 | SUBAGENT | Paste block + repo URL detection |
| A.6 | SUBAGENT | Smoke test + push |
| B.1 | SUBAGENT | README header + AI callout + What it does + Prerequisites |
| B.2 | SUBAGENT | README Setup section (7 steps) |
| B.3 | SUBAGENT | README Daily life + Troubleshooting + What this is not |
| B.4 | SUBAGENT | README final pass + push |
| C.1 | USER | Self-validation walkthrough |
| C.2 | SUBAGENT (conditional) | Fix gaps from C.1 |
| D.1 | SUBAGENT | Update CLAUDE.md |
| D.2 | SUBAGENT | Update architectural_patterns.md |
| D.3 | SUBAGENT | Update spec status |
| D.4 | SUBAGENT | Final verification + milestone |

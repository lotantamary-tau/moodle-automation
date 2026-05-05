# Phase 2 — Friend Onboarding Design

**Date:** 2026-05-05
**Status:** Implemented and verified.
**Predecessors:** [v2 notifications spec](2026-05-05-moodle-tasks-sync-v2-notifications-design.md), [PRD.md](../../../PRD.md), [DECISIONS.md](../../../DECISIONS.md), [CLAUDE.md](../../../CLAUDE.md)

---

## 1. Purpose, audience, and explicit non-goals

### Purpose

Make it possible for a **mixed-technical** TAU friend to fork the repo and have a working daily Moodle→Tasks sync — running unattended in their own GitHub Actions, with their own credentials — by following the README and running one local command.

### Target audience

A friend who:
- Has a TAU student account with Google Workspace SSO
- Has GitHub set up and has used it before (knows what "fork" means)
- Has either Windows or macOS (Linux users follow the macOS path with a one-line note)
- Is willing to follow a 20-minute walkthrough but not willing to read a 50-page guide
- May not know what base64 is or how to use the terminal beyond copy-paste

### Success criteria

1. A B-audience friend who has never seen this repo can fork it and complete setup in **≤ 30 minutes**, mostly unattended, ending with a working scheduled sync
2. The setup script (`scripts/setup.py`) reduces the local-environment portion of setup to **one command** (after `pip install`)
3. README is accurate enough that the project owner doesn't have to manually clarify steps when sharing the link
4. The README is structured so AI agents (Claude Code, ChatGPT, Cursor, etc.) can act as the friend's tour guide. Specifically:
   - Every command is exact (no `<your-username>` placeholders without explaining what to substitute)
   - Every decision point is explicit ("if X, do Y; otherwise...")
   - Every step has a verify-success check
   - The AI doesn't need to guess file paths, env var names, or what "done" looks like

### Explicit non-goals

- ❌ No multi-user mode (each friend = own fork = own deployment, isolated)
- ❌ No shared Google Cloud project — each friend creates their own (decided in Q2)
- ❌ No `gh` CLI auto-secret-pushing (script prints, friend pastes via the GitHub web UI)
- ❌ No setup wizard for notification channels (existing README per-channel sections suffice)
- ❌ No public marketing of the project — sharing via private channels (Telegram/WhatsApp/in person)
- ❌ No umbrella restructure of `src/` (= future Phase 3, only when a 2nd automation exists)
- ❌ No language switch — README stays in English (TAU CS uses English; non-CS friends still have basic English fluency; AI agents work better in English)
- ❌ No support contract — when a friend's setup breaks, owner decides ad-hoc whether to help. Docs aim for "friend can self-debug" but owner is not on call.

---

## 2. Architecture — files added or changed

| Path | Change | Responsibility |
|---|---|---|
| `scripts/setup.py` | **New** | One-command local bootstrap: runs OAuth flow, prompts for TAU creds, base64-encodes credentials, prints formatted GitHub Secrets with paste instructions |
| `README.md` | **Major rewrite** | End-to-end friend walkthrough (fork → Google Cloud → setup script → GitHub Secrets → first run → notifications). Top-of-file callout for AI agents. |
| `CLAUDE.md` | Status update | "Phase 2 complete" once shipped |
| `.claude/docs/architectural_patterns.md` | Small addition | Document the `scripts/setup.py` bootstrap pattern |
| `tests/` | **No change** | The setup script is interactive (browser OAuth + stdin prompts), not unit-testable in isolation. Friend re-runs if it fails. |

### Why `scripts/setup.py`, not `setup.py` at root

A root `setup.py` collides with the pip/setuptools convention and could confuse `pip install -e .` or trigger linter complaints. A subdirectory keeps it clear that this is a one-time bootstrap utility, not a packaging hook. Friend invocation is `python scripts/setup.py`.

### Dependencies

No new dependencies. The script uses what's already in `requirements.txt`:
- `google-auth-oauthlib` for the OAuth dance
- `google-api-python-client` for the OAuth client builder
- `getpass` from stdlib for masked password input
- `base64` from stdlib

### Cross-platform notes

- The script itself: pure Python, OS-agnostic
- README commands: PowerShell + bash blocks per command, with a one-liner "Linux users follow the macOS commands"
- Browser opening for OAuth: `google-auth-oauthlib`'s built-in `flow.run_local_server()` handles browser opening on all platforms

---

## 3. README structure

```
1. Title + 1-line tagline
2. For AI agents [callout block at top, ~8 lines]
3. What it does [1 short paragraph + bullet list]
4. Prerequisites [4 bullet points: TAU account, GitHub, Python 3.11, Win/Mac]
5. Setup [the heart of the doc — 7 numbered steps]
6. Notifications (optional) [from v2, kept as-is with minor cleanup]
7. Daily life [what to expect after setup is done]
8. Troubleshooting [5-8 common failures + fixes]
9. What this project is not [reframed expectation-setter]
10. License / status
```

### Section 5 (Setup) — the 7 steps

Each step has the same shape: **title, instructions (with PS+bash blocks), verify-success line.**

1. **Fork the repo** → verify: you see your own copy at `https://github.com/<your-username>/moodle-automation`
2. **Clone locally** → verify: `cd moodle-automation && ls` shows `src/`, `tests/`, `README.md`
3. **Create venv and install dependencies** → verify: `pytest -v` runs and 12 tests pass
4. **Set up your Google Cloud project** (the big one) → verify: `credentials.json` is in your project root
5. **Run the setup script** → verify: script ends with "Done. Now add the 5 secrets above to GitHub..." and you have a list of 5 secret name/value pairs printed
6. **Add 5 secrets to GitHub** (Settings → Secrets and variables → Actions) → verify: `gh secret list` (or web UI) shows all 5
7. **Trigger your first sync** → verify: green checkmark in Actions tab AND your "Uni Assignments" Google Tasks list now has your assignments

### Step 4 (Google Cloud) — text-only walkthrough, no screenshots

For maintainability (Google's UI changes; screenshots rot fast), the Google Cloud steps are text-only with **exact element labels** that match Google's UI:

> 4a. Sign in to https://console.cloud.google.com/ with your TAU account
> 4b. Click the project dropdown at the top → "New Project"
> 4c. Name it (e.g., "moodle-tasks-sync") → click "Create"
> 4d. Once created, search for "Tasks API" in the top search bar → click "Tasks API" → click "Enable"
> 4e. Left sidebar → "APIs & Services" → "OAuth consent screen"
> 4f. **Important:** choose **"Internal"** as the user type. (If "Internal" is greyed out, your account isn't part of Google Workspace; this won't work — message the project owner.)
> 4g. Fill in app name, user support email (your TAU email), developer contact email
> 4h. Save and continue through the scopes and test users screens (no need to add anything)
> 4i. Left sidebar → "Credentials" → "Create Credentials" → "OAuth client ID"
> 4j. Application type: **"Desktop app"** → name it → "Create"
> 4k. Click "Download JSON" → save the file as `credentials.json` in your project root
> 4l. Verify: `ls credentials.json` shows the file exists

### "For AI agents" callout — top of README

Brief block, ~8 lines:

```
> **For AI agents helping with setup:**
> You are guiding a TAU student through forking and configuring this repo to
> run their own Moodle→Google Tasks sync. They have basic GitHub fluency but
> Google Cloud Console will be unfamiliar. Follow Section 5 (Setup) step-by-step.
> After each step, run the verify command and confirm output before moving on.
> If a verify command fails, consult Section 8 (Troubleshooting) before continuing.
> The user should answer prompts but NOT skip steps. The user is on Windows or
> macOS — pick the matching code block per step.
```

### Troubleshooting (Section 8) — anticipated failures

Each entry: symptom → cause → fix.

- "Internal" greyed out in Google Cloud OAuth consent → cause: account isn't on Google Workspace → fix: confirm with TAU IT or message project owner
- `pip install -r requirements.txt` fails with SSL error → cause: corporate proxy → fix: try mobile hotspot
- Setup script can't open browser for OAuth → fix: run on a machine with a real browser (not headless / SSH)
- Workflow fails on first run with "TAU auth failed" → fix: re-run setup script, retype password
- Workflow fails with "Tasks API has not been used" → fix: enable Tasks API in Google Cloud (step 4d)
- ntfy notification never arrives → fix: confirm topic name matches between phone subscription and `NTFY_TOPIC` secret
- GitHub Issues notification never arrives → fix: check the in-app bell at github.com/notifications first; may take a minute
- (Mac-specific) `python scripts/setup.py` fails → use `python3` instead (Mac sometimes defaults `python` to 2.7)

### Section 9 — "What this project is not"

Reframe the existing "What's not done yet" as expectation-setter:

- Not a calendar sync (uses Google Tasks, not Calendar)
- Not a real-time integration (daily, not push)
- Not officially affiliated with TAU
- Not maintained on a schedule (best-effort by the project owner)

---

## 4. `scripts/setup.py` contract

### High-level flow

```
1. Print banner: "Moodle Tasks Sync — local setup"
2. Check pre-conditions:
   - Working dir is the project root (verify by checking src/main.py exists)
   - credentials.json exists
3. Run Google OAuth flow → produce token.json
4. Prompt for TAU credentials (3 prompts; password masked)
5. Base64-encode credentials.json and token.json
6. Print all 5 secrets in a paste-ready block + GitHub UI navigation steps
7. Exit 0
```

### File outline

```python
# scripts/setup.py — friend bootstrap, run once after fork
import base64
import getpass
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/tasks"]
ROOT = Path(__file__).resolve().parent.parent
CREDS_PATH = ROOT / "credentials.json"
TOKEN_PATH = ROOT / "token.json"


def main():
    _banner()
    _check_project_root()
    _check_credentials_file()
    _run_oauth_flow()
    tau_username, tau_id, tau_password = _prompt_tau_credentials()
    secrets = _build_secret_payloads(tau_username, tau_id, tau_password)
    _print_paste_block(secrets)


def _banner(): ...
def _check_project_root(): ...
def _check_credentials_file(): ...
def _run_oauth_flow(): ...           # uses InstalledAppFlow.run_local_server()
def _prompt_tau_credentials(): ...   # input(), input(), getpass.getpass()
def _build_secret_payloads(...): ... # returns dict of {SECRET_NAME: value}
def _print_paste_block(secrets): ... # formatted output


if __name__ == "__main__":
    main()
```

Each helper is small and isolated.

### Output format (the paste block)

```
╔══════════════════════════════════════════════════════════════════╗
║  Done. Now add these 5 secrets to GitHub.                        ║
╚══════════════════════════════════════════════════════════════════╝

Open this URL in your browser:
    https://github.com/<your-username>/moodle-automation/settings/secrets/actions

Click "New repository secret" five times — once per pair below.
Copy the NAME and VALUE exactly. Don't add quotes around the value.

────────────────────────────────────────────────────────────────────
Secret 1 of 5
NAME:   TAU_USERNAME
VALUE:  lotantamary
────────────────────────────────────────────────────────────────────
Secret 2 of 5
NAME:   TAU_ID
VALUE:  206694028
────────────────────────────────────────────────────────────────────
Secret 3 of 5
NAME:   TAU_PASSWORD
VALUE:  <the password you typed at the prompt — yes, the script prints it back so you can copy-paste it>
────────────────────────────────────────────────────────────────────
Secret 4 of 5
NAME:   GOOGLE_CREDENTIALS_B64
VALUE:  eyJpbnN0YWxsZWQiOnsiY2xpZW50X2lkIjoi…   (very long, all on ONE line)
────────────────────────────────────────────────────────────────────
Secret 5 of 5
NAME:   GOOGLE_TOKEN_B64
VALUE:  eyJ0b2tlbiI6Imt5YV9TY3hPa3FXY2NRSlFCNXc…  (very long, all on ONE line)
────────────────────────────────────────────────────────────────────

After adding all 5, go to the "Actions" tab → "Daily Moodle sync" →
"Run workflow" to trigger your first sync.
```

The repo URL is auto-derived from `git remote get-url origin` (parsing for owner/repo) so the friend doesn't have to paste it.

### Error handling

| Failure | Response |
|---|---|
| Not in project root (`src/main.py` not found) | Print: "Run this from the moodle-automation/ directory: `python scripts/setup.py`" → exit 1 |
| `credentials.json` missing | Print: "Place credentials.json in the project root, then re-run." → exit 1 |
| OAuth flow exception (browser closed, user denied, etc.) | Print: "OAuth was canceled or failed: `<error>`. Re-run when ready." → exit 1 |
| Empty input for any TAU credential | Re-prompt (don't accept blank) |
| Re-run with `token.json` already present | If still valid, skip OAuth; if expired, re-trigger flow |

### Things deliberately NOT in the script

- ❌ Pushing secrets via `gh secret set` (Mode B locked in)
- ❌ Walking through notification setup (handled by README's Notifications section)
- ❌ Verifying TAU credentials work (no way to validate before first workflow run)
- ❌ Any network call besides the OAuth flow itself
- ❌ Logging/debug output beyond the required prompts/output
- ❌ A `--help` flag with multiple options. If invoked with any argument, print a short usage line and exit.

---

## 5. Build sequence and decision points

Phase 2 breaks into 4 phases. Total ~3 hours active work + optional friend-test.

### Phase A — `scripts/setup.py` *(target: 30-45 min)*

Write the script per Section 4 contract.

**Pass criterion:** project owner can run `python scripts/setup.py` against a *fresh* clone of own repo with own `credentials.json` placed in root, and end up with all 5 secret name/value pairs printed correctly. The OAuth flow opens browser, sign-in works, `token.json` is created. Base64 strings decode back to the original JSON.

**Test trick:** clone the repo to a temp directory and run from there. Verifies path-finding logic.

### Phase B — README rewrite *(target: 1-1.5 hours)*

Implement Section 3 structure. Major rewrite, one PR / commit.

**Pass criterion:** every step has a verify command; every command block has Windows + Mac variants; "For AI agents" callout exists at the top; the Google Cloud Console walkthrough has step-by-step click-by-click instructions.

### Phase C — Self-validation *(target: 30-60 min)*

Project owner walks through the README from scratch as if a new friend. Use a fresh clone or fresh GitHub account.

Note every:
- Step where you needed to "fill in the blank" with knowledge not in the docs
- Command that didn't work as written
- Verify command that gave unexpected output
- Spot where you weren't sure if something succeeded or not

Fix every gap, then validate again. Stop when you can complete setup with the README alone.

**Pass criterion:** end-to-end fork-to-first-sync in <30 min using only the README.

### Phase D — Docs close-out *(target: 15 min)*

- Update `CLAUDE.md`: Status → "Phase 2 complete"
- Add `scripts/setup.py` to architecture map
- Update `.claude/docs/architectural_patterns.md` with the bootstrap pattern
- Mark this spec status → "Implemented and verified"
- Empty milestone commit: `milestone: Phase 2 complete; ready for friend onboarding`

### Decision points

| When | Decide | Why |
|---|---|---|
| End of Phase A | Does the script run end-to-end on owner's machine? | If not, debug — we don't even know if it works for ourselves yet |
| End of Phase B | Does the README structure feel maintainable? Any sections too long? | Last chance to restructure before validation |
| End of Phase C | Any gaps you couldn't fix purely in docs? | If yes, may need to add helpers to `setup.py` or accept the gap as troubleshooting |
| End of Phase D | Ship to first friend, or wait? | "Ship" = post repo URL in TAU friend group / DM one or two people first |

### Optional Phase E — real friend test (out of plan scope)

Strongly recommended but a one-off social action, not a code task: pick one patient friend, send them the repo URL with no other context, watch them go (in person or screen share), iterate based on real friction.

---

## 6. Risks and anti-patterns

### Critical risks

| Risk | How we'd know | Mitigation |
|---|---|---|
| **Google Cloud Console UI changes** between writing the README and friends using it | Friend reports clicks don't match doc | Use exact text labels (not pixel positions); date-stamp the Google Cloud section; troubleshooting entry: "if a step doesn't match, screenshot and message Lotan" |
| **Script fails on Mac** despite working on Windows | First Mac friend hits an error never seen | Phase C self-test catches this if a Mac is borrowable. Otherwise: explicit troubleshooting entry for `python` vs `python3`. |
| **Friend's Google account isn't on Workspace mode** | "Internal" greyed out in OAuth consent | Already in non-goals — not supported. Troubleshooting entry tells them to message owner. |
| **AI agent misinterprets the README** | Friend reports AI told them something we didn't write | "For AI agents" callout reduces this; not 100% preventable. Accept residual risk. |
| **tau-tools breaks** (TAU changes Moodle) — pre-existing | All forks fail on the same day | Same as v1: bump dep, contribute upstream. Out of Phase 2 scope. |

### Anti-patterns to enforce

- **No screenshots** in the README. Use exact UI text labels. Date-stamp anything dependent on a third-party UI state.
- **No interactive notification wizard** in `setup.py`. README's per-channel sections are sufficient. Mode B locked in.
- **No `gh` CLI requirement** anywhere in the friend's setup path. Script prints; they paste.
- **No screenshots/recordings of credentials** anywhere — even redacted. No real `credentials.json` content in the README, even as example.
- **No "if you can't follow this, just clone my .env"** — friends do not get the owner's credentials.
- **No support SLA** in the README. Friendly tone, but explicit "best-effort by project owner."
- **No language switching** — README is English. Hebrew is fine inside Tasks (assignment data) but not in docs.
- **No README bloat** — if file grows past ~500 lines, restructure rather than appending.

---

## 7. What this document is not

- An implementation plan with discrete tickets — that's the next document, produced by the writing-plans skill
- A description of Phase 3 (umbrella restructure) — separate spec/plan cycle, only when a 2nd automation arrives
- Immutable — if a phase reveals an assumption was wrong, update this spec and proceed

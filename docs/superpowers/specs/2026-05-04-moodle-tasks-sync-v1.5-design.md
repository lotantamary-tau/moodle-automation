# Moodle → Google Tasks Sync — v1.5 Design

**Date:** 2026-05-04
**Status:** Approved, ready for implementation planning
**Predecessors:** [v1 design spec](2026-05-03-moodle-tasks-sync-v1-design.md), [PRD.md](../../../PRD.md), [DECISIONS.md](../../../DECISIONS.md), [CLAUDE.md](../../../CLAUDE.md)

---

## 1. Purpose and v1.5 Scope

v1 ships a working sync that requires the user to manually run
`python -m src.main`. v1.5's purpose is to **remove the human from the loop**:
the same script runs unattended in GitHub Actions on a daily schedule, with the
user's TAU and Google credentials injected as secrets.

The "set it and forget it for me and my friends" vision becomes "set it and
forget it for me." Friend onboarding is left to a future phase but v1.5 is
designed so that adding it is cheap.

### v1.5 is

- A single new file: `.github/workflows/sync.yml`
- A small code change in `src/main.py` to use Israel-local date for the
  auto-complete heuristic when running in CI (where the OS timezone is UTC)
- 5 GitHub Secrets configured in the repo's Settings → Secrets and variables
  → Actions
- Daily scheduled runs at 05:00 UTC (= 07:00 IST winter / 08:00 IDT summer)
- Manual `workflow_dispatch` trigger available for testing without waiting for
  the cron

### v1.5 is explicitly NOT

- Friend onboarding (deferred to a separate phase — README polish, sharing
  model decisions, fork-friendly setup docs)
- Umbrella restructure of `src/` (deferred — only when a second automation is
  actually being built, per YAGNI)
- Notifications beyond GitHub's default workflow-failure email (deferred to v2
  — Telegram bot or GitHub Issues are the leading candidates)
- Retry logic for transient errors (daily cadence + idempotency makes a
  one-day blip acceptable)
- Resolving any of the deferred PRD open questions

### v1.5 success criteria

1. The workflow runs automatically every day at 05:00 UTC with zero
   intervention from the project owner.
2. A successful run is observable in the GitHub Actions tab and produces the
   same end state in Google Tasks as `python -m src.main` does locally.
3. The workflow YAML and supporting code changes do not introduce
   user-specific data into committed files. A friend forking the repo would
   only need to set their own secrets.
4. The workflow file is structured so that adding a second automation later
   (e.g. `grades_sync.yml`) requires copying-and-adjusting one workflow file,
   not rewriting from scratch.

---

## 2. Critical Risks

Three things might bite us. Each is binary: works or doesn't. We'll know
inside Phase D.

| Risk | How we'd know |
|---|---|
| **Base64 round-tripping breaks JSON** when GitHub's secret store mangles a multi-line value | The first manual run fails to parse `credentials.json` or `token.json` |
| **Library version drift between local and CI** (Windows-installed Python 3.13 vs Ubuntu Python 3.11 in Actions) | Some dependency behaves differently in CI; `pytest` results would already have caught it for `dedup`, but `tau-tools` or `google-api-python-client` could fail at runtime |
| **TAU IT or Google blocks the API call from a US-based GitHub Actions runner IP** | Auth or fetch fails in CI but works locally. Mitigation: re-run; consider self-hosted runner if persistent |

None of these is structurally fatal. All have known mitigations.

---

## 3. Architecture

### File changes

- **New:** `.github/workflows/sync.yml`
- **Modified (small):** `src/main.py` — switch `today` calculation from
  `date.today()` to `datetime.now(tz=ZoneInfo("Asia/Jerusalem")).date()`. Add
  `from zoneinfo import ZoneInfo` import.

That's the entire code surface of v1.5. Everything else is configuration
(secrets in GitHub UI, base64-encoded secret values).

### Workflow structure

The YAML defines one job, `sync`, with these steps in order:

1. `actions/checkout@v4` — pull repo source
2. `actions/setup-python@v5` — install Python 3.11 (matches `requirements.txt`)
3. `pip install -r requirements.lock.txt` — exact pinned versions
4. Decode `GOOGLE_CREDENTIALS_B64` from secrets to `credentials.json` on disk
5. Decode `GOOGLE_TOKEN_B64` from secrets to `token.json` on disk
6. `python -m src.main` — run the orchestrator with TAU env vars set from secrets

Triggers: `schedule: cron: "0 5 * * *"` AND `workflow_dispatch:` (manual button
in the Actions tab).

### Secrets layout

| Secret | Format | Source |
|---|---|---|
| `TAU_USERNAME` | plain text | from local `.env` |
| `TAU_ID` | plain text | from local `.env` |
| `TAU_PASSWORD` | plain text | from local `.env` |
| `GOOGLE_CREDENTIALS_B64` | base64-encoded JSON | `base64 < credentials.json` |
| `GOOGLE_TOKEN_B64` | base64-encoded JSON | `base64 < token.json` |

Why base64 for the JSON files specifically: GitHub Secrets technically support
multi-line strings, but the JSON contents include `{`, `}`, `"`, newlines, and
nested escapes that occasionally trigger YAML-quoting issues. Base64 reduces
the secret to a single safe ASCII string. The decode step in the workflow is
trivial.

### Cloud-portability check

We're already cloud-portable by design (12-factor env vars, no hardcoded
paths). The only adjustment v1.5 needs is the `today` timezone fix because
`date.today()` returns the OS-local date, and the OS in CI is UTC.

After v1.5, the `Config` and module structure are unchanged. A friend's fork
running with their own secrets will Just Work.

---

## 4. Build Sequence

Six phases. Total: ~1.5–2 hours active work + 24-hour passive wait between
Phase D and Phase E.

### Phase A — Code preparation *(target: 30 min)*

- Switch `src/main.py` from `date.today()` to
  `datetime.now(tz=ZoneInfo("Asia/Jerusalem")).date()`.
- Add `from zoneinfo import ZoneInfo` import.
- Add `tzdata` to `requirements.txt` and re-lock (`pip install tzdata` then
  `pip freeze > requirements.lock.txt`). `zoneinfo` is in the Python 3.9+
  standard library, but on Windows it has no embedded timezone database — the
  `tzdata` package provides it. Linux/CI has system tzdata so the package is
  redundant there but harmless.

**Pass criterion:** all 10 unit tests still pass; running `python -m src.main`
locally produces the same output as before AND the new code path works (you
can verify by adding a temporary `print(today)` and seeing an Israel-local
date even when system clock is UTC).

### Phase B — Create the workflow YAML *(target: 30 min)*

Write `.github/workflows/sync.yml` per § 3. Validate YAML with
`python -c "import yaml; yaml.safe_load(open('.github/workflows/sync.yml'))"`
or by pushing and watching for a "Workflow file is invalid" status on the
Actions tab.

**Pass criterion:** GitHub recognizes the workflow (visible in Actions tab
with the "Run workflow" button enabled).

### Phase C — Secret setup (USER manual, ~15 min)

The project owner:
1. Base64-encodes local `credentials.json` and `token.json`. On Windows
   PowerShell:
   ```powershell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("credentials.json"))
   ```
2. Adds 5 secrets via the repo's Settings UI or `gh secret set`.

**Pass criterion:** `gh secret list` returns all 5 secret names.

### Phase D — Live manual trigger test *(target: 10 min)*

Trigger the workflow manually from the Actions tab → "Run workflow" button.
Watch the live log. Confirm:
- All steps complete with exit code 0
- The script's stdout shows correct sync behavior
- Google Tasks reflects the expected state (typically: zero changes since
  the local run already synced everything)

**Pass criterion:** green checkmark on the manual run; no unexpected changes
in Google Tasks.

**Decision point:** if the manual run fails, debug before relying on the
schedule. Common failure modes are listed in § 2.

### Phase E — Confirm scheduled run *(24-hour wait + 5 min verification)*

Wait for the first scheduled execution at the next 05:00 UTC. Verify in the
Actions tab.

**Pass criterion:** scheduled run shows green; logs match expectations; if
any new assignments were issued during the wait, they appear in Tasks.

### Phase F — Documentation and close-out *(target: 15 min)*

- Update [CLAUDE.md](../../../CLAUDE.md) Status line to "v1.5 complete."
- Update this spec's Status to reflect completion.
- Update [.claude/docs/architectural_patterns.md](../../.claude/docs/architectural_patterns.md)
  to reference the new workflow file with a `file:line` ref.
- Mark the milestone with an empty commit:
  ```
  git commit --allow-empty -m "milestone: v1.5 cron complete; ready for v2 (notifications) or Phase 2 (friend onboarding)"
  ```

---

## 5. Decision Points (explicit)

| When | Decide | Why now |
|---|---|---|
| End of Phase D | Does the manual run succeed? | If not, the schedule is moot; debug before continuing |
| End of Phase E | Does the scheduled run succeed at 05:00 UTC? | Confirms the cron actually fires; sometimes GitHub Actions cron has multi-minute scheduling lag, and we need to know it's reliable |
| End of Phase F | Move to v2 (notifications), Phase 2 (friend onboarding), or stop? | All three are valid next steps; user picks based on what they need most |

---

## 6. Testing Approach

Same as v1: targeted, not comprehensive.

- **No new unit tests.** The single code change (timezone fix) doesn't change
  observable behavior in tests; `tests/test_dedup.py` already passes `today`
  as a parameter, so the change is invisible to dedup tests.
- **No tests for the workflow YAML.** It's wiring; the acceptance test is
  Phase D (manual trigger) and Phase E (scheduled trigger).
- **All 10 existing dedup tests must continue to pass.** Run `pytest -v` after
  Phase A to confirm no regression.

---

## 7. Anti-patterns to enforce during implementation

(Carried forward from v1's anti-pattern list, with v1.5-specific additions.)

- **No user-specific values committed to the workflow YAML.** Everything that
  varies between users is a secret. The same workflow file works for any TAU
  student in any fork without modification.
- **No hardcoded paths to `credentials.json` or `token.json` in the workflow.**
  The decode step writes to specific filenames; the script reads those
  filenames via `Config`. The names match between code and workflow but only
  in one place: `.env.example` and `Config` defaults.
- **No `--no-verify` or skipping CI.** If the workflow fails on push, fix the
  underlying issue.
- **No `secret-string` interpolation in the YAML's `run:` blocks.** Always
  pass secrets via `env:` to keep them out of command lines and shell history.
- **No retry-on-failure logic in v1.5.** Daily cadence + idempotency =
  acceptable to skip. Tempting to add but premature.
- **No notifications added during v1.5.** Stay focused. v2 is its own
  brainstorm.

---

## 8. Future-friendly design constraints (already baked in)

The whole point of starting small is keeping later phases cheap. v1.5 is
structured so that:

- **Friend onboarding (Phase 2):** the workflow YAML reads only from secrets.
  Friends fork, add their own 5 secrets, and the workflow runs unchanged.
  README polish at that time, but zero workflow or code changes.
- **Umbrella restructure (Phase 3):** the workflow uses `python -m src.main`.
  When `src/grades_sync/main.py` arrives, you copy `sync.yml` to
  `grades_sync.yml` and change one line (`-m src.grades_sync.main`). v1.5's
  workflow file doesn't need restructuring.
- **Notifications (v2):** `main.py` already counts created/completed tasks.
  v2 adds a notifier call after the loop. No structural change to v1.5.

---

## 9. What this document is not

- An implementation plan with discrete tickets — that's the next document, to
  be produced by the writing-plans skill
- A description of friend onboarding or umbrella restructure — those are
  separate spec/plan cycles
- Immutable — if a phase reveals that an assumption was wrong, update this
  spec and proceed

# Moodle → Google Tasks Sync — v2 Notifications Design

**Date:** 2026-05-05
**Status:** Approved, ready for implementation planning
**Predecessors:** [v1.5 design spec](2026-05-04-moodle-tasks-sync-v1.5-design.md), [v1 design spec](2026-05-03-moodle-tasks-sync-v1-design.md), [PRD.md](../../../PRD.md), [DECISIONS.md](../../../DECISIONS.md), [CLAUDE.md](../../../CLAUDE.md)

---

## 1. Purpose and v2 Scope

v1 ships a working sync. v1.5 makes it run unattended every day. Both phases are
silent: the user discovers changes by checking Google Tasks. v2's purpose is to
**actively notify the user** when the daily run actually does something —
either creating new tasks or auto-completing ones the user submitted in Moodle.

The design enables this for the project owner *and* for any friend who later
forks the repo, and it does so without forcing any single notification channel
on anyone. Each channel is opt-in per fork.

### v2 is

- A new module `src/notifier.py` containing one function per channel and a
  shared formatter
- Four notification channels, each independent and opt-in:
  1. **GitHub Issues** — opens a new issue (then immediately closes it) in the
     fork; the fork owner receives email via GitHub's default repo-watcher
     notifications
  2. **ntfy.sh** — POST to a user-chosen topic on the public ntfy.sh server,
     subscribed to via the ntfy phone app
  3. **Telegram** — POST to the Telegram Bot API; user creates a bot via
     `@BotFather` and finds their own chat ID
  4. **Discord** — POST to a webhook URL the user creates in any Discord
     server they own
- Wiring in `src/main.py` to call `notifier.notify_all(...)` after the
  create/complete loop, passing the lists of titles
- Five new optional fields in `Config` and five new optional env vars in the
  GitHub Actions workflow
- A "Notifications (optional)" section in `README.md` documenting setup for
  each channel

### v2 is explicitly NOT

- **WhatsApp** — no free, easy, programmatic option for personal automation;
  see § 3 for the rationale and dropped alternatives
- **Slack, email (SMTP), Pushover, Pushbullet** — out of scope; can be added
  later as more channels in the same opt-in pattern
- **Failure notifications via channels** — GitHub's default workflow-failure
  email already covers this; doubling up adds noise
- **Per-task notifications** — one summary message per run, not N messages
- **Rich formatting / Markdown / embeds** — plain text, identical string to
  every channel, to keep the formatter simple and channel-agnostic
- **Friend onboarding documentation polish** — that's a separate phase
  (Phase 2); v2 adds setup instructions for *channels* but not the broader
  fork-and-deploy walkthrough

### v2 success criteria

1. When at least one channel is configured and a daily run produces
   `created > 0` or `completed > 0`, the user receives a notification on every
   configured channel within ~10 seconds of the run completing.
2. When no channels are configured, the run completes silently — exactly the
   v1.5 behavior.
3. When a daily run produces `created == 0` and `completed == 0`, no
   notification is sent (avoids "0 new, 0 completed" spam).
4. Each channel is independent: a failure in one (e.g., Telegram bot deleted)
   does not block the others, and does not fail the workflow.
5. A friend forking the repo can enable any subset of channels by configuring
   the relevant secrets in their fork — no code changes required.

---

## 2. Critical Risks

| Risk | How we'd know | Mitigation |
|---|---|---|
| **GitHub Actions `GITHUB_TOKEN` doesn't have issues:write permission** | The first run with `NOTIFY_GITHUB_ISSUES=true` returns `403 Forbidden` | Explicit `permissions: issues: write` block in workflow YAML (Phase D) |
| **ntfy.sh server unreachable** | POST returns connection error | `_try()` wrapper logs and continues; user notices "missing notification" later if persistent |
| **Telegram bot blocked or deleted by user** | POST returns `403 Forbidden` or `400 Bad Request` | Same `_try()` mechanism; channel just goes silent |
| **Discord webhook URL revoked** | POST returns `404 Not Found` | Same `_try()` mechanism |
| **Notification spam if a bug fires multiple notifications per run** | User reports getting 5 messages for 1 sync | Notifier is called exactly once at the end of `main()`; not in any loop. Guarded by code review during Phase B. |
| **Hebrew text mangled in any channel** | User reports garbled characters | Already tested: Hebrew renders fine in Tasks; same UTF-8 stdout is the basis for the message string. Telegram, Discord, ntfy, and GitHub all support UTF-8 natively. |

None of these is structurally fatal. All have known mitigations or graceful degradation.

---

## 3. Architecture

### File changes

- **New:** `src/notifier.py`
- **New:** `tests/test_notifier.py` — 2 tests for the pure `_format_message` function
- **Modified (small):** `src/main.py` — collect created/completed titles into lists during the existing loops, then call `notifier.notify_all(...)`
- **Modified (small):** `src/config.py` — add 5 optional fields
- **Modified (small):** `.github/workflows/sync.yml` — add `permissions: issues: write` and pass 5 new env vars
- **Modified:** `README.md` — add "Notifications (optional)" section

That's the entire surface of v2. Nothing else changes.

### Notifier module structure

```python
# src/notifier.py
"""Optional notifications. Each channel is opt-in via env vars; absent => skip."""

import os
import requests

from src.config import Config


def notify_all(config: Config, created_titles: list[str], completed_titles: list[str]) -> None:
    """Send notifications via every configured channel. Silent if nothing changed."""
    if not created_titles and not completed_titles:
        return
    message = _format_message(created_titles, completed_titles)
    _try("github_issue", lambda: _notify_github_issue(config, message))
    _try("ntfy", lambda: _notify_ntfy(config, message))
    _try("telegram", lambda: _notify_telegram(config, message))
    _try("discord", lambda: _notify_discord(config, message))


def _format_message(created_titles: list[str], completed_titles: list[str]) -> str:
    parts = ["Moodle Tasks Sync:"]
    if created_titles:
        parts.append("")
        parts.append(f"new assignments({len(created_titles)}):")
        parts.extend(created_titles)
    if completed_titles:
        parts.append("")
        parts.append(f"completed assignments({len(completed_titles)}):")
        parts.extend(completed_titles)
    return "\n".join(parts)


def _try(channel_name: str, fn) -> None:
    try:
        fn()
    except Exception as e:
        print(f"[notifier] {channel_name} failed: {e}")


def _notify_github_issue(config: Config, message: str) -> None:
    if not config.notify_github_issues:
        return
    # Uses GITHUB_TOKEN env var (auto-provided in Actions; user sets locally if desired)
    # POST to /repos/{owner}/{repo}/issues to create, then PATCH state=closed
    ...


def _notify_ntfy(config: Config, message: str) -> None:
    if not config.ntfy_topic:
        return
    requests.post(f"https://ntfy.sh/{config.ntfy_topic}", data=message.encode("utf-8"), timeout=10)


def _notify_telegram(config: Config, message: str) -> None:
    if not (config.telegram_bot_token and config.telegram_chat_id):
        return
    requests.post(
        f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage",
        json={"chat_id": config.telegram_chat_id, "text": message},
        timeout=10,
    )


def _notify_discord(config: Config, message: str) -> None:
    if not config.discord_webhook_url:
        return
    requests.post(config.discord_webhook_url, json={"content": message}, timeout=10)
```

### Message format

Identical text sent to all four channels, plain UTF-8. Two examples:

**Mixed (2 new + 1 completed):**
```
Moodle Tasks Sync:

new assignments(2):
אלגוריתמים: שאלות הבנה – שבוע 4
Software Project: HW 1

completed assignments(1):
נוירוביולוגיה: תרגיל 3
```

**Only new (3 new, 0 completed):**
```
Moodle Tasks Sync:

new assignments(3):
אלגוריתמים: שאלות הבנה – שבוע 4
מבנה מחשבים: שאלות הבנה – שבוע 2
Software Project: HW 1
```

**Only completed (0 new, 1 completed):**
```
Moodle Tasks Sync:

completed assignments(1):
נוירוביולוגיה: תרגיל 3
```

**Both empty:** no notification fires (early return in `notify_all`).

### Config additions

```python
# src/config.py — Config dataclass gets these new fields
notify_github_issues: bool = False
ntfy_topic: str = ""
telegram_bot_token: str = ""
telegram_chat_id: str = ""
discord_webhook_url: str = ""
```

`load()` reads each from its env var (`NOTIFY_GITHUB_ISSUES`, `NTFY_TOPIC`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `DISCORD_WEBHOOK_URL`) with safe defaults. The `notify_github_issues` bool is parsed as `os.environ.get("NOTIFY_GITHUB_ISSUES", "").lower() == "true"`.

### Workflow YAML changes

Two changes in `.github/workflows/sync.yml`:

1. Add a `permissions:` block:
   ```yaml
   permissions:
     contents: read
     issues: write
   ```
2. Pass new secrets through the `Run sync` step's `env:` block:
   ```yaml
   NOTIFY_GITHUB_ISSUES: ${{ vars.NOTIFY_GITHUB_ISSUES }}
   NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
   TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
   TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
   DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
   ```
   Note: `NOTIFY_GITHUB_ISSUES` is a non-secret variable (not `secrets.`) because it's a public flag. `GITHUB_TOKEN` is auto-provided by Actions and doesn't need to be added.

For local development, the user's own `GITHUB_TOKEN` (a Personal Access Token) would need to be in `.env` if they want GitHub Issue notifications when running locally. v2 doesn't require this — local runs without `GITHUB_TOKEN` simply skip the channel.

### Channel-specific operational notes

**GitHub Issues:**
- Two API calls per notification: POST to create, PATCH to close
- Uses `requests` and the `GITHUB_TOKEN` env var; no extra dependencies
- Repository identifier (`owner/repo`) is read from `GITHUB_REPOSITORY` env var (auto-provided in Actions)
- Locally: user must set `GITHUB_REPOSITORY=owner/repo` if they want this channel

**ntfy.sh:**
- Single POST; body is the raw message bytes
- No auth needed; topic obscurity *is* the security model — pick a hard-to-guess topic (UUID-like)
- User installs the **ntfy** app on iOS or Android, taps "Subscribe to topic", enters their topic name once

**Telegram:**
- Single POST to Bot API
- User creates the bot via `@BotFather` (Telegram chat with the official bot creator)
- User finds their own `chat_id` by sending any message to their new bot, then visiting `https://api.telegram.org/bot<token>/getUpdates` to read the chat ID from the response

**Discord:**
- Single POST to the webhook URL
- User creates the webhook in any server they own (Server Settings → Integrations → Webhooks → New Webhook)
- The webhook URL is the credential — anyone with it can post to that channel; treat it as a secret

### Failure isolation

`_try()` in `notify_all()` ensures one channel's failure doesn't break the others:

- Catches all exceptions per channel
- Logs `[notifier] <channel> failed: <error>` to stdout
- Does not raise; main.py continues normally

This means: a notification-related bug or an external service outage **never** causes the sync workflow to fail. The user might miss a notification, but the sync itself remains reliable.

---

## 4. Build Sequence

Seven phases. Total: ~3 hours active work + user-side channel testing time.

### Phase A — Config additions *(target: 15 min)*

Add 5 optional fields to `Config` in `src/config.py`, populated from env vars in `load()`. No tests needed (config is simple data).

**Pass criterion:** all 10 unit tests still pass; running `python -m src.main` locally without any new env vars set produces identical behavior to v1.5.

### Phase B — Notifier module *(target: 1.5 hours)*

Create `src/notifier.py` per § 3. Create `tests/test_notifier.py` with two tests for `_format_message`:

1. Mixed: `created=["A: 1", "B: 2"], completed=["C: 3"]` → exact expected multi-line string
2. Only new: `created=["A: 1"], completed=[]` → no "completed" section in output

**Pass criterion:** all 12 tests pass (10 dedup + 2 format).

### Phase C — Wire into main.py *(target: 15 min)*

Modify the existing create and complete loops to also collect title strings into lists. After both loops, call `notifier.notify_all(cfg, created_titles, completed_titles)`.

**Pass criterion:** local run with no notification env vars set produces identical output to v1.5 (the `notify_all` early-return triggers when nothing changed).

### Phase D — Workflow YAML updates *(target: 15 min)*

Add `permissions: issues: write` and the 5 new env passthroughs.

**Pass criterion:** YAML still validates (`yaml.safe_load`); a manual `workflow_dispatch` run still succeeds (with no notifications fired since no test scenario is set up yet).

### Phase E — Channel testing *(target: 30 min, mostly USER actions)*

The user configures the channels they want to use, then triggers one workflow run that exercises all enabled channels at once.

For each channel:
1. Configure the channel (per § 3 operational notes)
2. Set the env var(s) as repo secrets via `gh secret set` or the GitHub UI

Then a single test run:
1. Delete one task in Google Tasks (so a new one will be created)
2. `gh workflow run "Daily Moodle sync"`
3. Watch the logs — confirm: task created, notification sent on each enabled channel
4. Visually verify each channel: ntfy phone app, Telegram chat, Discord channel, GitHub Issues tab

**Pass criterion:** every enabled channel receives the formatted notification message; the closed GitHub Issue (if enabled) appears in the repo's Issues tab.

### Phase F — README documentation *(target: 30 min)*

Add a "Notifications (optional)" section to `README.md`. For each channel:

- One-line description
- Step-by-step setup instructions (links to BotFather, ntfy app, Discord webhook docs, etc.)
- Which env var(s) to set, and where (GitHub Secrets vs `.env`)

Friend-facing copy. Assumes nothing about the reader's existing accounts.

### Phase G — Close-out *(target: 15 min)*

- Update [CLAUDE.md](../../../CLAUDE.md) Status to "v2 complete"
- Update this spec's Status to "Implemented and verified"
- Update [.claude/docs/architectural_patterns.md](../../.claude/docs/architectural_patterns.md) with notifier reference
- Empty milestone commit:
  ```
  git commit --allow-empty -m "milestone: v2 notifications complete; ready for Phase 2 (friend onboarding)"
  ```

---

## 5. Decision Points (explicit)

| When | Decide | Why now |
|---|---|---|
| End of Phase B | Are the format tests actually catching what we care about? | If `_format_message` is buggy, every channel gets a wrong message. The tests are cheap; the bug-blast-radius without them is wide. |
| End of Phase D | Does the workflow still pass with no channels configured? | This is the "no regression" check before introducing channel testing. |
| End of Phase E | Did every enabled channel actually deliver? | Visual verification on each phone/chat. |
| End of Phase G | Move to Phase 2 (friend onboarding) now or take a break? | Natural milestone; user picks. |

The "open design questions" deferred from earlier specs remain deferred — this v2 doesn't address them and shouldn't.

---

## 6. Testing Approach

Same philosophy as v1 and v1.5: targeted, not comprehensive.

- **Unit tests for `_format_message` only** (Phase B). Pure function, edge-case-prone, blast radius if buggy. Two tests minimum.
- **No unit tests for channel functions.** They are thin wrappers around external services; testing them mostly tests `requests`. Manual verification at Phase E covers integration.
- **No unit tests for `notify_all`.** Orchestration glue; manually verified by running the workflow.
- **No unit tests for the workflow YAML.** It's wiring; the acceptance test is Phase E.

All 12 tests must pass at the end of Phase B and continue passing through Phase G.

---

## 7. Anti-patterns to enforce during implementation

(Carried forward from v1 and v1.5, with v2-specific additions.)

- **No user-specific data committed.** Channel config flows entirely through secrets/vars. Friends configure their own.
- **No retry logic** in channel functions. One attempt; on failure, log and move on. Daily cadence + idempotency handles transient issues.
- **No notification batching across runs.** Each run notifies (or doesn't) independently. No persistent state about "what we've notified about before."
- **No channel-specific message customization** in v2. Same plain-text string for all channels. Channels handle wrapping/rendering.
- **No per-channel error escalation.** All failures swallowed by `_try()`. The user might miss a notification; the workflow stays green.
- **No coupling main.py to specific channels.** main.py only calls `notifier.notify_all(...)`. Adding/removing channels is local to `notifier.py`.
- **No logging of secrets.** Channel functions never print tokens, webhook URLs, or chat IDs.

---

## 8. Future-friendly design constraints (already baked in)

The v2 architecture supports future expansion cheaply:

- **Adding a 5th channel later** (e.g., Slack, email, Pushover): one new function in `notifier.py` + one new env var in `config.py` + one new line in `notify_all()`. No restructuring.
- **Friend onboarding (Phase 2):** the channel setup steps written for the README in Phase F become the foundation of the friend-onboarding documentation. No rewrite needed.
- **Umbrella restructure (Phase 3):** `notifier.py` is a peer to `moodle_client.py` and `tasks_client.py`. When the codebase moves to `src/tasks_sync/`, `notifier.py` moves alongside or into `src/common/`. No design changes required now.

---

## 9. What this document is not

- An implementation plan with discrete tickets — that's the next document, produced by the writing-plans skill
- A description of friend onboarding (Phase 2) or umbrella restructure (Phase 3) — separate spec/plan cycles
- Immutable — if Phase E reveals an assumption was wrong, update this spec and proceed

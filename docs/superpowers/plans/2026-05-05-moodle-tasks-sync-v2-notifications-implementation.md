# Moodle → Google Tasks Sync — v2 Notifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> Each task is labeled `[SUBAGENT]`, `[USER]`, or `[SUBAGENT + USER verify]` so the controller knows whether to dispatch or hand off to the user.

**Goal:** Add opt-in notifications via 4 free channels (GitHub Issues, ntfy.sh, Telegram, Discord) so the user (and any forking friend) gets pinged when the daily sync creates new tasks or auto-completes existing ones.

**Architecture:** A new `src/notifier.py` module with one function per channel and a shared plain-text formatter. `main.py` collects created/completed titles and calls `notifier.notify_all(...)` once at the end. Each channel is independent and toggleable per-fork via secrets/vars; absent secrets = silent skip. One channel's failure doesn't break the others (`_try()` wrapper).

**Tech Stack:** Python 3.11+, `requests` (already in transitive deps via google libs), GitHub REST API, ntfy.sh HTTP API, Telegram Bot API, Discord webhook URLs.

**Spec:** [docs/superpowers/specs/2026-05-05-moodle-tasks-sync-v2-notifications-design.md](../specs/2026-05-05-moodle-tasks-sync-v2-notifications-design.md)

---

## File Structure (final state at end of v2)

| Path | Change | Responsibility |
|---|---|---|
| `src/notifier.py` | New | One function per channel + shared formatter + `notify_all()` orchestrator |
| `tests/test_notifier.py` | New | 2 tests for `_format_message` (the only logic worth unit-testing) |
| `src/config.py` | Modified | Add 5 new optional fields (`notify_github_issues`, `ntfy_topic`, `telegram_bot_token`, `telegram_chat_id`, `discord_webhook_url`) |
| `src/main.py` | Modified | Collect titles into lists during the create/complete loops; call `notifier.notify_all(...)` at the end |
| `.github/workflows/sync.yml` | Modified | Add `permissions: issues: write`; pass 5 new env vars to the `Run sync` step |
| `README.md` | Modified | Add "Notifications (optional)" section with per-channel setup instructions |

No restructuring. No new top-level dependencies (`requests` is already installed transitively by `google-api-python-client`).

## Working Assumptions Locked In For This Plan

- **Trigger:** notifications fire only when `created > 0 OR completed > 0`. No-op runs are silent.
- **Format:** plain UTF-8 text, identical for all channels:
  ```
  Moodle Tasks Sync:

  new assignments(2):
  אלגוריתמים: שאלות הבנה – שבוע 4
  Software Project: HW 1

  completed assignments(1):
  נוירוביולוגיה: תרגיל 3
  ```
  - Header always present
  - "new" section omitted if 0 new
  - "completed" section omitted if 0 completed
- **Channels (4 total):** GitHub Issues, ntfy.sh, Telegram, Discord. Each opt-in via secret/var.
- **Failure isolation:** one channel's exception logs and is swallowed; other channels still fire; workflow exits green.
- **No retries.** Single attempt per channel per run.
- **No tests beyond `_format_message`.** Channels are thin `requests.post` wrappers.
- **Working directory** for all subagent tasks: `c:\Users\lotan\UniversityDev\moodleAgent\`
- **Python interpreter:** `.venv/Scripts/python.exe`
- **Pytest binary:** `.venv/Scripts/pytest.exe`
- **gh CLI:** authenticated as `lotantamary-tau` for repo `lotantamary-tau/moodle-automation`

If any assumption changes before execution starts, the affected tasks must be revised.

---

## Phase A — Config Additions

### Task A.1: Add 5 optional notification fields to Config  `[SUBAGENT]`

**Files:**
- Modify: `src/config.py`

- [ ] **Step 1: Read the current `src/config.py`**

The file currently looks like:

```python
"""Reads env vars exactly once. Other modules accept Config as a parameter."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    tau_username: str
    tau_id: str
    tau_password: str
    google_credentials_path: str
    google_token_path: str
    moodle_session_file: str = "session.json"
    days_ahead: int = 30
    tasks_list_name: str = "Uni Assignments"
    title_format: str = "{course_name}: {title}"


def load() -> Config:
    load_dotenv()
    return Config(
        tau_username=os.environ["TAU_USERNAME"],
        tau_id=os.environ["TAU_ID"],
        tau_password=os.environ["TAU_PASSWORD"],
        google_credentials_path=os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
        google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "token.json"),
    )
```

- [ ] **Step 2: Add 5 new optional fields to the `Config` dataclass**

After the existing `title_format` line, add:

```python
    # Notification channels (all optional; absence = channel disabled)
    notify_github_issues: bool = False
    ntfy_topic: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook_url: str = ""
```

- [ ] **Step 3: Populate them in `load()`**

Update the `Config(...)` call at the end of `load()` to include these new fields:

```python
def load() -> Config:
    load_dotenv()
    return Config(
        tau_username=os.environ["TAU_USERNAME"],
        tau_id=os.environ["TAU_ID"],
        tau_password=os.environ["TAU_PASSWORD"],
        google_credentials_path=os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
        google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "token.json"),
        notify_github_issues=os.environ.get("NOTIFY_GITHUB_ISSUES", "").lower() == "true",
        ntfy_topic=os.environ.get("NTFY_TOPIC", ""),
        telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
        discord_webhook_url=os.environ.get("DISCORD_WEBHOOK_URL", ""),
    )
```

- [ ] **Step 4: Verify it loads correctly**

Run:
```
.venv/Scripts/python.exe -c "from src.config import load; c = load(); print(f'notify_github_issues={c.notify_github_issues!r}'); print(f'ntfy_topic={c.ntfy_topic!r}'); print(f'telegram_bot_token={c.telegram_bot_token!r}'); print(f'telegram_chat_id={c.telegram_chat_id!r}'); print(f'discord_webhook_url={c.discord_webhook_url!r}')"
```

Expected: prints 5 lines with the values. With no notification env vars set, all should be empty strings except `notify_github_issues=False`.

- [ ] **Step 5: Run all tests to confirm no regression**

Run: `.venv/Scripts/pytest.exe -v`
Expected: 10 passed.

- [ ] **Step 6: Run the sync to confirm it still works**

Run: `.venv/Scripts/python.exe -m src.main`
Expected: same output as before. No notifications should fire (no env vars set, and the notifier hasn't been wired in yet anyway).

- [ ] **Step 7: Commit**

```
git add src/config.py
git commit -m "feat: add optional notification channel config fields"
```

---

## Phase B — Notifier Module

### Task B.1: Scaffold `src/notifier.py` and write the first formatter test  `[SUBAGENT]`

**Files:**
- Create: `src/notifier.py`
- Create: `tests/test_notifier.py`

- [ ] **Step 1: Create `src/notifier.py` with stubs**

```python
"""Optional notifications. Each channel is opt-in via env vars; absent => skip."""

import os

import requests

from src.config import Config


def notify_all(config: Config, created_titles: list[str], completed_titles: list[str]) -> None:
    """Send notifications via every configured channel. Silent if nothing changed."""
    raise NotImplementedError


def _format_message(created_titles: list[str], completed_titles: list[str]) -> str:
    raise NotImplementedError
```

- [ ] **Step 2: Write the first failing test for `_format_message` — mixed case**

Create `tests/test_notifier.py`:

```python
from src.notifier import _format_message


def test_format_message_mixed_new_and_completed():
    """When both lists are non-empty, both sections appear in order."""
    result = _format_message(
        created_titles=["אלגוריתמים: שאלות הבנה – שבוע 4", "Software Project: HW 1"],
        completed_titles=["נוירוביולוגיה: תרגיל 3"],
    )
    expected = (
        "Moodle Tasks Sync:\n"
        "\n"
        "new assignments(2):\n"
        "אלגוריתמים: שאלות הבנה – שבוע 4\n"
        "Software Project: HW 1\n"
        "\n"
        "completed assignments(1):\n"
        "נוירוביולוגיה: תרגיל 3"
    )
    assert result == expected
```

- [ ] **Step 3: Run the test, verify it FAILS**

Run: `.venv/Scripts/pytest.exe tests/test_notifier.py::test_format_message_mixed_new_and_completed -v`
Expected: FAIL with NotImplementedError.

- [ ] **Step 4: Implement `_format_message`**

Replace the stub of `_format_message` in `src/notifier.py`:

```python
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
```

- [ ] **Step 5: Run the test, verify it PASSES**

Run: `.venv/Scripts/pytest.exe tests/test_notifier.py::test_format_message_mixed_new_and_completed -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```
git add src/notifier.py tests/test_notifier.py
git commit -m "test: notifier _format_message handles mixed new and completed"
```

### Task B.2: Add the second formatter test — only-new edge case  `[SUBAGENT]`

**Files:**
- Modify: `tests/test_notifier.py`

- [ ] **Step 1: Append the second test**

Add to `tests/test_notifier.py` below the first test:

```python
def test_format_message_only_new_omits_completed_section():
    """When completed_titles is empty, the 'completed' section is not in the output."""
    result = _format_message(
        created_titles=["Software Project: HW 1"],
        completed_titles=[],
    )
    expected = (
        "Moodle Tasks Sync:\n"
        "\n"
        "new assignments(1):\n"
        "Software Project: HW 1"
    )
    assert result == expected
    # Sanity: 'completed' must not appear at all
    assert "completed" not in result
```

- [ ] **Step 2: Run, verify it PASSES with no implementation change**

Run: `.venv/Scripts/pytest.exe tests/test_notifier.py -v`
Expected: 2 passed.

(The implementation already handles this case correctly because `if completed_titles:` short-circuits when the list is empty. This test is a regression guard.)

- [ ] **Step 3: Commit**

```
git add tests/test_notifier.py
git commit -m "test: notifier _format_message omits empty sections"
```

### Task B.3: Implement `notify_all()` and the four channel functions  `[SUBAGENT]`

**Files:**
- Modify: `src/notifier.py`

- [ ] **Step 1: Replace the entire `src/notifier.py`**

Use the Write tool to overwrite `src/notifier.py` with:

```python
"""Optional notifications. Each channel is opt-in via env vars; absent => skip."""

import os
from typing import Callable

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


def _try(channel_name: str, fn: Callable[[], None]) -> None:
    """Run a channel's notify function. Log and swallow exceptions so one failure
    doesn't prevent other channels from firing."""
    try:
        fn()
    except Exception as e:
        print(f"[notifier] {channel_name} failed: {e}")


def _notify_github_issue(config: Config, message: str) -> None:
    """Open an issue with the message, then close it immediately. Notification
    happens via GitHub's default repo-watcher email on issue creation.

    Reads GITHUB_TOKEN and GITHUB_REPOSITORY directly from os.environ — both are
    auto-provided by GitHub Actions, and locally they're set by the user only if
    they want this channel.
    """
    if not config.notify_github_issues:
        return
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("[notifier] github_issue: NOTIFY_GITHUB_ISSUES=true but GITHUB_TOKEN or GITHUB_REPOSITORY missing; skipping")
        return
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    title = message.split("\n")[0]
    create_resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers=headers,
        json={"title": title, "body": message},
        timeout=10,
    )
    create_resp.raise_for_status()
    issue_number = create_resp.json()["number"]
    requests.patch(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        headers=headers,
        json={"state": "closed"},
        timeout=10,
    ).raise_for_status()
    print(f"[notifier] github_issue: opened+closed #{issue_number}")


def _notify_ntfy(config: Config, message: str) -> None:
    if not config.ntfy_topic:
        return
    requests.post(
        f"https://ntfy.sh/{config.ntfy_topic}",
        data=message.encode("utf-8"),
        timeout=10,
    ).raise_for_status()
    print(f"[notifier] ntfy: posted to topic")


def _notify_telegram(config: Config, message: str) -> None:
    if not (config.telegram_bot_token and config.telegram_chat_id):
        return
    requests.post(
        f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage",
        json={"chat_id": config.telegram_chat_id, "text": message},
        timeout=10,
    ).raise_for_status()
    print(f"[notifier] telegram: sent to chat")


def _notify_discord(config: Config, message: str) -> None:
    if not config.discord_webhook_url:
        return
    requests.post(
        config.discord_webhook_url,
        json={"content": message},
        timeout=10,
    ).raise_for_status()
    print(f"[notifier] discord: posted to webhook")
```

- [ ] **Step 2: Verify it imports cleanly**

Run: `.venv/Scripts/python.exe -c "from src.notifier import notify_all, _format_message; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Verify all tests still pass**

Run: `.venv/Scripts/pytest.exe -v`
Expected: 12 passed (10 dedup + 2 format).

- [ ] **Step 4: Smoke test `notify_all` with empty lists (should early-return silently)**

Run:
```
.venv/Scripts/python.exe -c "from src.config import load; from src.notifier import notify_all; notify_all(load(), [], []); print('returned silently as expected')"
```

Expected output: just `returned silently as expected`. No `[notifier]` log lines (the early-return triggers because both lists are empty).

- [ ] **Step 5: Smoke test `notify_all` with content but no channels configured**

Run:
```
.venv/Scripts/python.exe -c "from src.config import load; from src.notifier import notify_all; notify_all(load(), ['Course X: Task Y'], []); print('done')"
```

Expected output: just `done`. No `[notifier]` log lines because no channel is configured (the `_notify_*` functions all early-return when their config is empty), and `_try` only logs on exception.

- [ ] **Step 6: Commit**

```
git add src/notifier.py
git commit -m "feat: notifier with 4 channel implementations and failure isolation"
```

---

## Phase C — Wire `notify_all` into `main.py`

### Task C.1: Collect titles and call notifier  `[SUBAGENT]`

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: Read the current `src/main.py`**

The file currently looks like:

```python
"""Entry point: orchestrates fetch -> dedup -> create+complete."""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from src import config, dedup, moodle_client, tasks_client


def main() -> None:
    # Force UTF-8 stdout so Hebrew task titles don't crash Windows cp1252 terminals
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    cfg = config.load()
    print("[main] starting sync")

    assignments = moodle_client.fetch(cfg)
    existing = tasks_client.list_existing(cfg)

    new_assignments = dedup.find_new(assignments, existing)
    print(f"[dedup] {len(new_assignments)} new assignment(s) to push (out of {len(assignments)} fetched)")

    active_existing = [t for t in existing if not t.completed]
    israel_today = datetime.now(tz=ZoneInfo("Asia/Jerusalem")).date()
    to_complete = dedup.find_completed(assignments, active_existing, today=israel_today)
    print(f"[dedup] {len(to_complete)} task(s) to mark completed")

    for a in new_assignments:
        title = cfg.title_format.format(course_name=a.course_name, title=a.title)
        notes = f"moodle_id:{a.moodle_id}"
        due_str = a.due_date.strftime("%Y-%m-%dT00:00:00.000Z")
        tasks_client.create(cfg, title, notes, due_str)

    for t in to_complete:
        tasks_client.mark_complete(cfg, t.google_id)

    print(f"[main] done. created={len(new_assignments)} completed={len(to_complete)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add `notifier` to the imports**

Change the import line:
```python
from src import config, dedup, moodle_client, tasks_client
```

To:
```python
from src import config, dedup, moodle_client, notifier, tasks_client
```

- [ ] **Step 3: Modify the create loop to collect titles**

Replace:
```python
    for a in new_assignments:
        title = cfg.title_format.format(course_name=a.course_name, title=a.title)
        notes = f"moodle_id:{a.moodle_id}"
        due_str = a.due_date.strftime("%Y-%m-%dT00:00:00.000Z")
        tasks_client.create(cfg, title, notes, due_str)
```

With:
```python
    created_titles: list[str] = []
    for a in new_assignments:
        title = cfg.title_format.format(course_name=a.course_name, title=a.title)
        notes = f"moodle_id:{a.moodle_id}"
        due_str = a.due_date.strftime("%Y-%m-%dT00:00:00.000Z")
        tasks_client.create(cfg, title, notes, due_str)
        created_titles.append(title)
```

- [ ] **Step 4: Modify the complete loop to collect titles**

Replace:
```python
    for t in to_complete:
        tasks_client.mark_complete(cfg, t.google_id)
```

With:
```python
    completed_titles: list[str] = []
    for t in to_complete:
        tasks_client.mark_complete(cfg, t.google_id)
        completed_titles.append(t.title)
```

- [ ] **Step 5: Call `notifier.notify_all` after both loops**

Insert this line after the complete loop and before the final `print` statement:

```python
    notifier.notify_all(cfg, created_titles, completed_titles)
```

The final state of the bottom of `main()` should be:

```python
    completed_titles: list[str] = []
    for t in to_complete:
        tasks_client.mark_complete(cfg, t.google_id)
        completed_titles.append(t.title)

    notifier.notify_all(cfg, created_titles, completed_titles)

    print(f"[main] done. created={len(new_assignments)} completed={len(to_complete)}")
```

- [ ] **Step 6: Verify it imports cleanly**

Run: `.venv/Scripts/python.exe -c "from src import main; print('ok')"`
Expected: `ok`

- [ ] **Step 7: Run all tests**

Run: `.venv/Scripts/pytest.exe -v`
Expected: 12 passed.

- [ ] **Step 8: Run the sync end-to-end locally — should be silent (no notifications)**

Run: `.venv/Scripts/python.exe -m src.main`
Expected output (no notification lines because no channels are configured locally):
```
[main] starting sync
[moodle] fetched 2 actionable, non-overdue assignments (skipped 2 not-yet-actionable)
[tasks] listed 3 existing tasks (active+completed)
[dedup] 0 new assignment(s) to push (out of 2 fetched)
[dedup] 0 task(s) to mark completed
[main] done. created=0 completed=0
```

(Numbers may vary based on current Moodle state. The key things: no errors, no `[notifier]` log lines, exit code 0.)

- [ ] **Step 9: Commit**

```
git add src/main.py
git commit -m "feat: main collects titles and calls notifier.notify_all"
```

---

## Phase D — Workflow YAML Updates

### Task D.1: Add `permissions` block and 5 new env passthroughs  `[SUBAGENT]`

**Files:**
- Modify: `.github/workflows/sync.yml`

- [ ] **Step 1: Read the current workflow file**

The file currently looks roughly like:

```yaml
name: Daily Moodle sync

on:
  schedule:
    # Daily at 04:37 UTC (= 06:37 IST winter / 07:37 IDT summer)
    # The :37 minute avoids load spikes at the top/half of the hour.
    - cron: "37 4 * * *"
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Checkout repo
        uses: actions/checkout@v6

      - name: Set up Python 3.11
        uses: actions/setup-python@v6
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

- [ ] **Step 2: Add a `permissions:` block at the job level**

Insert this block immediately under `runs-on: ubuntu-latest` and above `timeout-minutes: 5`:

```yaml
    permissions:
      contents: read
      issues: write
```

The `jobs.sync` block should now start with:

```yaml
jobs:
  sync:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    timeout-minutes: 5
    steps:
```

- [ ] **Step 3: Pass 5 new env vars in the `Run sync` step**

Find the `env:` block under `Run sync`. Add these 5 lines below the existing `GOOGLE_TOKEN_PATH: token.json` line:

```yaml
          NOTIFY_GITHUB_ISSUES: ${{ vars.NOTIFY_GITHUB_ISSUES }}
          NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
```

The full `Run sync` block should now look like:

```yaml
      - name: Run sync
        env:
          TAU_USERNAME: ${{ secrets.TAU_USERNAME }}
          TAU_ID: ${{ secrets.TAU_ID }}
          TAU_PASSWORD: ${{ secrets.TAU_PASSWORD }}
          GOOGLE_CREDENTIALS_PATH: credentials.json
          GOOGLE_TOKEN_PATH: token.json
          NOTIFY_GITHUB_ISSUES: ${{ vars.NOTIFY_GITHUB_ISSUES }}
          NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
        run: python -m src.main
```

Notes:
- `GITHUB_TOKEN` is auto-provided by Actions; do NOT add it manually
- `GITHUB_REPOSITORY` is auto-provided by Actions; do NOT add it manually
- `NOTIFY_GITHUB_ISSUES` uses `vars.` (repository variable, not secret) because it's a public on/off toggle, not sensitive
- The other 4 use `secrets.` because they contain tokens, webhook URLs, or chat IDs

- [ ] **Step 4: Validate YAML syntax**

Run:
```
.venv/Scripts/python.exe -c "import yaml; yaml.safe_load(open('.github/workflows/sync.yml')); print('ok')"
```

Expected: `ok`. If it fails, fix indentation/quoting.

- [ ] **Step 5: Commit and push**

```
git add .github/workflows/sync.yml
git commit -m "feat: workflow grants issues:write permission and passes 5 notification env vars"
git push origin master
```

- [ ] **Step 6: Verify GitHub still recognizes the workflow as active**

Run: `gh workflow list`
Expected: includes `Daily Moodle sync` with `active` status.

---

## Phase E — Channel Setup and Live Test

### Task E.1: USER configures channels they want to use  `[USER]`

The user picks any subset of the 4 channels and configures them. Each channel can be skipped — channels with no secret stay silent.

**For each channel the user enables, follow its sub-section below.**

#### E.1.a — GitHub Issues

- [ ] Set the `NOTIFY_GITHUB_ISSUES` repository **variable** (not secret) to `true`:

  ```
  gh variable set NOTIFY_GITHUB_ISSUES --body "true" --repo lotantamary-tau/moodle-automation
  ```

  (`GITHUB_TOKEN` and `GITHUB_REPOSITORY` are auto-provided by Actions; no further setup needed.)

#### E.1.b — ntfy.sh

- [ ] Pick a hard-to-guess topic name (e.g., a UUID). On macOS/Linux you can run `uuidgen`; on Windows PowerShell run `[guid]::NewGuid().ToString()`. A random-looking string is enough.
- [ ] Install the **ntfy** app on your phone:
  - iOS: search "ntfy" in App Store
  - Android: search "ntfy" in Play Store, or get from F-Droid
- [ ] In the ntfy app, tap "+", then "Subscribe to topic", and enter your topic name.
- [ ] Set the topic as a repository **secret**:

  ```
  echo "your-chosen-topic-name" | gh secret set NTFY_TOPIC --repo lotantamary-tau/moodle-automation
  ```

#### E.1.c — Telegram

- [ ] In Telegram, message **@BotFather** and type `/newbot`. Follow the prompts to name your bot and get a **bot token** (looks like `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`).
- [ ] Send any message to your new bot in Telegram (this opens a chat).
- [ ] Find your **chat ID** by visiting (in any browser) `https://api.telegram.org/bot<your-bot-token>/getUpdates`. Look for `"chat":{"id":<some-number>}` in the JSON response. Copy that number.
- [ ] Set both as repository **secrets**:

  ```
  echo "your-bot-token" | gh secret set TELEGRAM_BOT_TOKEN --repo lotantamary-tau/moodle-automation
  echo "your-chat-id" | gh secret set TELEGRAM_CHAT_ID --repo lotantamary-tau/moodle-automation
  ```

#### E.1.d — Discord

- [ ] In Discord, go to a server you own → **Server Settings** → **Integrations** → **Webhooks** → **New Webhook**.
- [ ] Name it (e.g., "Moodle Sync"), pick a channel, copy the **webhook URL**.
- [ ] Set the webhook URL as a repository **secret**:

  ```
  echo "https://discord.com/api/webhooks/..." | gh secret set DISCORD_WEBHOOK_URL --repo lotantamary-tau/moodle-automation
  ```

After all desired channels are configured:

- [ ] **Verify the secrets and variable are set:**

  ```
  gh secret list --repo lotantamary-tau/moodle-automation
  gh variable list --repo lotantamary-tau/moodle-automation
  ```

  Expected: each enabled channel's secret/variable appears in one of those lists. (Channels you skipped won't appear — that's fine.)

### Task E.2: USER deletes one task to set up the test, then SUBAGENT triggers and verifies  `[USER + SUBAGENT verify]`

- [ ] **Step 1 (USER):** In Google Tasks, delete one task in the "Uni Assignments" list. Any one. This forces the next sync to create at least one new task, which triggers a notification.

- [ ] **Step 2 (USER):** Tell the controller you've deleted a task. The controller will trigger the workflow and watch the run.

- [ ] **Step 3 (SUBAGENT): Trigger the workflow manually**

  ```
  gh workflow run "Daily Moodle sync" --repo lotantamary-tau/moodle-automation
  sleep 5
  gh run list --workflow=sync.yml --limit=1
  ```

- [ ] **Step 4 (SUBAGENT): Watch the run and capture logs**

  ```
  gh run watch <run-id> --exit-status
  gh run view <run-id> --log
  ```

  Find the lines starting with `[notifier]`. Expected output for each enabled channel:
  - `[notifier] github_issue: opened+closed #<n>` (if GitHub Issues enabled)
  - `[notifier] ntfy: posted to topic` (if ntfy enabled)
  - `[notifier] telegram: sent to chat` (if Telegram enabled)
  - `[notifier] discord: posted to webhook` (if Discord enabled)

  And the `[main] done. created=1 completed=0` line at the bottom.

  If any `[notifier] <channel> failed: <error>` appears, debug that channel's setup.

- [ ] **Step 5 (USER): Visually verify each enabled channel received the notification**

  - **GitHub Issues:** open the repo's Issues tab → "Closed" filter → confirm a recent issue with title `Moodle Tasks Sync:` and the formatted body
  - **ntfy.sh:** check the ntfy app on your phone — a push notification should have arrived
  - **Telegram:** open the chat with your bot — the formatted message should appear
  - **Discord:** open the channel — the formatted message should appear from "Moodle Sync" (or whatever you named the webhook)

  All channels should show the expected format:
  ```
  Moodle Tasks Sync:

  new assignments(1):
  <course>: <title>
  ```

- [ ] **Step 6 (SUBAGENT): If everything verified, mark the milestone**

  ```
  git commit --allow-empty -m "milestone: v2 notifications verified across enabled channels"
  git push origin master
  ```

- [ ] **Step 7 (SUBAGENT): Diagnose any failures**

  If a channel didn't deliver, look at the run logs for that specific `[notifier]` line:

  | Symptom | Likely cause | Fix |
  |---|---|---|
  | `github_issue failed: 403` | `permissions: issues: write` missing | Verify Phase D's permissions block was committed and pushed |
  | `github_issue: ... GITHUB_TOKEN missing` | Workflow YAML didn't get auto-injected | Should not happen in Actions; if local, set GITHUB_TOKEN manually |
  | `ntfy failed: ConnectionError` | ntfy.sh server down (rare) | Retry; check https://ntfy.sh/ |
  | `telegram failed: 400 Bad Request` | Wrong chat ID or bot blocked | Re-check chat ID via getUpdates; un-block bot in Telegram |
  | `discord failed: 404` | Webhook deleted | Recreate webhook, re-set secret |
  | No `[notifier]` line at all for an enabled channel | Secret/variable not set, or set with wrong name | Re-run `gh secret set` / `gh variable set` |

---

## Phase F — README Documentation

### Task F.1: Add "Notifications (optional)" section to README  `[SUBAGENT]`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read the current `README.md`**

The file currently has sections like Setup, Tests, etc.

- [ ] **Step 2: Insert a new section between "What it does" and "Setup"**

After the "What it does" section's closing paragraph and before the "Requirements" or "Setup" heading, insert this new section:

```markdown
## Notifications (optional)

When the daily sync creates a new task or auto-completes one, you can be
notified on any of four channels — all free, all opt-in, all independent.
Skip any channels you don't want; configure only the ones you do.

If you skip ALL channels, the sync runs silently — same as before. You discover
changes by checking Google Tasks.

### GitHub Issues

Easiest option. Uses your existing GitHub account; no extra signup.

- The sync opens an issue in your fork (then closes it immediately so the
  open-issues list stays clean)
- GitHub emails you about new issues automatically as the repo owner

**Setup:** set a repository **variable** (not secret) named `NOTIFY_GITHUB_ISSUES`
to `true`. Via `gh`:

```bash
gh variable set NOTIFY_GITHUB_ISSUES --body "true"
```

Or via the web UI: Settings → Secrets and variables → Actions → Variables tab → New variable.

### ntfy.sh — phone push notifications

Free push notifications without an account.

**Setup:**
1. Install the **ntfy** app on your phone (iOS App Store or Android Play Store)
2. Pick a hard-to-guess topic name (treat it like a weak password — anyone who
   guesses it can read your messages or send fake ones)
3. In the app, tap "+" → "Subscribe to topic" → enter your topic name
4. Set it as a repo **secret**:
   ```bash
   echo "your-topic-name" | gh secret set NTFY_TOPIC
   ```

### Telegram

Rich messages in your Telegram chat.

**Setup:**
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

**Setup:**
1. In Discord: Server Settings → Integrations → Webhooks → New Webhook
2. Pick a channel, name the webhook (e.g., "Moodle Sync"), copy the URL
3. Set it as a repo **secret**:
   ```bash
   echo "https://discord.com/api/webhooks/..." | gh secret set DISCORD_WEBHOOK_URL
   ```

### Verifying

After enabling channels, you can test by deleting one task in Google Tasks
and triggering the workflow manually:

```bash
gh workflow run "Daily Moodle sync"
```

The next run will re-create the deleted task and notify all configured channels.
```

- [ ] **Step 3: Commit**

```
git add README.md
git commit -m "docs: add Notifications (optional) section with per-channel setup"
```

---

## Phase G — Close-out

### Task G.1: Update CLAUDE.md  `[SUBAGENT]`

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the Status line**

Find this paragraph in `CLAUDE.md`:

```
**Status:** v1.5 complete. The sync runs unattended every day at 05:00 UTC via
GitHub Actions. Friend onboarding (a future Phase 2) and umbrella restructure
(a future Phase 3) are deferred until needed. v2 may add notifications
(Telegram or GitHub Issues) when new tasks are detected.
```

Replace with:

```
**Status:** v2 complete. The sync runs unattended every day at 04:37 UTC via
GitHub Actions and notifies the user via any configured channels (GitHub
Issues, ntfy.sh, Telegram, Discord). Friend onboarding (a future Phase 2)
and umbrella restructure (a future Phase 3) are deferred until needed.
```

- [ ] **Step 2: Add the notifier to the Architecture quick reference**

Find the `## Architecture quick reference` heading. After the existing `tests/test_dedup.py` bullet, add:

```
- [src/notifier.py](src/notifier.py) — optional notifications across 4
  channels (GitHub Issues, ntfy.sh, Telegram, Discord); each opt-in via secret
- [tests/test_notifier.py](tests/test_notifier.py) — 2 unit tests for the
  message formatter
```

- [ ] **Step 3: Commit**

```
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md status and architecture map for v2"
```

### Task G.2: Update architectural_patterns.md  `[SUBAGENT]`

**Files:**
- Modify: `.claude/docs/architectural_patterns.md`

- [ ] **Step 1: Add a notifier paragraph**

In `.claude/docs/architectural_patterns.md`, find the `## Architectural Patterns` section. After the existing **Cron deployment via GitHub Actions** paragraph, add:

```markdown
**Opt-in notifications:** [src/notifier.py](../../src/notifier.py) sends a
single plain-text summary to any of 4 channels (GitHub Issues, ntfy.sh,
Telegram, Discord) when a daily run produces non-empty results. Each channel
is independent; absent secret = silent skip. One channel's failure is logged
and isolated so it doesn't cascade to the others (`_try()` wrapper). The
formatter is a pure function and the only tested unit
([tests/test_notifier.py](../../tests/test_notifier.py)).

```

- [ ] **Step 2: Commit**

```
git add .claude/docs/architectural_patterns.md
git commit -m "docs: document notifier pattern in architectural_patterns.md"
```

### Task G.3: Update v2 design spec status  `[SUBAGENT]`

**Files:**
- Modify: `docs/superpowers/specs/2026-05-05-moodle-tasks-sync-v2-notifications-design.md`

- [ ] **Step 1: Update the Status line**

In the spec file, find:
```
**Status:** Approved, ready for implementation planning
```

Replace with:
```
**Status:** Implemented and verified. All enabled channels deliver notifications correctly.
```

- [ ] **Step 2: Commit**

```
git add docs/superpowers/specs/2026-05-05-moodle-tasks-sync-v2-notifications-design.md
git commit -m "docs: mark v2 spec as implemented"
```

### Task G.4: Final verification and v2 milestone  `[SUBAGENT]`

- [ ] **Step 1: Run all tests**

Run: `.venv/Scripts/pytest.exe -v`
Expected: 12 passed.

- [ ] **Step 2: Run the script locally one more time**

Run: `.venv/Scripts/python.exe -m src.main`
Expected: clean run; no `[notifier]` lines (no channels configured locally).

- [ ] **Step 3: Verify recent CI runs are healthy**

Run:
```
gh run list --workflow=sync.yml --limit=5 --json conclusion,event,createdAt
```

Expected: most recent runs (the Phase E test trigger) have `conclusion=success`.

- [ ] **Step 4: Verify no secrets ever entered git history**

Run:
```
git log --all --diff-filter=A --name-only --pretty=format: | sort -u | grep -E '^\.env$|credentials\.json$|token\.json$|session\.json$' || echo "no secrets in history"
```

Expected: `no secrets in history`.

- [ ] **Step 5: Mark v2 complete with a final empty commit and push**

```
git commit --allow-empty -m "milestone: v2 complete; ready for Phase 2 (friend onboarding)"
git push origin master
```

---

## What v2 explicitly does NOT include

(Carried over from the spec; surface as a "future phase candidate" rather than building.)

- WhatsApp notifications (no free, easy programmatic option)
- Slack, email (SMTP), Pushover, Pushbullet
- Failure notifications via channels (GitHub's default failure email handles this)
- Per-task notifications (one summary per run)
- Rich formatting / Markdown / embeds
- Friend onboarding documentation polish (= Phase 2)
- Umbrella restructure of `src/` (= Phase 3)

---

## Subagent dispatch summary

For convenience when the controller dispatches:

| Task | Type | Notes |
|---|---|---|
| A.1 | SUBAGENT | Config additions + commit |
| B.1 | SUBAGENT | Notifier scaffold + first formatter test (TDD) |
| B.2 | SUBAGENT | Second formatter test (regression guard) |
| B.3 | SUBAGENT | Full notifier implementation + smoke tests |
| C.1 | SUBAGENT | Wire notify_all into main.py |
| D.1 | SUBAGENT | Workflow YAML + permissions + push |
| E.1 | USER | Configure channels (per-channel sub-tasks) |
| E.2 | USER then SUBAGENT | User deletes a task; subagent triggers + verifies |
| F.1 | SUBAGENT | README Notifications section |
| G.1 | SUBAGENT | CLAUDE.md update |
| G.2 | SUBAGENT | architectural_patterns.md update |
| G.3 | SUBAGENT | v2 spec status update |
| G.4 | SUBAGENT | Final verification + milestone |

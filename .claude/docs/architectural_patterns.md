# Architectural Patterns

> Originally drafted before code existed; updated after v1 ships to reference
> real `file:line` locations.

## Architectural Patterns

**Layered pipeline:** [src/main.py:8](src/main.py) orchestrates a one-way data
flow:

```
config.load → moodle_client.fetch → list_existing → find_new + find_completed → create + mark_complete
```

Each layer has a single responsibility and a narrow interface (lists of plain
dataclasses, never library-specific objects).

**Wrapper-per-external-service:** every external dependency is hidden behind
one module:

- [src/moodle_client.py:11](src/moodle_client.py) wraps `tau-tools.Moodle` and
  returns `list[Assignment]`
- [src/tasks_client.py:14](src/tasks_client.py) wraps Google Tasks API:
  OAuth flow, list management, read, write, complete

The orchestrator never imports `tau_tools` or `googleapiclient` directly. This
isolates breakage when an external service changes (very likely for
`tau-tools`) and lets future Moodle integrations slot in alongside
`moodle_client.py` without touching the orchestrator.

**Pure-function dedup:** [src/dedup.py](src/dedup.py) contains only pure
functions — `find_new` and `find_completed` — that take in dataclasses and
return dataclasses. They are the only tested module
([tests/test_dedup.py](tests/test_dedup.py), 10 cases).

## Design Decisions (with implementation references)

The substantive "why" lives in [DECISIONS.md](../../DECISIONS.md). Below are
the implementation locations:

1. `tau-tools` over the official Moodle Web Services API —
   [src/moodle_client.py:11](src/moodle_client.py)
2. GitHub Actions over Routines / Make / Lambda — not implemented yet, planned
   for v1.5
3. No LLM in v1 runtime — confirmed by the absence of any `anthropic` import
   in `src/`
4. Google Workspace Internal mode (TAU SSO) — chosen over External mode after
   discovering the 7-day refresh-token expiry would break unattended runs.
   Configuration in [src/tasks_client.py:11](src/tasks_client.py) (SCOPES) and
   in the Google Cloud Console project owned by the user's TAU account.
5. Two-place credentials (`.env` local, GitHub Secrets prod) with identical
   variable names — implemented via [src/config.py:23](src/config.py)
   `os.environ` reads, identical for local and CI.
6. Google Tasks over Calendar for v1 — [src/tasks_client.py](src/tasks_client.py)
   uses the Google Tasks API exclusively.

## State Management

State lives in three places, by design no shared mutable state in memory:

- **Per-run inputs:** environment variables loaded once at
  [src/config.py:24](src/config.py) `load()`. Other modules accept the typed
  `Config` as a parameter; nobody else touches `os.environ`.
- **Cross-run cache:**
  - `session.json` — tau-tools session cookie, set by
    [src/moodle_client.py:12](src/moodle_client.py)
  - `token.json` — Google OAuth refresh token, written by
    [src/tasks_client.py:21](src/tasks_client.py) `_get_credentials`. Both are
    in `.gitignore`.
- **Source of truth for "what's already synced":** Google Tasks itself. The
  Moodle assignment ID lives in the task's `notes` field as `moodle_id:<n>`,
  parsed by the regex in [src/dedup.py:8](src/dedup.py).

## Recurring Logic Patterns

- **Idempotency:** `find_new` only returns assignments not represented; main.py
  never creates a duplicate. Verified on every run via the second-run
  `created=0` invariant.
- **Auto-complete heuristic:** `find_completed` in
  [src/dedup.py](src/dedup.py) treats a task as completable when its
  `moodle_id` is gone from the current Moodle fetch AND its due date has not
  yet passed. Past-due gone-from-fetch tasks are left alone (ambiguous).
- **Fail loud, fail clear:** no exception swallowing. Stack traces bubble to
  the user / CI logs. Hebrew titles work because
  [src/main.py:11](src/main.py) forces stdout to UTF-8.
- **Never log secrets:** confirmed by inspection — no `print` of credentials
  anywhere.

## API / Interface Design Patterns

CLI entry: `python -m src.main` with no required arguments — all configuration
via env vars. See [src/main.py:36](src/main.py) `if __name__ == "__main__"`.

Internal module interfaces pass `list[Assignment]` and `list[Task]` between
layers, never library-specific objects. Defined in
[src/models.py](src/models.py).

## Dependency Injection / Inversion of Control

Lightweight, no framework. Dependencies are constructed in
[src/main.py:14](src/main.py) and passed to functions explicitly. No globals,
no singletons.

`config.py` is the only module that reads `os.environ`; every other module
accepts `Config` as a parameter. This makes adding a `--dry-run` flag trivial
in v1.5: swap the `tasks_client` for a logging stub.

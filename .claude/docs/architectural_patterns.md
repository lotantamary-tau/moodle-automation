# Architectural Patterns

> This file was initialized with the project before code exists. The patterns
> below are *proposed* — drawn from [PRD.md](../../PRD.md) and
> [DECISIONS.md](../../DECISIONS.md). As code lands, replace prose with concrete
> `file:line` references and update or remove proposals that don't survive
> contact with reality.

## Architectural Patterns

**Layered pipeline (proposed):** `moodle_client` (source) → `dedup` (filter) →
`tasks_client` (sink), orchestrated by `main.py`. Each layer has a single
responsibility and a narrow interface (lists of plain data objects), so any one
layer can be swapped or extended without touching the others.

**Wrapper-per-external-service (proposed):** every external dependency
(`tau-tools`, Google Tasks API) is hidden behind one module. The orchestrator
never imports the library directly. This:
- Isolates breakage when an external service changes (very likely for `tau-tools`)
- Lets future Moodle integrations (calendar, grades, forum activity) slot in
  alongside `moodle_client.py` without modifying the orchestrator — the user has
  flagged this extensibility as a first-class requirement
- Makes it possible to fake either side for tests without mocking deep internals

## Design Decisions

The substantive "why" lives in [DECISIONS.md](../../DECISIONS.md) — six
decisions with full reasoning. Summary index for quick navigation:

1. `tau-tools` over official Moodle Web Services API — official API blocked by
   TAU's three-field auth ([DECISIONS.md:7-26](../../DECISIONS.md#L7-L26))
2. GitHub Actions over Routines / Make / Lambda — deterministic, free,
   debuggable ([DECISIONS.md:29-50](../../DECISIONS.md#L29-L50))
3. No LLM in v1 runtime — Pro plan excludes API; v1 logic is deterministic
   ([DECISIONS.md:54-65](../../DECISIONS.md#L54-L65))
4. Public repo + fork-based sharing — clean credential isolation via per-repo
   GitHub Secrets ([DECISIONS.md:67-86](../../DECISIONS.md#L67-L86))
5. Two-place credentials (`.env` local, GitHub Secrets prod) with identical
   variable names — 12-factor pattern ([DECISIONS.md:89-95](../../DECISIONS.md#L89-L95))
6. Google Tasks over Calendar for v1 — closer fit to "list of items with due
   dates" ([DECISIONS.md:99-104](../../DECISIONS.md#L99-L104))

## State Management

State lives in three places, by design no shared mutable state in memory:

- **Per-run inputs:** environment variables (`os.environ`) — read once at startup
- **Cross-run cache:** `session.json` (TAU session cookie) and `token.json`
  (Google OAuth refresh token) on disk. Both must be in `.gitignore`. In CI,
  `token.json` is rehydrated from a GitHub Secret each run.
- **Source of truth for "what's already synced":** Google Tasks itself. The
  Moodle assignment ID lives in the task's notes (or title — TBD) and is the
  dedup key. No separate state file is planned for v1; this is fragile if users
  delete tasks manually and is one of the open design questions.

## Recurring Logic Patterns

- **Idempotency contract:** every operation that writes to Google Tasks must
  check first whether the assignment is already represented. Re-running on the
  same day is a success criterion ([PRD.md:204-208](../../PRD.md#L204-L208)),
  so this is a hard requirement, not a nice-to-have.
- **Fail loud, fail clear:** GitHub Actions logs are the only debugging surface.
  Errors should bubble up with stack traces; transient errors may retry but
  must log every attempt. Never swallow exceptions silently.
- **Never log secrets:** even when debugging auth, log only that auth was
  attempted, not what was sent.

## API / Interface Design Patterns

CLI / entry point: `python -m src.main` with no required arguments — all
configuration via env vars. Optional flags (e.g., `--dry-run`) TBD.

Internal module interfaces should pass plain data (dataclasses, dicts) between
layers, never library-specific objects. Example: `moodle_client.fetch()` returns
a list of normalized `Assignment` records, not raw `tau-tools` `AssignmentInfo`
objects. This keeps the dedup and Google-Tasks layers free of `tau-tools`
imports.

## Dependency Injection / Inversion of Control

Lightweight, no framework: dependencies are constructed in `main.py` and passed
into functions explicitly. No globals, no singletons. This makes it trivial to
substitute fakes in tests and to add a `--dry-run` mode that swaps the real
`tasks_client` for a logging stub.

Configuration is injected the same way: `config.py` reads env vars once and
exposes a typed config object that other modules accept as a parameter. No
module should call `os.environ` directly except `config.py`.

# Moodle → Google Tasks Sync — v1 Design

**Date:** 2026-05-03
**Status:** Approved, ready for implementation planning
**Predecessors:** [PRD.md](../../../PRD.md), [DECISIONS.md](../../../DECISIONS.md), [CLAUDE.md](../../../CLAUDE.md)

---

## 1. Purpose and v1 Scope

Personal automation that pulls open assignments from Tel Aviv University's
Moodle and creates Google Tasks for them. v1's purpose is to prove the pipe
works end-to-end on the project owner's own machine and account, with safe
re-runs.

### v1 is

- A locally-runnable Python script (`python -m src.main`)
- Authenticates to TAU Moodle via the `tau-tools` library, caching the session
- Fetches all upcoming assignments in a configurable window (default: next 30 days)
- Creates Google Tasks with the Moodle due date and a title format chosen at the Phase 3 decision point (default proposal: `[Course Name] Assignment Name`)
- Idempotent: re-running on the same day creates nothing new
- Logs clearly to stdout
- Configured entirely through environment variables, loaded locally from `.env`

### v1 is explicitly NOT

- Scheduled in GitHub Actions (deferred to v1.5)
- Documented for friend onboarding / fork model (deferred to v1.5)
- Filtering on submission status (`tau-tools` doesn't expose it)
- LLM-enhanced in any way at runtime
- Designed with abstractions for hypothetical future Moodle features (YAGNI)
- Resolving the 5 PRD open questions beyond dedup — those wait until they bite

### v1 success criteria

1. Project owner runs `python -m src.main` once and sees real TAU assignments
   appear in their real Google Tasks list with correct due dates.
2. Running the same command again on the same day creates zero new tasks.
3. The architecture is structured so that v1.5 (GitHub Actions) requires only
   adding `.github/workflows/weekly.yml` and configuring secrets — zero changes
   to `src/`.

---

## 2. Critical Risk

**The entire project rests on `tau-tools` working against the project owner's
TAU account.** As of design time, the library has not been executed end-to-end
by the owner. If `tau-tools` cannot authenticate, cannot reach the assignments
endpoint, or returns unusable data, no amount of architecture saves the
project.

This risk is structurally addressed by the build sequence: Phase 1 is a
throwaway 10-line spike whose only purpose is to validate the dependency.
Phases 2+ do not begin until Phase 1 passes.

---

## 3. Architecture

Plain Python modules. No framework. No plugin system. No abstraction layers
beyond what's needed to make `dedup` testable as a pure function and to keep
`tau-tools` breakage contained to one file.

### Layered pipeline

```
[env vars]
    ↓
config.py  (read once, return typed config)
    ↓
main.py orchestrator
    ├─→ moodle_client.fetch(config)        → list[Assignment]
    ├─→ tasks_client.list_existing(config) → list[Task]
    ├─→ dedup.find_new(assignments, tasks) → list[Assignment]
    └─→ tasks_client.create(task) for each
```

### Data contracts

Plain dataclasses passed between layers — never library-specific objects:

```python
@dataclass
class Assignment:
    moodle_id: int
    title: str
    course_name: str
    due_date: datetime

@dataclass
class Task:
    google_id: str
    title: str
    notes: str            # contains the moodle_id for dedup
    due_date: date | None
    completed: bool
```

The choice to wrap `tau-tools` and Google Tasks objects into our own
dataclasses serves two specific purposes:

1. **`dedup.find_new` is pure** — takes two lists, returns one list. Trivially
   unit-testable without mocking either external service.
2. **`tau-tools` breakage is contained.** When TAU changes their Moodle and
   the library breaks, only `moodle_client.py` needs adjustment. The
   orchestrator and dedup don't know what `tau-tools` is.

It does NOT serve hypothetical future "second Moodle feature" extensibility.
That's YAGNI; refactor for it the first time a real second use case appears.

### File layout

| Path | Purpose | Tested? |
|---|---|---|
| `src/__init__.py` | Package marker | — |
| `src/main.py` | Orchestrator (~30 lines) | No (manual verification) |
| `src/config.py` | Reads env vars once, returns typed `Config` | No |
| `src/models.py` | `Assignment` and `Task` dataclasses | No |
| `src/moodle_client.py` | Wraps `tau-tools.Moodle`, returns `list[Assignment]` | No (thin pass-through) |
| `src/tasks_client.py` | Google OAuth + read/write Tasks API | No (thin pass-through) |
| `src/dedup.py` | Pure function: `find_new(assignments, tasks) -> list[Assignment]` | **Yes** |
| `tests/test_dedup.py` | Unit tests for the dedup function | — |
| `requirements.txt` | Pinned dependencies | — |
| `.env.example` | Template with placeholder env var names only | — |
| `.env` | Real secrets (gitignored) | — |
| `.gitignore` | Excludes `.env`, `session.json`, `token.json`, `.venv`, `__pycache__`, `credentials.json` | — |

### Cloud-portability check

The architecture is designed to lift cleanly into GitHub Actions in v1.5 with
zero changes to `src/`:

- All secrets read via `os.environ` — same code path locally (loaded from
  `.env` by `python-dotenv`) and in CI (injected from GitHub Secrets)
- `python -m src.main` is the entry point in both
- `token.json` is base64-decoded from a GitHub Secret at job start, written to
  disk for the run, discarded after; refresh token is long-lived
- `session.json` is not preserved between CI runs; re-authenticating once a
  week is acceptable

---

## 4. Build Sequence

Five phases. Each ends with a concrete pass/fail outcome. Phase boundaries are
explicit decision points.

### Phase 0 — Environment setup *(target: 30 min)*

- Create `.venv` with Python 3.11+
- Install `tau-tools`, `google-api-python-client`, `google-auth-oauthlib`,
  `python-dotenv`; pin versions in `requirements.txt`
- Create `.gitignore` with all sensitive paths listed
- Create Google Cloud Project, enable Google Tasks API, configure an OAuth
  consent screen (testing mode is fine — no verification needed for the
  Tasks scope), download OAuth client credentials JSON, save as
  `credentials.json` (gitignored)
- Stub `.env.example` and `.env` with the 5 env var names from
  [PRD.md:109-114](../../../PRD.md#L109-L114)

**Pass criterion:** `pip list` shows the four libraries; `.gitignore` is in
place; `credentials.json` exists locally and is gitignored.

### Phase 1 — Spike: tau-tools *(target: 30 min, ceiling: 2 hours)*

- Create `spike_moodle.py` (~10 lines, throwaway)
- Construct `Moodle(username, id, password, "session.json")` from env vars
- Call `m.get_assignments(limit=50, since=now, until=now + 30 days)`
- `print()` the result

**Pass criterion:** the script prints a non-empty list of the project owner's
real upcoming assignments with recognizable course names and due dates.

**Fail handling:** if the script fails to authenticate, fails to reach the
endpoint, or returns empty / wrong-shaped data and cannot be fixed within ~2
hours of debugging, **stop the project**. The architecture below is moot
without this dependency. Pivot options (manual scraping, requesting a token
from TAU IT, abandoning the project) are evaluated at that point.

### Phase 2 — Spike: Google Tasks *(target: 1 hour)*

- Create `spike_tasks.py` (~20 lines, throwaway)
- Run the `google-auth-oauthlib` browser-based InstalledAppFlow once,
  generate `token.json`
- Use `googleapiclient.discovery.build("tasks", "v1", credentials=...)` to
  insert one hardcoded task into the default Tasks list

**Pass criterion:** the test task appears in the Google Tasks app on the
project owner's phone within seconds.

### Phase 3 — Walking skeleton *(target: 2 hours)*

- Create `walking_skeleton.py` (single file, throwaway)
- Combine spikes 1 and 2: pull all assignments from Moodle, push every single
  one as a Google Task. No dedup. No filtering. Ugly print logging.

**Pass criterion:** the project owner's real assignments appear as tasks in
the real Google Tasks list with correct due dates.

**Decision point — BEFORE Phase 4 begins:**
With real data on screen, decide and document in this spec:
- **Dedup mechanism**: store Moodle ID in task notes? title? Both? Check
  active tasks only, or active + completed?
- **Title format**: confirm `[Course Name] Assignment Name` reads well, or pick
  a different format
- **Target list**: write to the default Google Tasks list, or create a
  dedicated list named e.g. "Moodle"
- **Time window**: confirm 30 days is right; adjust default if not

**Cleanup before Phase 4:** delete the duplicate test tasks the skeleton
created in Google Tasks.

### Phase 4 — Refactor into modules + add dedup *(target: 3-4 hours)*

- Split `walking_skeleton.py` into the modules from § 3
- Implement the dedup mechanism chosen at the Phase 3 decision point
- Write `tests/test_dedup.py` with at least 5 cases:
  1. Empty existing-tasks list → all assignments are new
  2. All assignments already present → empty result
  3. Mix of present and new → only new returned
  4. Tasks with malformed/missing notes field → handled without crashing
  5. Tasks with same title but different Moodle ID → both are kept distinct
- Add `requirements.txt` and minimal `.env.example`

**Pass criterion:** `python -m src.main` run twice in a row creates new tasks
on the first run and zero tasks on the second run; `pytest` passes.

### Phase 5 — Cleanup and v1 close-out *(target: 1 hour)*

- Delete `spike_moodle.py`, `spike_tasks.py`, `walking_skeleton.py`
- Write minimal `README.md` covering only: what this is, how to set it up
  locally, how to run it. Friend-onboarding polish is v1.5.
- Update [CLAUDE.md](../../../CLAUDE.md) Build & Test Commands section with
  established commands; remove the "no `requirements.txt` exists yet" caveat
- Update [.claude/docs/architectural_patterns.md](../../../.claude/docs/architectural_patterns.md)
  to replace proposals with `file:line` references to real code
- **Decision point:** is the project ready to push to GitHub? If yes, agree on
  repo name (default `moodle-tasks-sync`, owner may bikeshed) and create the
  remote.

**Pass criterion:** v1 success criteria from § 1 hold. Working tree is clean.
Local git history tells a coherent story.

### Total estimate

8–10 hours of focused work, spread across multiple sessions.

---

## 5. Decision Points (explicit)

Three decisions are baked into the sequence rather than deferred to "we'll
figure it out":

| When | Decide | Why now |
|---|---|---|
| End of Phase 1 | Does the project survive? | Pass/fail on `tau-tools` viability — every later decision depends on this |
| Before Phase 4 | Dedup mechanism, title format, target list, time window | All four are easier to decide with real data on screen than in the abstract |
| End of Phase 4 | Is dedup actually correct? | Re-running and seeing zero new tasks is the only way to verify |
| End of Phase 5 | Push to GitHub now or stay local? | v1 may be useful enough as a local script for a while; pushing is a v1.5 prerequisite |

The other PRD open questions ([PRD.md:172-181](../../../PRD.md#L172-L181)) are
deferred until they actually bite:

- Due-date-changed handling: v1 dedup is "create-only" and ignores date
  changes. Acceptable. Revisit when a real assignment's date shifts mid-window.
- Manual completion handling: covered by the Phase 3 dedup decision
- Session expiration mid-run: handle when observed
- Summary message: v1.5+ feature
- Dry-run mode: nice-to-have, optionally added late in Phase 4 as a
  `--dry-run` flag if cheap

---

## 6. Testing Approach

Targeted, not comprehensive.

- **No tests in Phases 0-3.** Spikes and walking skeleton are throwaway code.
- **`tests/test_dedup.py` in Phase 4.** Pure-function tests. No mocking. Feed
  in fake `Assignment` and `Task` lists, assert the output. The five cases in
  Phase 4 above are the minimum.
- **No tests for `moodle_client.py` or `tasks_client.py`.** They are thin
  wrappers; testing them mostly tests the underlying libraries. Manual
  verification covers integration (Phase 3 and Phase 4 pass criteria).
- **No tests for `main.py` or `config.py`.** Glue code, manually verified by
  running the script.

The reasoning: bugs in `dedup` silently corrupt the project owner's real Task
list (duplicates, missed assignments). Bugs anywhere else surface loudly via
crashes or visibly wrong output. Tests live where silent corruption is
possible.

---

## 7. Anti-patterns to enforce during implementation

(Carried forward from CLAUDE.md, restated here so they're not lost in the
plan-to-implementation handoff.)

- **No downstream code before Phase 1 passes.** This is the whole point of the
  spike-first sequence.
- **No LLM calls anywhere in the runtime.** Out of scope for v1.
- **No hardcoded credentials.** Always env vars. `.env` always in
  `.gitignore`.
- **No user-specific data committed.** Code must work in any user's fork
  (relevant for v1.5; cheap to enforce now).
- **No TAU-specific branding** in repo metadata, README headlines, or workflow
  names.
- **No abstractions designed for hypothetical "future Moodle features."** YAGNI.
- **No scope creep without asking.** Default stance is pragmatic-but-ask:
  surface every "we could also add X" as a quick proposal with cost/benefit
  before writing it.
- **No logging of secrets**, even when debugging auth.

---

## 8. What this document is not

- An implementation plan with discrete tickets — that's the next document, to
  be produced by the writing-plans skill
- A user-facing README — that's a Phase 5 deliverable
- Immutable — if a phase reveals that a decision was wrong, update this spec
  and proceed

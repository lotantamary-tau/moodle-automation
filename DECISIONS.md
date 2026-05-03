# Architectural Decisions

This document captures the *reasoning* behind the key choices in this project. The PRD says **what** we're building; this document says **why** we built it that way. It's intended as context for future maintainers (including the original author returning to the project months later) and for AI assistants like Claude Code that may help extend the project.

---

## 1. Why `tau-tools` instead of the official Moodle Web Services API

**The official Moodle API would have been the textbook-correct choice.** It's documented, sanctioned, stable, and uses proper token authentication. We pursued it first.

**It was structurally closed off.** TAU's Moodle uses a custom authentication plugin that adds a third login field (student ID number) alongside username and password. Standard Moodle's `login/token.php` endpoint — the documented way for students to obtain an API token — only accepts username and password. The custom auth plugin never receives the ID, so authentication fails regardless of what credentials are submitted.

We tried:
- Direct `login/token.php` calls with various parameter combinations (ID as username, concatenated password values, etc.) — all failed
- Looking for the token on the Security Keys page in the user profile — TAU hides the actual token values from users
- Searching for documented workarounds — none exist for this auth pattern

**Going through TAU IT to request a token was rejected as impractical** — universities almost universally refuse student API access for personal automation, and even a successful request would take weeks.

**`tau-tools` is the right answer for this specific situation.** It's an unofficial Python library built by TAU students that handles the three-field auth by mimicking browser login flow, capturing the session cookie, and calling Moodle's internal JSON endpoints (specifically `block_timeline_extra_local_get_action_events_by_timesort`, which powers the dashboard Timeline widget). This is not HTML scraping — it's hitting real structured-data endpoints, just internal ones rather than the public-facing API.

**Trade-offs accepted:**
- Unofficial → can break if TAU changes their Moodle setup; mitigated by the library having active student maintainers
- Likely violates TAU terms of service for automated access; risk accepted by each user individually
- Requires storing the actual TAU password (not just a revocable token); mitigated by GitHub Secrets encryption

---

## 2. Why GitHub Actions instead of Claude Routines, Make, or other schedulers

The decision came down to matching the tool to the task's nature. This task is:
- **Deterministic** — same inputs should produce same outputs every run
- **Structured** — fetch JSON, transform, write JSON; no judgment required
- **Cost-sensitive** — should be free for personal use
- **Debuggable** — when it breaks, we want clear logs

**GitHub Actions wins on all four.** It runs the exact same Python every time, gives line-numbered stack traces, costs nothing for personal use, and is the standard tool developers use for cron-style automation.

**Claude Routines was seriously considered** because the user has a Pro plan and Routines fits the "describe what you want in natural language" workflow. Rejected because:
- LLM execution introduces variance into a pipeline that benefits from determinism
- Consumes Pro plan tokens on a task that doesn't actually need reasoning
- Harder to debug structured pipeline failures

**Make.com was rejected** because it can't run arbitrary Python, which we need for the `tau-tools` authentication. Make would have to call out to GitHub Actions or another runtime anyway, making it a redundant middle layer.

**Local cron was rejected** because it requires the user's computer to be on at the scheduled time.

**AWS Lambda / Google Cloud Scheduler were rejected** as overkill — they require credit cards, platform-specific learning, and offer no advantage over GitHub Actions for this scope.

**Future flexibility:** if the project later needs LLM reasoning (e.g., AI-generated assignment summaries), the right pattern is to call the Anthropic API from inside the Python script for those specific steps, not to switch the entire orchestrator to Routines. This keeps reasoning costs proportional to actual reasoning needs.

---

## 3. Why no LLM in the v1 runtime

The Pro plan does not include Anthropic API usage — API access is billed separately through the Anthropic Console. Adding LLM calls to the runtime would mean:
- Setting up a separate billing relationship
- Loading credits and managing usage
- Real per-run cost (small, but nonzero)

**Most v1 personalization doesn't actually need an LLM.** Task naming, urgency rules, list organization, and course filtering are all deterministic logic that's clearer and cheaper as plain Python rules. We reserve LLM usage for genuinely v2+ features (description summarization, effort estimation) where reasoning adds real value.

**Pro plan's value is in development, not runtime.** The user uses Pro to *build and modify* the script via Claude in chat. The script itself runs without touching Claude.

---

## 4. Why public repo with fork-based sharing instead of private repo with collaborators

The user wanted to share the project with friends while keeping their own credentials private. Two patterns were considered:

**Private repo + collaborators (rejected):**
- Friends added as collaborators have read access to the canonical repo
- They'd need to fork from a private repo, which is more friction
- More importantly: in a single-repo collaboration model, there are scenarios where one user's GitHub Secrets could be accessible to workflows triggered by other collaborators. Not a clean isolation model.

**Public repo + fork-based sharing (chosen):**
- Each user forks the repo into their own GitHub account, creating an independent repo
- GitHub Secrets are stored per-repo and forks do not inherit secrets — this is enforced by GitHub for security
- Each fork's GitHub Actions runs independently with that fork's secrets
- Standard open-source collaboration pattern; friends know how to use it
- One-click "Sync fork" lets friends pull updates without losing their secrets or schedule

**The credentials-safety insight that drove this:** credentials are *never in the code*. They live in GitHub Secrets (per-repo, encrypted) and `.env` files (local, git-ignored). Public vs. private is therefore not a credentials question — it's a question of *who can find and use the tool*, which is a softer concern handled by generic naming.

**Naming choice:** the repo uses a generic name (e.g., `moodle-tasks-sync`) rather than something explicitly TAU-referencing. This reduces discoverability by parties (especially TAU IT) who might draw attention to the underlying `tau-tools` dependency and accelerate its breakage.

---

## 5. Why store credentials in two places (`.env` locally, GitHub Secrets in production)

**Local development needs credentials to test the script before deploying.** Hardcoding them is unsafe (commits to git accidentally happen). The standard pattern is a `.env` file at project root with `.env` listed in `.gitignore`, loaded via `python-dotenv` at runtime. This file never leaves the developer's machine.

**Production (GitHub Actions) needs credentials at runtime.** GitHub Secrets is the encrypted, audited storage GitHub provides for exactly this purpose. Secrets are injected as environment variables into the workflow run, never logged, and never visible to anyone except the repo owner.

**Same variable names in both environments** means the same code runs locally and in production with no changes — `os.environ["TAU_USERNAME"]` works either way. This is a standard 12-factor app pattern.

---

## 6. Why Google Tasks rather than Calendar (for v1)

Google Tasks is simpler — it's a list of items with due dates, which maps cleanly to "assignments to do." Google Calendar is built around events with start/end times, which is a less natural fit for assignment deadlines.

**This is reversible.** v2 may add Calendar integration alongside Tasks. The Python script can write to multiple Google services from the same OAuth token (just request additional scopes during initial auth).

---

## What this document is NOT

- A full conversation transcript of how decisions were reached (intentionally summarized)
- A specification of the code (see PRD.md and the code itself)
- Immutable — if a decision turns out to be wrong during build, update both this file and PRD.md and note the change

## When to update this document

- When a "committed" architecture decision changes
- When new significant decisions are made (e.g., "we chose Notion over Obsidian for note integration because...")
- When future-you returns to the project and wonders "wait, why did we do it this way?" — that's the signal that the reasoning wasn't captured well enough

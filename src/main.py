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
        # Use local-timezone date directly to avoid date-shift bugs from UTC conversion
        due_str = a.due_date.strftime("%Y-%m-%dT00:00:00.000Z")
        tasks_client.create(cfg, title, notes, due_str)

    for t in to_complete:
        tasks_client.mark_complete(cfg, t.google_id)

    print(f"[main] done. created={len(new_assignments)} completed={len(to_complete)}")


if __name__ == "__main__":
    main()

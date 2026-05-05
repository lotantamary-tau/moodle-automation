"""Wraps tau-tools. Returns plain Assignment dataclasses; orchestrator never sees tau-tools types."""

import re
from datetime import datetime, timedelta

from tau_tools.moodle import Moodle

from src.config import Config
from src.models import Assignment

_COURSE_PREFIX_PATTERN = re.compile(r"^\d+\s*-\s*")


def _strip_course_prefix(name: str) -> str:
    """Strip leading '<digits> - ' prefix from course names like '03682160 - אלגוריתמים'."""
    return _COURSE_PREFIX_PATTERN.sub("", name).strip()


def fetch(config: Config) -> list[Assignment]:
    moodle = Moodle(
        username=config.tau_username,
        id=config.tau_id,
        password=config.tau_password,
        session_file=config.moodle_session_file,
    )
    now = datetime.now()
    horizon = now + timedelta(days=config.days_ahead)

    # Call the Moodle Timeline endpoint directly so we can access the full
    # event data, including action.actionable. tau-tools' get_assignments
    # discards this field. action.actionable=False means the assignment is
    # scheduled but not yet open for student action — we filter those out so
    # the user doesn't see tasks for assignments they can't actually start.
    response = moodle.request_service(
        "block_timeline_extra_local_get_action_events_by_timesort",
        [{
            "index": 0,
            "methodname": "block_timeline_extra_local_get_action_events_by_timesort",
            "args": {
                "limitnum": 50,
                "timesortfrom": int(now.timestamp()),
                "timesortto": int(horizon.timestamp()),
                "limittononsuspendedevents": True,
            },
        }],
    )

    result: list[Assignment] = []
    skipped_not_actionable = 0
    for event in response.get("events", []):
        if event.get("overdue"):
            continue
        action = event.get("action") or {}
        if not action.get("actionable", True):
            skipped_not_actionable += 1
            continue
        result.append(
            Assignment(
                moodle_id=event["instance"],
                title=event["name"],
                course_name=_strip_course_prefix(event["course"]["fullname"]),
                due_date=datetime.fromtimestamp(event["timesort"]),
            )
        )
    print(f"[moodle] fetched {len(result)} actionable, non-overdue assignments (skipped {skipped_not_actionable} not-yet-actionable)")
    return result

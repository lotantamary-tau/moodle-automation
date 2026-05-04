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
    # tau-tools 1.1.8 expects UNIX timestamps, not datetime objects
    raw = moodle.get_assignments(
        limit=50,
        since=int(now.timestamp()),
        until=int(horizon.timestamp()),
    )

    result: list[Assignment] = []
    for a in raw:
        if a.is_overdue:
            continue
        result.append(
            Assignment(
                moodle_id=a.id,
                title=a.name,
                course_name=_strip_course_prefix(a.course_name),
                due_date=a.due_date,
            )
        )
    print(f"[moodle] fetched {len(result)} non-overdue assignments")
    return result

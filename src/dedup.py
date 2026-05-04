"""Pure functions for finding new assignments to create and tasks to complete."""

import re
from datetime import date

from src.models import Assignment, Task

_MOODLE_ID_PATTERN = re.compile(r"moodle_id:(\d+)")


def find_new(assignments: list[Assignment], existing_tasks: list[Task]) -> list[Assignment]:
    seen_ids = _seen_moodle_ids(existing_tasks)
    return [a for a in assignments if a.moodle_id not in seen_ids]


def find_completed(assignments: list[Assignment], active_tasks: list[Task], today: date) -> list[Task]:
    current_ids = {a.moodle_id for a in assignments}
    result: list[Task] = []
    for task in active_tasks:
        match = _MOODLE_ID_PATTERN.search(task.notes)
        if not match:
            continue
        moodle_id = int(match.group(1))
        if moodle_id in current_ids:
            continue  # still pending in Moodle
        if task.due_date is None:
            continue  # ambiguous
        if task.due_date < today:
            continue  # past due, might be missed not submitted
        result.append(task)
    return result


def _seen_moodle_ids(tasks: list[Task]) -> set[int]:
    ids: set[int] = set()
    for task in tasks:
        match = _MOODLE_ID_PATTERN.search(task.notes)
        if match:
            ids.add(int(match.group(1)))
    return ids

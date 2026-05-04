"""Pure functions for finding new assignments to create and tasks to complete."""

import re

from src.models import Assignment, Task

_MOODLE_ID_PATTERN = re.compile(r"moodle_id:(\d+)")


def find_new(assignments: list[Assignment], existing_tasks: list[Task]) -> list[Assignment]:
    seen_ids = _seen_moodle_ids(existing_tasks)
    return [a for a in assignments if a.moodle_id not in seen_ids]


def _seen_moodle_ids(tasks: list[Task]) -> set[int]:
    ids: set[int] = set()
    for task in tasks:
        match = _MOODLE_ID_PATTERN.search(task.notes)
        if match:
            ids.add(int(match.group(1)))
    return ids

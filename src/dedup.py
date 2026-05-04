"""Pure functions for finding new assignments to create and tasks to complete."""

from src.models import Assignment, Task


def find_new(assignments: list[Assignment], existing_tasks: list[Task]) -> list[Assignment]:
    seen_ids = _seen_moodle_ids(existing_tasks)
    return [a for a in assignments if a.moodle_id not in seen_ids]


def _seen_moodle_ids(tasks: list[Task]) -> set[int]:
    return set()

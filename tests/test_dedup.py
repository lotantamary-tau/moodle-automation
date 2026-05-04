from datetime import datetime

from src.dedup import find_new
from src.models import Assignment, Task


def _assignment(moodle_id: int) -> Assignment:
    return Assignment(
        moodle_id=moodle_id,
        title=f"Assignment {moodle_id}",
        course_name="Course",
        due_date=datetime(2026, 6, 1, 12, 0),
    )


def _task(google_id: str, notes: str, completed: bool = False) -> Task:
    return Task(
        google_id=google_id,
        title="any",
        notes=notes,
        due_date=None,
        completed=completed,
    )


def test_empty_existing_tasks_returns_all_assignments():
    assignments = [_assignment(1), _assignment(2)]
    result = find_new(assignments, existing_tasks=[])
    assert result == assignments


def test_all_present_returns_empty():
    assignments = [_assignment(1), _assignment(2)]
    existing = [_task("g1", "moodle_id:1"), _task("g2", "moodle_id:2")]
    result = find_new(assignments, existing)
    assert result == []


def test_mix_returns_only_new():
    assignments = [_assignment(1), _assignment(2), _assignment(3)]
    existing = [_task("g1", "moodle_id:1"), _task("g3", "moodle_id:3")]
    result = find_new(assignments, existing)
    assert [a.moodle_id for a in result] == [2]

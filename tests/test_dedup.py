from datetime import date, datetime

from src.dedup import find_completed, find_new
from src.models import Assignment, Task


def _assignment(moodle_id: int) -> Assignment:
    return Assignment(
        moodle_id=moodle_id,
        title=f"Assignment {moodle_id}",
        course_name="Course",
        due_date=datetime(2026, 6, 1, 12, 0),
    )


def _task(google_id: str, notes: str, completed: bool = False, due_date: date | None = None) -> Task:
    return Task(
        google_id=google_id,
        title="any",
        notes=notes,
        due_date=due_date,
        completed=completed,
    )


TODAY = date(2026, 5, 4)


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


def test_malformed_notes_are_ignored():
    assignments = [_assignment(1), _assignment(2)]
    existing = [
        _task("g_a", ""),
        _task("g_b", "user-typed reminder"),
        _task("g_c", "moodle_id:notanumber"),
        _task("g_d", "moodle_id:1"),
    ]
    result = find_new(assignments, existing)
    assert [a.moodle_id for a in result] == [2]


def test_dedup_is_by_id_not_title():
    """Two assignments with identical titles but different IDs must both survive
    if neither ID is in the existing tasks."""
    a1 = Assignment(moodle_id=10, title="Lab", course_name="Physics", due_date=datetime(2026, 6, 1, 12, 0))
    a2 = Assignment(moodle_id=11, title="Lab", course_name="Physics", due_date=datetime(2026, 6, 8, 12, 0))
    existing = [_task("g99", "moodle_id:99")]
    result = find_new([a1, a2], existing)
    assert result == [a1, a2]


def test_find_completed_empty_active_tasks_returns_empty():
    assignments = [_assignment(1)]
    result = find_completed(assignments, active_tasks=[], today=TODAY)
    assert result == []


def test_find_completed_skips_tasks_still_in_moodle_fetch():
    assignments = [_assignment(1)]
    # task has moodle_id:1 — still in the fetch, must NOT be completed
    active = [_task("g1", "moodle_id:1")]
    result = find_completed(assignments, active, today=TODAY)
    assert result == []


def test_find_completed_skips_tasks_with_no_due_date():
    """A task gone from the fetch but with no due_date is ambiguous — leave it alone."""
    assignments = [_assignment(99)]
    active = [_task("gone_no_date", "moodle_id:1", due_date=None)]
    result = find_completed(assignments, active, today=TODAY)
    assert result == []


def test_find_completed_returns_task_gone_from_fetch_with_future_due_date():
    """A task whose moodle_id is gone from the current fetch and whose due date is
    still in the future was probably submitted — mark it complete."""
    assignments = [_assignment(99)]  # id 1 NOT in current fetch
    future = date(2026, 6, 1)
    completed_task = _task("gone_future", "moodle_id:1", due_date=future)
    active = [completed_task]
    result = find_completed(assignments, active, today=TODAY)
    assert result == [completed_task]


def test_find_completed_skips_past_due_tasks_gone_from_fetch():
    """A past-due task gone from the fetch is ambiguous (missed vs submitted late?) —
    leave it alone, the user can decide."""
    assignments = [_assignment(99)]  # id 1 NOT in current fetch
    past = date(2026, 4, 1)  # before TODAY (2026-05-04)
    active = [_task("gone_past", "moodle_id:1", due_date=past)]
    result = find_completed(assignments, active, today=TODAY)
    assert result == []

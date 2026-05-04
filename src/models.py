"""Plain data passed between modules. The only types crossing module boundaries."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Assignment:
    moodle_id: int
    title: str
    course_name: str
    due_date: datetime


@dataclass(frozen=True)
class Task:
    google_id: str
    title: str
    notes: str
    due_date: date | None
    completed: bool

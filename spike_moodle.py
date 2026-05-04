"""Throwaway spike: confirm tau-tools can fetch real assignments. Deleted in Phase 5."""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from tau_tools.moodle import Moodle

load_dotenv()

m = Moodle(
    username=os.environ["TAU_USERNAME"],
    id=os.environ["TAU_ID"],
    password=os.environ["TAU_PASSWORD"],
    session_file="session.json",
)

now = datetime.now()
horizon = now + timedelta(days=30)

# tau-tools 1.1.8 wants UNIX timestamps (ints), not datetime objects
assignments = m.get_assignments(limit=50, since=int(now.timestamp()), until=int(horizon.timestamp()))

print(f"[spike] got {len(assignments)} assignments")
for a in assignments:
    print(f"  - id={a.id} course={a.course_name!r} title={a.name!r} due={a.due_date} overdue={a.is_overdue}")

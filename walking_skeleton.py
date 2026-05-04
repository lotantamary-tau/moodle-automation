"""Throwaway walking skeleton: end-to-end, no dedup, no abstractions. Deleted in Phase 5."""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tau_tools.moodle import Moodle

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/tasks"]


def get_google_creds() -> Credentials:
    token_path = os.environ["GOOGLE_TOKEN_PATH"]
    creds_path = os.environ["GOOGLE_CREDENTIALS_PATH"]
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def main() -> None:
    moodle = Moodle(
        username=os.environ["TAU_USERNAME"],
        id=os.environ["TAU_ID"],
        password=os.environ["TAU_PASSWORD"],
        session_file="session.json",
    )

    now = datetime.now()
    horizon = now + timedelta(days=30)
    # tau-tools 1.1.8 expects UNIX timestamps, not datetime objects
    assignments = moodle.get_assignments(
        limit=50,  # TAU Moodle endpoint caps at 50
        since=int(now.timestamp()),
        until=int(horizon.timestamp()),
    )
    print(f"[skeleton] fetched {len(assignments)} assignments")

    creds = get_google_creds()
    tasks_service = build("tasks", "v1", credentials=creds)

    created = 0
    for a in assignments:
        if a.is_overdue:
            print(f"[skeleton] skip overdue: {a.name!r}")
            continue
        # Use the local-timezone date directly to avoid date-shift bugs
        # (converting to UTC can shift the date by one day for late-night deadlines)
        due_str = a.due_date.strftime("%Y-%m-%dT00:00:00.000Z")
        body = {
            "title": f"[{a.course_name}] {a.name}",
            "notes": f"moodle_id:{a.id}",
            "due": due_str,
        }
        result = tasks_service.tasks().insert(tasklist="@default", body=body).execute()
        print(f"[skeleton] created: {result['title']!r}")
        created += 1

    print(f"[skeleton] done. created={created}")


if __name__ == "__main__":
    main()

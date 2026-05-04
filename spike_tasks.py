"""Throwaway spike: confirm Google Tasks API auth + write works. Deleted in Phase 5."""

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/tasks"]
CREDS_PATH = os.environ["GOOGLE_CREDENTIALS_PATH"]
TOKEN_PATH = os.environ["GOOGLE_TOKEN_PATH"]


def get_credentials() -> Credentials:
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def main() -> None:
    creds = get_credentials()
    service = build("tasks", "v1", credentials=creds)

    due = (datetime.now(tz=timezone.utc) + timedelta(days=1)).isoformat()
    body = {
        "title": "[spike] hello from moodle-tasks-sync",
        "notes": "moodle_id:0\nThis is a spike test task. Safe to delete.",
        "due": due,
    }
    result = service.tasks().insert(tasklist="@default", body=body).execute()
    print(f"[spike] created task id={result['id']} title={result['title']!r}")


if __name__ == "__main__":
    main()

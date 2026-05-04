"""Wraps Google Tasks API: OAuth flow, list management, read, write, complete."""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import Config

SCOPES = ["https://www.googleapis.com/auth/tasks"]


def _get_credentials(config: Config) -> Credentials:
    creds = None
    if os.path.exists(config.google_token_path):
        creds = Credentials.from_authorized_user_file(config.google_token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config.google_credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(config.google_token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def _build_service(config: Config):
    return build("tasks", "v1", credentials=_get_credentials(config))


def _get_or_create_list(service, list_name: str) -> str:
    """Return the ID of the named task list, creating it if it doesn't exist."""
    all_lists = service.tasklists().list().execute().get("items", [])
    for tl in all_lists:
        if tl.get("title") == list_name:
            return tl["id"]
    created = service.tasklists().insert(body={"title": list_name}).execute()
    print(f"[tasks] created list '{list_name}'")
    return created["id"]


def list_existing(config: Config) -> list:
    """Return all Task objects from the Uni Assignments list (active + completed)."""
    from src.models import Task
    from datetime import date

    service = _build_service(config)
    list_id = _get_or_create_list(service, config.tasks_list_name)

    results: list[Task] = []
    page_token = None
    while True:
        resp = (
            service.tasks()
            .list(
                tasklist=list_id,
                showCompleted=True,
                showHidden=True,
                maxResults=100,
                pageToken=page_token,
            )
            .execute()
        )
        for item in resp.get("items", []):
            due_date = None
            if item.get("due"):
                try:
                    due_date = date.fromisoformat(item["due"][:10])
                except ValueError:
                    pass
            results.append(
                Task(
                    google_id=item["id"],
                    title=item.get("title", ""),
                    notes=item.get("notes", ""),
                    due_date=due_date,
                    completed=item.get("status") == "completed",
                )
            )
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    print(f"[tasks] listed {len(results)} existing tasks (active+completed)")
    return results


def mark_complete(config: Config, google_id: str) -> None:
    """Mark a task as completed in the Uni Assignments list."""
    service = _build_service(config)
    list_id = _get_or_create_list(service, config.tasks_list_name)
    task = service.tasks().get(tasklist=list_id, task=google_id).execute()
    task["status"] = "completed"
    service.tasks().update(tasklist=list_id, task=google_id, body=task).execute()
    print(f"[tasks] marked complete: {task.get('title', google_id)!r}")


def create(config: Config, title: str, notes: str, due_str: str) -> str:
    """Create one task in the Uni Assignments list. Returns the new google_id."""
    service = _build_service(config)
    list_id = _get_or_create_list(service, config.tasks_list_name)
    body = {"title": title, "notes": notes, "due": due_str}
    result = service.tasks().insert(tasklist=list_id, body=body).execute()
    print(f"[tasks] created: {title!r}")
    return result["id"]

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

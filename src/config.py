"""Reads env vars exactly once. Other modules accept Config as a parameter."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    tau_username: str
    tau_id: str
    tau_password: str
    google_credentials_path: str
    google_token_path: str
    moodle_session_file: str = "session.json"
    days_ahead: int = 30
    tasks_list_name: str = "Uni Assignments"
    title_format: str = "{course_name}: {title}"


def load() -> Config:
    load_dotenv()
    return Config(
        tau_username=os.environ["TAU_USERNAME"],
        tau_id=os.environ["TAU_ID"],
        tau_password=os.environ["TAU_PASSWORD"],
        google_credentials_path=os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
        google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "token.json"),
    )

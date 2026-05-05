"""Optional notifications. Each channel is opt-in via env vars; absent => skip."""

import os

import requests

from src.config import Config


def notify_all(config: Config, created_titles: list[str], completed_titles: list[str]) -> None:
    """Send notifications via every configured channel. Silent if nothing changed."""
    raise NotImplementedError


def _format_message(created_titles: list[str], completed_titles: list[str]) -> str:
    parts = ["Moodle Tasks Sync:"]
    if created_titles:
        parts.append("")
        parts.append(f"new assignments({len(created_titles)}):")
        parts.extend(created_titles)
    if completed_titles:
        parts.append("")
        parts.append(f"completed assignments({len(completed_titles)}):")
        parts.extend(completed_titles)
    return "\n".join(parts)

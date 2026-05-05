"""Optional notifications. Each channel is opt-in via env vars; absent => skip."""

import os
from typing import Callable

import requests

from src.config import Config


def notify_all(config: Config, created_titles: list[str], completed_titles: list[str]) -> None:
    """Send notifications via every configured channel. Silent if nothing changed."""
    if not created_titles and not completed_titles:
        return
    message = _format_message(created_titles, completed_titles)
    _try("github_issue", lambda: _notify_github_issue(config, message))
    _try("ntfy", lambda: _notify_ntfy(config, message))
    _try("telegram", lambda: _notify_telegram(config, message))
    _try("discord", lambda: _notify_discord(config, message))


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


def _try(channel_name: str, fn: Callable[[], None]) -> None:
    """Run a channel's notify function. Log and swallow exceptions so one failure
    doesn't prevent other channels from firing."""
    try:
        fn()
    except Exception as e:
        print(f"[notifier] {channel_name} failed: {e}")


def _notify_github_issue(config: Config, message: str) -> None:
    """Open an issue with the message, then close it immediately. Notification
    happens via GitHub's default repo-watcher email on issue creation.

    Reads GITHUB_TOKEN and GITHUB_REPOSITORY directly from os.environ — both are
    auto-provided by GitHub Actions, and locally they're set by the user only if
    they want this channel.
    """
    if not config.notify_github_issues:
        return
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("[notifier] github_issue: NOTIFY_GITHUB_ISSUES=true but GITHUB_TOKEN or GITHUB_REPOSITORY missing; skipping")
        return
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    title = message.split("\n")[0]
    create_resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers=headers,
        json={"title": title, "body": message},
        timeout=10,
    )
    create_resp.raise_for_status()
    issue_number = create_resp.json()["number"]
    requests.patch(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        headers=headers,
        json={"state": "closed"},
        timeout=10,
    ).raise_for_status()
    print(f"[notifier] github_issue: opened+closed #{issue_number}")


def _notify_ntfy(config: Config, message: str) -> None:
    if not config.ntfy_topic:
        return
    # Phones strip leading whitespace from notification bodies, so we use ntfy's
    # Title header for the headline (renders as a bold row above the body)
    headline, _, body = message.partition("\n")
    requests.post(
        f"https://ntfy.sh/{config.ntfy_topic}",
        data=body.lstrip("\n").encode("utf-8"),
        headers={"Title": headline.rstrip(":")},
        timeout=10,
    ).raise_for_status()
    print(f"[notifier] ntfy: posted to topic")


def _notify_telegram(config: Config, message: str) -> None:
    if not (config.telegram_bot_token and config.telegram_chat_id):
        return
    requests.post(
        f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage",
        json={"chat_id": config.telegram_chat_id, "text": message},
        timeout=10,
    ).raise_for_status()
    print(f"[notifier] telegram: sent to chat")


def _notify_discord(config: Config, message: str) -> None:
    if not config.discord_webhook_url:
        return
    requests.post(
        config.discord_webhook_url,
        json={"content": message},
        timeout=10,
    ).raise_for_status()
    print(f"[notifier] discord: posted to webhook")

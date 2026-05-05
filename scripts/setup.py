"""scripts/setup.py — friend bootstrap, run once after fork.

Runs the Google OAuth flow, prompts for TAU credentials, and prints all 5
GitHub Secrets ready to paste into the repo's Settings → Secrets → Actions UI.
"""

import base64
import getpass
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/tasks"]
ROOT = Path(__file__).resolve().parent.parent
CREDS_PATH = ROOT / "credentials.json"
TOKEN_PATH = ROOT / "token.json"


def main() -> None:
    _banner()
    _check_project_root()
    _check_credentials_file()
    _run_oauth_flow()
    tau_username, tau_id, tau_password = _prompt_tau_credentials()
    secrets = _build_secret_payloads(tau_username, tau_id, tau_password)
    _print_paste_block(secrets)


def _banner() -> None:
    print("=" * 68)
    print("  Moodle Tasks Sync — local setup")
    print("=" * 68)
    print()


def _check_project_root() -> None:
    raise NotImplementedError


def _check_credentials_file() -> None:
    raise NotImplementedError


def _run_oauth_flow() -> None:
    raise NotImplementedError


def _prompt_tau_credentials() -> tuple[str, str, str]:
    raise NotImplementedError


def _build_secret_payloads(username: str, id_: str, password: str) -> dict[str, str]:
    raise NotImplementedError


def _print_paste_block(secrets: dict[str, str]) -> None:
    raise NotImplementedError


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("Usage: python scripts/setup.py")
        print("  No arguments. Run from the project root after placing credentials.json.")
        sys.exit(0)
    main()

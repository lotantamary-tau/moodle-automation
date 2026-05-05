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
    main_py = ROOT / "src" / "main.py"
    if not main_py.exists():
        print("ERROR: src/main.py not found.")
        print("Run this from the moodle-automation/ directory:")
        print("  python scripts/setup.py")
        sys.exit(1)


def _check_credentials_file() -> None:
    if not CREDS_PATH.exists():
        print("ERROR: credentials.json not found in the project root.")
        print("Place your downloaded credentials.json there, then re-run.")
        print(f"Expected path: {CREDS_PATH}")
        sys.exit(1)


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

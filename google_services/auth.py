import os
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_credentials():
    """
    Get Google OAuth credentials.

    Local development:
        Uses credentials/credentials.json
        and creates credentials/token.json after login.

    Later on Render:
        We can move the token to an environment variable.
    """

    project_root = Path(__file__).resolve().parent.parent

    credentials_path = (
        project_root / "credentials" / "credentials.json"
    )

    token_path = (
        project_root / "credentials" / "token.json"
    )

    creds = None

    # --------------------------------------------------------
    # 1. Load existing token
    # --------------------------------------------------------

    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(
                str(token_path),
                SCOPES
            )
        except Exception as e:
            print(f"⚠️ Could not load existing token: {e}")
            creds = None

    # --------------------------------------------------------
    # 2. Refresh expired token
    # --------------------------------------------------------

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())

            with open(token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())

            print("✅ Google OAuth token refreshed.")

        except Exception as e:
            print(f"⚠️ Could not refresh Google token: {e}")
            creds = None

    # --------------------------------------------------------
    # 3. First-time login
    # --------------------------------------------------------

    if not creds or not creds.valid:

        if not credentials_path.exists():
            raise RuntimeError(
                "OAuth credentials.json not found at: "
                f"{credentials_path}"
            )

        print("🔐 Google authorization required.")
        print("🌐 Your browser will open for Google login.")

        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path),
            SCOPES
        )

        creds = flow.run_local_server(port=0)

        # Save token for future runs
        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

        print("✅ Google OAuth authorization successful.")
        print(f"💾 Token saved to: {token_path}")

    return creds
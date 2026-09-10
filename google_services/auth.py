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

    LOCAL:
        Uses:
            credentials/credentials.json
            credentials/token.json

    RENDER:
        Uses:
            GOOGLE_TOKEN_JSON
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
    # 1. CHECK GOOGLE_TOKEN_JSON
    # --------------------------------------------------------

    google_token_json = os.getenv("GOOGLE_TOKEN_JSON")

    if google_token_json:
        try:
            token_data = json.loads(google_token_json)

            creds = Credentials.from_authorized_user_info(
                token_data,
                SCOPES
            )

            print(
                "Google OAuth token loaded from environment."
            )

        except Exception as e:
            print(
                f"Could not load GOOGLE_TOKEN_JSON: {e}"
            )

            creds = None

    # --------------------------------------------------------
    # 2. LOAD LOCAL token.json
    # --------------------------------------------------------

    if creds is None and token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(
                str(token_path),
                SCOPES
            )

            print(
                "Google OAuth token loaded from token.json."
            )

        except Exception as e:
            print(
                f"Could not load existing token: {e}"
            )

            creds = None

    # --------------------------------------------------------
    # 3. REFRESH EXPIRED TOKEN
    # --------------------------------------------------------

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())

            print(
                "Google OAuth token refreshed."
            )

            # Only save the refreshed token locally.
            if not google_token_json:
                with open(
                    token_path,
                    "w",
                    encoding="utf-8"
                ) as token_file:
                    token_file.write(
                        creds.to_json()
                    )

        except Exception as e:
            print(
                f"Could not refresh Google OAuth token: {e}"
            )

            creds = None

    # --------------------------------------------------------
    # 4. IF TOKEN IS VALID, RETURN IT
    # --------------------------------------------------------

    if creds and creds.valid:
        return creds

    # --------------------------------------------------------
    # 5. LOCAL FIRST-TIME LOGIN
    # --------------------------------------------------------

    if not google_token_json:

        if not credentials_path.exists():
            raise RuntimeError(
                "OAuth credentials.json not found at: "
                f"{credentials_path}"
            )

        print(
            "Google authorization required."
        )

        print(
            "Your browser will open for Google login."
        )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path),
            SCOPES
        )

        creds = flow.run_local_server(
            port=0
        )

        # Save token for future local runs.
        with open(
            token_path,
            "w",
            encoding="utf-8"
        ) as token_file:
            token_file.write(
                creds.to_json()
            )

        print(
            "Google OAuth authorization successful."
        )

        print(
            f"Token saved to: {token_path}"
        )

        return creds

    # --------------------------------------------------------
    # 6. RENDER TOKEN IS INVALID
    # --------------------------------------------------------

    raise RuntimeError(
        "Google OAuth credentials are invalid or expired. "
        "Please generate a new token.json locally and update "
        "GOOGLE_TOKEN_JSON on Render."
    )
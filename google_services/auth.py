import os
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ============================================================
# CACHE GOOGLE CREDENTIALS
# ============================================================

_credentials_cache = None


# ============================================================
# GET GOOGLE CREDENTIALS
# ============================================================

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

    Credentials are cached in memory so token.json
    is not loaded repeatedly during the same server run.
    """

    global _credentials_cache


    # ========================================================
    # 1. RETURN CACHED CREDENTIALS
    # ========================================================

    if _credentials_cache is not None:

        # If cached credentials are still valid,
        # return them immediately.

        if _credentials_cache.valid:
            return _credentials_cache


    # ========================================================
    # PROJECT PATHS
    # ========================================================

    project_root = Path(__file__).resolve().parent.parent

    credentials_path = (
        project_root
        / "credentials"
        / "credentials.json"
    )

    token_path = (
        project_root
        / "credentials"
        / "token.json"
    )


    creds = None


    # ========================================================
    # 2. CHECK GOOGLE_TOKEN_JSON
    # ========================================================

    google_token_json = os.getenv(
        "GOOGLE_TOKEN_JSON"
    )


    if google_token_json:

        try:

            token_data = json.loads(
                google_token_json
            )

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


    # ========================================================
    # 3. LOAD LOCAL token.json
    # ========================================================

    if (
        creds is None
        and token_path.exists()
    ):

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


    # ========================================================
    # 4. REFRESH EXPIRED TOKEN
    # ========================================================

    if (
        creds
        and creds.expired
        and creds.refresh_token
    ):

        try:

            creds.refresh(
                Request()
            )

            print(
                "Google OAuth token refreshed."
            )


            # ------------------------------------------------
            # SAVE REFRESHED TOKEN LOCALLY
            # ------------------------------------------------

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


    # ========================================================
    # 5. IF TOKEN IS VALID
    # ========================================================

    if (
        creds
        and creds.valid
    ):

        _credentials_cache = creds

        return creds


    # ========================================================
    # 6. LOCAL FIRST-TIME LOGIN
    # ========================================================

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


        # ----------------------------------------------------
        # SAVE TOKEN
        # ----------------------------------------------------

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


        _credentials_cache = creds

        return creds


    # ========================================================
    # 7. RENDER TOKEN INVALID
    # ========================================================

    raise RuntimeError(
        "Google OAuth credentials are invalid or expired. "
        "Please generate a new token.json locally and update "
        "GOOGLE_TOKEN_JSON on Render."
    )